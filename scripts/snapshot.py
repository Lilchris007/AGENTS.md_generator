from __future__ import annotations

import os
import subprocess
import sys


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def must(cmd: list[str]) -> None:
    p = subprocess.run(cmd)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main() -> None:
    # 1) No-op on clean tree.
    st = run(["git", "status", "--porcelain"])
    if st.returncode != 0:
        print(st.stderr, file=sys.stderr)
        raise SystemExit(st.returncode)
    if not st.stdout.strip():
        print("snapshot: no changes")
        return

    # 2) Gate on green checks.
    must(["ruff", "format", "."])
    must(["ruff", "check", "."])
    must(["pytest", "-q"])

    # 3) Commit with deterministic message.
    msg = os.environ.get("SNAPSHOT_MSG", "").strip()
    if not msg:
        # Use a short stat hint; keep message stable.
        stat = run(["git", "diff", "--stat"]).stdout.strip().splitlines()
        hint = stat[0] if stat else "WIP"
        msg = f"snapshot: {hint}"

    must(["git", "add", "-A"])
    must(["git", "commit", "-m", msg])
    print(f"snapshot: committed ({msg})")


if __name__ == "__main__":
    main()
