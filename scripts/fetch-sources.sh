#!/usr/bin/env bash
# Re-create the pinned source snapshots used to build OMEGA-ENGINEERING X10.
#   scripts/fetch-sources.sh [target-dir]   (default: ../sources next to this repo)
# Each repository is checked out at the exact commit recorded in audit/source-manifest.json,
# so tools/build.py reproduces plugins/ byte-for-byte and the excluded files stay inspectable.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HERE/../sources}"
mkdir -p "$DEST"
python3 - "$HERE/audit/source-manifest.json" <<'PY' | while read -r dir remote commit; do
import json, sys
for m in json.load(open(sys.argv[1])):
    print(m["dir"], m["remote"], m["commit"])
PY
  if [ -d "$DEST/$dir/.git" ]; then
    git -C "$DEST/$dir" fetch -q origin "$commit" 2>/dev/null || git -C "$DEST/$dir" fetch -q origin
  else
    git clone -q "$remote" "$DEST/$dir"
  fi
  git -C "$DEST/$dir" -c advice.detachedHead=false checkout -q "$commit"
  echo "ok  $dir @ ${commit:0:12}"
done
