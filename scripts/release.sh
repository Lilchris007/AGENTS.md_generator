#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/release.sh v0.1.2 A
#   ./scripts/release.sh v0.1.2 B
#   ./scripts/release.sh v0.1.2 C

REPO="markoblogo/AGENTS.md_generator"
VERSION="${1:-}"
MODE="${2:-A}"
PYTHON_BIN=""

usage() {
  cat <<'EOF'
Usage:
  ./scripts/release.sh vX.Y.Z A|B|C

Examples:
  ./scripts/release.sh v0.1.2 A
  ./scripts/release.sh v0.2.0 B
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

ok() {
  echo "OK: $*"
}

warn() {
  echo "WARN: $*" >&2
}

confirm() {
  local prompt="${1}"
  local ans
  read -r -p "${prompt} [y/N] " ans
  case "${ans}" in
    y|Y) return 0 ;;
    *) die "Cancelled." ;;
  esac
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"
}

pick_python() {
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
    return
  fi
  die "Missing command: python (or python3)"
}

require_clean_git_tree() {
  git diff --quiet || die "Working tree has unstaged changes."
  git diff --cached --quiet || die "Index has staged changes."
  if [ -n "$(git ls-files --others --exclude-standard)" ]; then
    die "Working tree has untracked files."
  fi
}

require_no_existing_tag() {
  if git rev-parse -q --verify "refs/tags/${VERSION}" >/dev/null 2>&1; then
    die "Tag already exists locally: ${VERSION}"
  fi
  if git ls-remote --exit-code --tags origin "refs/tags/${VERSION}" >/dev/null 2>&1; then
    die "Tag already exists on origin: ${VERSION}"
  fi
}

run_checks() {
  echo "== Running checks =="
  "${PYTHON_BIN}" -m agentsgen._smoke
  if command -v pytest >/dev/null 2>&1; then
    pytest -q
  else
    warn "pytest not found; skipping pytest -q."
  fi
  ok "Checks completed."
}

gh_ready() {
  command -v gh >/dev/null 2>&1 || return 1
  gh auth status -h github.com >/dev/null 2>&1 || return 1
  return 0
}

main() {
  if [ "${VERSION}" = "-h" ] || [ "${VERSION}" = "--help" ] || [ -z "${VERSION}" ]; then
    usage
    exit 1
  fi
  case "${MODE}" in
    A|B|C) ;;
    *) usage; die "Mode must be A, B, or C." ;;
  esac

  require_cmd git
  pick_python

  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repository."

  local notes_file="RELEASES/${VERSION}.md"
  [ -f "${notes_file}" ] || die "Release notes file not found: ${notes_file}"

  echo "== Pre-flight =="
  echo "Version: ${VERSION}"
  echo "Mode: ${MODE}"
  echo "Notes: ${notes_file}"
  require_clean_git_tree
  ok "Git tree is clean."
  require_no_existing_tag
  ok "Tag is available locally and on origin."

  confirm "Run release checks now (smoke + pytest if available)?"
  run_checks

  confirm "Create annotated tag ${VERSION}?"
  git tag -a "${VERSION}" -m "${VERSION}"
  ok "Tag created: ${VERSION}"

  confirm "Push tag ${VERSION} to origin?"
  git push origin "${VERSION}"
  ok "Tag pushed: ${VERSION}"

  echo "== GitHub Release =="
  if gh_ready; then
    confirm "Create GitHub Release ${VERSION} with gh now?"
    gh release create "${VERSION}" \
      --repo "${REPO}" \
      --verify-tag \
      --title "${VERSION}" \
      --notes-file "${notes_file}"
    ok "GitHub Release created."
  else
    warn "gh is missing or not authenticated. Skipping GitHub Release creation."
    echo "Run manually:"
    echo "  gh auth login -h github.com -p https -s repo"
    echo "  gh release create ${VERSION} \\"
    echo "    --repo ${REPO} \\"
    echo "    --verify-tag \\"
    echo "    --title \"${VERSION}\" \\"
    echo "    --notes-file ${notes_file}"
  fi

  ok "Done."
}

main "$@"
