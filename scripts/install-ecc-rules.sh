#!/usr/bin/env bash
# Opt-in install of ECC rule packs. Claude Code plugins cannot ship rules, so ECC documents
# copying whole rule directories (README "Rules"). This script does exactly that, and refuses to
# overwrite an existing pack unless --force is given.
#   scripts/install-ecc-rules.sh [--project] [--force] common typescript [python ...]
#   scripts/install-ecc-rules.sh --list
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
RULES="$HERE/plugins/ecc/rules"
TARGET="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/rules/ecc"
FORCE=0; PACKS=()
for a in "$@"; do
  case "$a" in
    --list) ls "$RULES" | grep -v '\.md$'; exit 0 ;;
    --project) TARGET="$PWD/.claude/rules/ecc" ;;
    --force) FORCE=1 ;;
    -*) echo "unknown option $a" >&2; exit 2 ;;
    *) PACKS+=("$a") ;;
  esac
done
[ ${#PACKS[@]} -gt 0 ] || { echo "usage: $0 [--project] [--force] <pack>... (see --list)" >&2; exit 2; }
mkdir -p "$TARGET"
for p in "${PACKS[@]}"; do
  [ -d "$RULES/$p" ] || { echo "no such rule pack: $p (see --list)" >&2; exit 1; }
  if [ -e "$TARGET/$p" ] && [ $FORCE -eq 0 ]; then
    echo "skip $p: $TARGET/$p exists (use --force to replace)"; continue
  fi
  rm -rf "${TARGET:?}/$p"
  cp -R "$RULES/$p" "$TARGET/$p"
  echo "installed $p -> $TARGET/$p"
done
echo "Rules are always-loaded context. Remove with: rm -rf \"$TARGET/<pack>\""
