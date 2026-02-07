from __future__ import annotations

from pathlib import Path

from .github import detect_github_actions
from .makefile import parse_makefile_targets
from .model import DetectResult
from .node import commands_from_node, detect_node
from .python import commands_from_python, detect_python


COMMON_SOURCE_DIRS = [
    "src",
    "app",
    "apps",
    "services",
    "packages",
    "frontend",
    "backend",
    "client",
    "server",
    "web",
    "api",
    "worker",
    "workers",
    "cmd",
    "internal",
]


COMMON_CONFIG_FILES = [
    "Makefile",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "pytest.ini",
    "ruff.toml",
    "mypy.ini",
    "docker-compose.yml",
    "docker-compose.yaml",
]


def _detect_stack(py: bool, node: bool) -> str:
    if py and node:
        return "mixed"
    if py:
        return "python"
    if node:
        return "node"
    return "static"


def detect_repo(repo: Path) -> DetectResult:
    repo = repo.resolve()
    res = DetectResult()

    # Docs
    docs: list[str] = []
    for f in ["README.md", "RUNBOOK.md", "CONTRIBUTING.md"]:
        if (repo / f).is_file():
            docs.append(f)
    res.paths["docs"] = docs or ["README.md"]
    res.paths["ci"] = ".github/workflows/" if (repo / ".github" / "workflows").is_dir() else ""
    for dname, key in [("scripts", "scripts"), ("plans", "plans"), ("drafts", "drafts")]:
        if (repo / dname).is_dir():
            res.paths[key] = f"{dname}/"

    # Structure hints: top-level source dirs + config files. (Cheap signals only.)
    source_dirs: list[str] = []
    for d in COMMON_SOURCE_DIRS:
        if (repo / d).is_dir():
            source_dirs.append(d)
    config_locations: list[str] = []
    for f in COMMON_CONFIG_FILES:
        if (repo / f).is_file():
            config_locations.append(f)
    if (repo / ".github" / "workflows").is_dir():
        config_locations.append(".github/workflows/")

    # CI evidence
    ci = detect_github_actions(repo)
    if ci:
        res.paths["ci"] = ci.ci_dir
        res.evidence.ci.extend(ci.workflows or [ci.ci_dir])

    make = parse_makefile_targets(repo)
    if make:
        res.evidence.make.append(make.path)
        res.evidence.make.extend([f"target:{t}" for t in make.targets])
        res.rationale.append(f"Using Makefile targets because {make.path} exists.")

    py = detect_python(repo)
    if py:
        res.evidence.python.extend(py.evidence)
        if py.toolchain != "vanilla":
            res.rationale.append(f"Detected python toolchain '{py.toolchain}' based on lockfile/tool config.")

    node = detect_node(repo)
    if node:
        res.evidence.node.extend(node.evidence)
        res.rationale.append(f"Detected node package manager '{node.package_manager}' based on lockfile(s).")

        # If we detected node only via nested package.json (monorepo-ish), use those dirs as source hints.
        for ev in node.evidence:
            if ev.endswith("package.json") and "/" in ev:
                d = ev.split("/", 1)[0]
                if (repo / d).is_dir() and d not in source_dirs:
                    source_dirs.append(d)

    # Monorepo hint: if root has no sentinel, look a bit deeper (cheap scan).
    if py is None and node is None:
        # Depth-limited-ish scan: rglob can be expensive; keep it small by scanning known names.
        # This still stays read-only and bounded for typical repos.
        found_pkg = []
        found_py = []
        for p in sorted(repo.rglob("package.json")):
            try:
                rel = p.relative_to(repo)
            except Exception:
                continue
            if len(rel.parts) > 4:
                continue
            found_pkg.append(str(rel))
            if len(found_pkg) >= 5:
                break
        for p in sorted(repo.rglob("pyproject.toml")):
            try:
                rel = p.relative_to(repo)
            except Exception:
                continue
            if len(rel.parts) > 4:
                continue
            found_py.append(str(rel))
            if len(found_py) >= 5:
                break
        if found_pkg:
            res.evidence.node.extend(found_pkg)
        if found_py:
            res.evidence.python.extend(found_py)

        primary_stack = _detect_stack(bool(found_py), bool(found_pkg))
        if primary_stack == "mixed":
            res.rationale.append("Detected monorepo/mixed stack via nested package.json and pyproject.toml (no root sentinel).")
    else:
        primary_stack = _detect_stack(py is not None, node is not None)
    res.project["primary_stack"] = primary_stack
    res.project["name"] = repo.name
    res.project["repo_root"] = "."

    # Attach structure hints to paths so they flow into ProjectInfo (used by the structure section).
    if source_dirs:
        res.paths["source_dirs"] = sorted(set(source_dirs))
    if config_locations:
        # Keep stable order, but de-dup.
        seen: set[str] = set()
        out: list[str] = []
        for x in config_locations:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        res.paths["config_locations"] = out

    # Determine commands by priority:
    # 1) Makefile
    # 2) node scripts
    # 3) python toolchain
    # 4) empty
    cmds: dict[str, str] = {}
    if make:
        # Use standard targets if present.
        for k in ["dev", "test", "lint", "format", "build", "typecheck"]:
            if k in make.targets:
                cmds[k] = f"make {k}"
        # common alternates for dev
        if "dev" not in cmds:
            for alt in ["run", "start", "serve"]:
                if alt in make.targets:
                    cmds["dev"] = f"make {alt}"
                    break
        if cmds:
            res.rationale.append("Commands sourced from Makefile (highest priority).")
    if not cmds and node:
        cmds.update(commands_from_node(node))
        # Record package manager when detected.
        res.project["node_package_manager"] = node.package_manager
        if cmds:
            res.rationale.append("Commands sourced from package.json scripts.")
    if not cmds and py:
        cmds.update(commands_from_python(py))
        res.project["python_toolchain"] = py.toolchain
        if cmds:
            res.rationale.append("Commands sourced from python toolchain heuristics.")

    # Always preserve that we saw scripts/configs, even when Makefile dominates.
    if make and node:
        res.project["node_package_manager"] = node.package_manager
    if make and py:
        res.project["python_toolchain"] = py.toolchain

    # Only keep non-empty commands.
    res.commands = {k: v for k, v in cmds.items() if v and v.strip()}

    return res
