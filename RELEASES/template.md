# vX.Y.Z - <one-line value>

## What's inside
- <1-3 bullets: user-visible changes>
- <optional: internal refactor / tests / docs>

## Safety model (why it won't wreck your repo)
- Marker-only updates: if `AGENTS.md` / `RUNBOOK.md` have `<!-- AGENTSGEN:START ... -->`, agentsgen updates only inside marker blocks.
- No markers = no touch: if markers are missing, agentsgen writes `AGENTS.generated.md` / `RUNBOOK.generated.md`.
- Preview-first: supports `--dry-run` and `--print-diff`.

## GitHub PR Guard (if applicable)
- `agentsgen-guard` fails PRs when generated sections drift or files are missing.
- Optional sticky PR comment with remediation commands (best-effort, fork-safe).

## Quickstart

```bash
pipx install git+https://github.com/markoblogo/AGENTS.md_generator@vX.Y.Z

agentsgen init --autodetect
agentsgen update
agentsgen check .
```

## Known limitations
- <1-3 honest constraints>
- <optional: note about release tooling/environment limits>

## Notes
- Docs: <README updated / link>
- Tag: vX.Y.Z

