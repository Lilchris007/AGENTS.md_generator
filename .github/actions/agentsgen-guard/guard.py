from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agentsgen.actions import check_repo


COMMENT_MARKER = "<!-- agentsgen-guard -->"


def _set_output(name: str, value: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def _to_bool(value: str, default: bool = False) -> bool:
    v = (value or "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default


def _split_files(raw: str) -> list[str]:
    # Accept comma-separated and/or newline-separated lists.
    parts = [p.strip() for p in re.split(r"[\n,]+", raw or "") if p.strip()]
    # Keep order but dedupe.
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _pack_drift_info_from_json(output: str, limit: int = 5) -> tuple[int, list[str]]:
    try:
        payload = json.loads(output)
    except Exception:
        return 0, []
    if not isinstance(payload, dict):
        return 0, []
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        return 0, []
    changed: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        action = str(row.get("action", "")).strip().lower()
        path = str(row.get("path", "")).strip()
        if path and action in {"created", "updated", "generated"}:
            changed.append(path)
    return len(changed), changed[:limit]


def _load_event(path: str) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _api_request(
    method: str, url: str, token: str, payload: dict[str, Any] | None = None
) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urlopen(req, timeout=12) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def _find_sticky_comment_id(token: str, repo: str, issue_number: int) -> int | None:
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments?per_page=100"
    comments = _api_request("GET", url, token)
    if not isinstance(comments, list):
        return None
    for c in comments:
        body = c.get("body", "")
        if isinstance(body, str) and COMMENT_MARKER in body:
            cid = c.get("id")
            if isinstance(cid, int):
                return cid
    return None


def _upsert_comment(token: str, repo: str, issue_number: int, body: str) -> None:
    existing_id = _find_sticky_comment_id(token, repo, issue_number)
    if existing_id is not None:
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_id}"
        _api_request("PATCH", url, token, payload={"body": body})
        return
    create_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    _api_request("POST", create_url, token, payload={"body": body})


def _targeted_messages(
    problems: list[str], warnings: list[str], files: list[str]
) -> tuple[list[str], list[str]]:
    wanted = {f.strip().upper() for f in files if f.strip()}
    if not wanted:
        return problems, warnings

    prefixes = tuple(f"{f}:" for f in wanted)
    missing_names = tuple(f"Missing {f}" for f in wanted)
    no_marker_names = tuple(f"{f} has no AGENTSGEN markers" for f in wanted)

    def keep_problem(msg: str) -> bool:
        m = msg.strip()
        # Repo-level checks should always fail regardless of selected files.
        if m.startswith("Missing .agentsgen.json"):
            return True
        return (
            m.startswith(prefixes)
            or m.startswith(missing_names)
            or m.startswith(no_marker_names)
        )

    def keep_warning(msg: str) -> bool:
        m = msg.strip()
        return m.startswith(prefixes)

    return [p for p in problems if keep_problem(p)], [
        w for w in warnings if keep_warning(w)
    ]


def _quote(value: str) -> str:
    return shlex.quote(value)


def _build_fix_lines(
    path: str,
    files_arg: str,
    show_commands: bool,
    problems: list[str],
    *,
    pack_failed: bool,
) -> list[str]:
    if not show_commands:
        return []
    path_q = _quote(path)
    has_missing = any(p.startswith("Missing ") for p in problems)
    lines = [
        "",
        "**How to fix (run locally):**",
        (
            f"- `agentsgen init {path_q}` (required: missing files/config detected)"
            if has_missing
            else f"- `agentsgen init {path_q}` (only if files are missing)"
        ),
        f"- `agentsgen update {path_q}` (apply generator updates for marker-managed sections)",
        f"- ensure `{files_arg}` exist and contain AGENTSGEN markers",
        f"- `agentsgen check {path_q}`",
    ]
    if pack_failed:
        lines.append(
            f"- `agentsgen pack {path_q} --autodetect` (refresh LLMO pack files)"
        )
        lines.append(f"- `agentsgen pack {path_q} --autodetect --check`")
    lines.append("- commit changes and push")
    return lines


def _run_pack_check(
    path: str,
    pack_format: str,
    *,
    pack_autodetect: bool,
    pack_llms_format: str,
    pack_output_dir: str,
    pack_files: list[str],
) -> tuple[int, str, list[str], int]:
    fmt = (pack_format or "json").strip().lower()
    if fmt not in {"json", "text"}:
        fmt = "json"
    cmd = ["agentsgen", "pack", path, "--check", "--format", fmt]
    if pack_autodetect:
        cmd.append("--autodetect")
    else:
        cmd.append("--no-autodetect")
    llms_fmt = (pack_llms_format or "").strip()
    if llms_fmt:
        cmd.extend(["--llms-format", llms_fmt])
    out_dir = (pack_output_dir or "").strip()
    if out_dir:
        cmd.extend(["--output-dir", out_dir])
    if pack_files:
        cmd.extend(["--files", ",".join(pack_files)])
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 2, "agentsgen command not found while running pack check", [], 0
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    drift_count, top_paths = (
        _pack_drift_info_from_json(p.stdout or "", limit=5)
        if fmt == "json"
        else (0, [])
    )
    return p.returncode, out.strip(), top_paths, drift_count


def main() -> int:
    path = (os.getenv("INPUT_PATH") or ".").strip() or "."
    files_raw = os.getenv("INPUT_FILES", "AGENTS.md,RUNBOOK.md")
    files = _split_files(files_raw)
    files_arg = ",".join(files) if files else "AGENTS.md,RUNBOOK.md"
    comment = _to_bool(os.getenv("INPUT_COMMENT", "false"))
    token = os.getenv("INPUT_TOKEN", "")
    show_commands = _to_bool(os.getenv("INPUT_SHOW_COMMANDS", "true"), default=True)
    pack_enabled = _to_bool(
        os.getenv("INPUT_PACK", "false"), default=False
    ) or _to_bool(os.getenv("INPUT_PACK_CHECK", "false"), default=False)
    pack_format = os.getenv("INPUT_PACK_FORMAT", "json")
    pack_autodetect = _to_bool(os.getenv("INPUT_PACK_AUTODETECT", "true"), default=True)
    pack_llms_format = os.getenv("INPUT_PACK_LLMS_FORMAT", "")
    pack_output_dir = os.getenv("INPUT_PACK_OUTPUT_DIR", "")
    pack_files = _split_files(os.getenv("INPUT_PACK_FILES", ""))

    target = Path(path)
    code, problems, warnings = check_repo(target)
    problems, warnings = _targeted_messages(problems, warnings, files)
    pack_failed = False
    pack_output = ""
    pack_top_paths: list[str] = []
    pack_drift_count = 0

    if pack_enabled:
        pack_code, pack_output, pack_top_paths, pack_drift_count = _run_pack_check(
            path,
            pack_format,
            pack_autodetect=pack_autodetect,
            pack_llms_format=pack_llms_format,
            pack_output_dir=pack_output_dir,
            pack_files=pack_files,
        )
        if pack_code != 0:
            pack_failed = True

    if warnings:
        for w in warnings:
            print(f"[agentsgen-guard] WARN: {w}", file=sys.stderr)

    if pack_enabled:
        pack_status = "DRIFT" if pack_failed else "OK"
        print(
            f"[agentsgen-guard] pack_check={pack_status} drift_count={pack_drift_count}",
            file=sys.stderr,
        )
        if pack_top_paths:
            print(
                f"[agentsgen-guard] pack top files: {', '.join(pack_top_paths)}",
                file=sys.stderr,
            )

    if code == 0 and not problems and not pack_failed:
        summary = "agentsgen-guard: OK (AGENTS docs look up to date)."
        print(summary)
        _set_output("status", "ok")
        _set_output("summary", summary)
        return 0

    if pack_failed and not problems:
        summary = "agentsgen-guard: FAIL (LLMO pack is missing/out of date)."
    elif pack_failed and problems:
        summary = "agentsgen-guard: FAIL (AGENTS docs and LLMO pack are out of date)."
    else:
        summary = "agentsgen-guard: FAIL (AGENTS docs missing or out of date)."
    print(summary, file=sys.stderr)
    if problems:
        print("", file=sys.stderr)
        print("--- agentsgen check findings ---", file=sys.stderr)
        for p in problems:
            print(f"- {p}", file=sys.stderr)
    if pack_failed:
        print("", file=sys.stderr)
        print("--- pack check findings ---", file=sys.stderr)
        if pack_output:
            print(pack_output, file=sys.stderr)
        else:
            print("- `agentsgen pack --autodetect --check` failed", file=sys.stderr)

    fix_lines = _build_fix_lines(
        path, files_arg, show_commands, problems, pack_failed=pack_failed
    )
    for ln in fix_lines:
        print(ln, file=sys.stderr)

    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    event = _load_event(event_path)
    is_pr = event_name == "pull_request" and isinstance(event.get("pull_request"), dict)

    if comment and is_pr and token and repo:
        try:
            pr = event["pull_request"]
            issue_number = pr.get("number")
            if isinstance(issue_number, int):
                comment_body = "\n".join(
                    [
                        COMMENT_MARKER,
                        "### agentsgen-guard",
                        "This PR fails the AGENTS docs guard."
                        if not pack_failed
                        else "This PR fails the AGENTS/LLMO docs guard.",
                        "",
                        "Required generated docs are missing/outdated for this repository.",
                        "",
                        "## 📦 LLMO Pack check",
                        (
                            "Status: DRIFT"
                            if pack_failed
                            else ("Status: OK" if pack_enabled else "Status: SKIPPED")
                        ),
                        (
                            f"Summary: drift detected in pack outputs ({pack_drift_count} files)"
                            if pack_failed
                            else (
                                "Summary: pack check passed"
                                if pack_enabled
                                else "Summary: pack check disabled"
                            )
                        ),
                        (
                            "Top files: " + ", ".join(pack_top_paths)
                            if pack_top_paths
                            else "Top files: (not available)"
                        ),
                        "Fix:",
                        "- Run: `agentsgen pack --autodetect`",
                        "- Or: `agentsgen pack` (if your repo has explicit pack config)",
                        *fix_lines,
                    ]
                ).strip()
                _upsert_comment(
                    token=token, repo=repo, issue_number=issue_number, body=comment_body
                )
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            print(
                f"[agentsgen-guard] WARN: could not post PR comment: {e}",
                file=sys.stderr,
            )
        except Exception as e:  # pragma: no cover - safety net
            print(
                f"[agentsgen-guard] WARN: unexpected comment failure: {e}",
                file=sys.stderr,
            )

    _set_output("status", "fail")
    _set_output("summary", summary)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
