from __future__ import annotations

from pathlib import Path

from .constants import SECTION_NAMES
from .model import ProjectInfo, RenderPlan
from .render import load_template, render_template


def build_render_plan(info: ProjectInfo) -> RenderPlan:
    warnings_md = "\n".join([f"- {w}" for w in (info.warnings or [])]) or "- (none)"

    overview = "\n".join(
        [
            f"- **Project:** {info.project_name}",
            f"- **Stack:** {info.stack}" + (
                f" ({info.package_manager})" if info.package_manager else (
                    f" ({info.python_tooling})" if info.python_tooling else ""
                )
            ),
            "- Keep changes small and verifiable.",
        ]
    )

    rules = "\n".join(
        [
            "**DO**",
            "- Prefer small diffs.",
            "- Add or update tests when behavior changes.",
            "- Run repo checks before finishing.",
            "",
            "**DON'T**",
            "- Do not rewrite unrelated code.",
            "- Do not refactor without confirming intent.",
            "- Do not commit secrets or local env files.",
            "",
            "**If uncertain**",
            "- Ask a short clarifying question before making big changes.",
            "",
            "**Warnings**",
            warnings_md,
        ]
    )

    def cmd_line(label: str, key: str) -> str | None:
        v = (info.commands.get(key, "") or "").strip()
        if not v:
            return None
        return f"- **{label}:** `{v}`"

    commands_lines = [
        cmd_line("Install", "install"),
        cmd_line("Dev", "dev"),
        cmd_line("Test", "test"),
        cmd_line("Lint", "lint"),
        cmd_line("Format", "format"),
        cmd_line("Build", "build"),
    ]
    commands = "\n".join([x for x in commands_lines if x]) or "- (no commands configured)"

    structure_parts: list[str] = []
    if info.source_dirs:
        structure_parts.append("- **Source:** " + ", ".join([f"`{p}`" for p in info.source_dirs]))
    if info.config_locations:
        structure_parts.append(
            "- **Config:** " + ", ".join([f"`{p}`" for p in info.config_locations])
        )
    if info.branching_model:
        structure_parts.append(f"- **Branching:** {info.branching_model}")
    structure = "\n".join(structure_parts) or "- (not specified)"

    output_protocol = "\n".join(
        [
            "When you finish work, include:",
            "- Summary (1-3 bullets)",
            "- Files changed (list paths)",
            "- Verification (exact commands to run)",
        ]
    )

    guardrails = "\n".join(
        [
            "## Guardrails (read this first)",
            "",
            "You are an autonomous coding agent. Your job is to produce *useful*, *reviewable*, and *safe* changes.",
            "",
            "### Non-negotiables",
            "- Prefer small, incremental changes over big rewrites.",
            "- Don't change behavior unless the task explicitly requires it.",
            "- Don't introduce new dependencies unless you can justify them and keep them minimal.",
            "- Never touch secrets, tokens, or credentials. If something looks like a secret: stop and ask.",
            "- If you are unsure: propose two options and pick the safer one.",
            "",
            "### Safe edits policy",
            "- Default to additive changes: new files or small localized edits.",
            "- Avoid wide refactors (renames, mass formatting, code motion) unless requested.",
            "- If you must refactor: do it in a separate step from functional changes.",
            "- Keep diffs boring: make them easy to review.",
            "",
            "### Tests are the gate",
            "- If tests exist: run them (or provide exact commands to run).",
            "- If tests fail: fix or explain why and propose the minimal fix.",
            "- If there are no tests: add a small smoke test or a reproducible manual check.",
            "",
            "### Output expectations",
            "- Produce an explicit summary:",
            "  1) What changed",
            "  2) Why",
            "  3) How to verify (commands)",
            "  4) Risk notes (what could break)",
            "",
            "### When to stop and ask",
            "Ask before doing any of the following:",
            "- Changing public APIs, schema, or data formats",
            "- Deleting files or large blocks of code",
            "- Introducing new build tooling, CI, or major dependencies",
            "- Touching auth, payments, encryption, or compliance-related code",
        ]
    )

    workflow = "\n".join(
        [
            "## Workflow & PR discipline",
            "",
            "### Work in thin slices",
            "Aim for a sequence that can be reviewed quickly:",
            "1) scaffold / wiring",
            "2) core logic",
            "3) tests",
            "4) docs",
            "",
            "### Commit hygiene (even if you don't commit)",
            "Structure your work as if it were clean commits:",
            "- feat: functional change",
            "- test: tests only",
            "- docs: docs only",
            "- refactor: no behavior change",
            "",
            "### Reviewability checklist",
            "Before you say done, confirm:",
            "- Diff is small enough to review",
            "- Naming is consistent with the repo",
            "- No dead code or TODOs without context",
            "- Verification steps are included",
            "- Edge cases are not ignored silently",
        ]
    )

    verification = "\n".join(
        [
            "## Verification (how to check my work)",
            "",
            "When you change code, always provide:",
            "- One fast check (<=30s)",
            "- One full check (tests/lint)",
            "",
            "Example format:",
            "- Fast: `<command>`",
            "- Full: `<command>`",
            "",
            "If you cannot run commands in this environment, still provide the exact commands for the user to run locally.",
        ]
    )

    style = "\n".join(
        [
            "## Coding conventions (agent instructions)",
            "",
            "- Match existing style and patterns in the repo.",
            "- Prefer clarity over cleverness.",
            "- Avoid magic abstractions until the second iteration.",
            "- Log/print only when it helps debugging; avoid noisy output.",
            "- Errors should be actionable: explain what failed and how to fix it.",
            "",
            "When adding a function/module:",
            "- Include a docstring (what/why, not just how)",
            "- Keep interfaces small and composable",
            "- Add at least one test (happy path + one edge case)",
        ]
    )

    python_notes = "\n".join(
        [
            "## Python project notes",
            "",
            "### Local setup",
            "- Create venv: `python -m venv .venv && source .venv/bin/activate`",
            "- Install: `pip install -e .`",
            "",
            "### Common commands",
            "- Tests: `pytest`",
            "- Lint: `ruff check .`",
            "- Format: `ruff format .`",
            "",
            "### Packaging expectations",
            "- Keep dependencies minimal",
            "- Prefer standard library where reasonable",
            "- Ensure CLI help output is clear and stable",
        ]
    )

    node_notes = "\n".join(
        [
            "## Node project notes",
            "",
            "### Common commands",
            "- Install: `npm ci` (or `pnpm i --frozen-lockfile`)",
            "- Tests: `npm test`",
            "- Lint: `npm run lint`",
            "- Build: `npm run build`",
            "",
            "### Guardrails",
            "- Don't update lockfiles unless necessary",
            "- Prefer minimal dependency changes",
        ]
    )

    static_notes = "\n".join(
        [
            "## Static site / docs notes",
            "",
            "### Safe edits",
            "- Avoid large HTML/CSS refactors unless requested",
            "- Prefer small layout changes with predictable impact",
            "- If mobile layout changes: verify at least one narrow breakpoint",
            "",
            "### Quick checks",
            "- Run formatter (if present)",
            "- Validate links (spot-check)",
        ]
    )

    repo_context = "\n".join(
        [
            "## Repo context (optional)",
            "",
            "- (add repo-specific notes here: invariants, no-touch areas, release process, etc.)",
        ]
    )

    return RenderPlan(
        sections={
            "overview": overview,
            "rules": rules,
            "commands": commands,
            "structure": structure,
            "output_protocol": output_protocol,
            "guardrails": guardrails,
            "workflow": workflow,
            "verification": verification,
            "style": style,
            "python": python_notes,
            "node": node_notes,
            "static": static_notes,
            "repo_context": repo_context,
        }
    )


def render_agents_md(info: ProjectInfo, template_path: Path, single_test_hint: str, configs_hint: str) -> str:
    plan = build_render_plan(info)

    ctx: dict[str, str] = {
        "project_name": info.project_name,
        "stack": info.stack,
        "package_manager": info.package_manager,
        "python_tooling": info.python_tooling,
        "overview_block": plan.sections["overview"],
        "rules_block": plan.sections["rules"],
        "commands_block": plan.sections["commands"],
        "structure_block": plan.sections["structure"],
        "output_protocol_block": plan.sections["output_protocol"],
        "single_test_hint": single_test_hint,
        "configs_hint": configs_hint,
        "guardrails_block": plan.sections["guardrails"],
        "workflow_block": plan.sections["workflow"],
        "verification_block": plan.sections["verification"],
        "style_block": plan.sections["style"],
        "python_block": plan.sections["python"],
        "node_block": plan.sections["node"],
        "static_block": plan.sections["static"],
        "repo_context_block": plan.sections["repo_context"],
    }

    return render_template(load_template(template_path), ctx)


def render_runbook_md(info: ProjectInfo, template_path: Path) -> str:
    c = info.commands
    quick_cmds = [x.strip() for x in [c.get("install", ""), c.get("dev", ""), c.get("test", ""), c.get("lint", "")] if x and x.strip()]

    if quick_cmds:
        quickstart = "\n".join([f"```sh\n{cmd}\n```" for cmd in quick_cmds[:6]])
    else:
        quickstart = "- (no quickstart commands configured)"

    common_tasks = "\n".join(
        [
            "- Run tests: " + (f"`{c.get('test','').strip()}`" if c.get("test", "").strip() else "(not set)"),
            "- Lint: " + (f"`{c.get('lint','').strip()}`" if c.get("lint", "").strip() else "(not set)"),
            "- Build: " + (f"`{c.get('build','').strip()}`" if c.get("build", "").strip() else "(not set)"),
        ]
    )

    troubleshooting = "\n".join(
        [
            "- If dependencies fail: verify the expected Node/Python version for this repo.",
            "- If tests are flaky: re-run once, then isolate and fix the root cause.",
            "- If environment is unclear: ask for the expected OS/tooling versions.",
        ]
    )

    ctx: dict[str, str] = {
        "project_name": info.project_name,
        "stack": info.stack,
        "quickstart_block": quickstart,
        "common_tasks_block": common_tasks,
        "troubleshooting_block": troubleshooting,
    }

    return render_template(load_template(template_path), ctx)


def template_paths(base: Path, stack: str) -> tuple[Path, Path]:
    agents_tpl = base / stack / "AGENTS.md.tpl"
    runbook_tpl = base / stack / "RUNBOOK.md.tpl"
    return agents_tpl, runbook_tpl


def required_sections(stack: str) -> list[str]:
    stack = (stack or "").strip().lower()
    base = [
        "overview",
        "rules",
        "commands",
        "structure",
        "output_protocol",
        "guardrails",
        "workflow",
        "verification",
        "style",
    ]
    if stack in ("python", "node", "static"):
        return base + [stack]
    return base


def required_runbook_sections() -> list[str]:
    return ["quickstart", "common_tasks", "troubleshooting"]
