#!/usr/bin/env bash
# Install a plugin's runtime npm dependencies without touching its tracked files.
#   scripts/install-plugin-deps.sh <plugin-dir>
# ECC's hooks require npm packages (js-yaml, ajv, @iarna/toml, sql.js) that Claude Code does not
# install; upstream TROUBLESHOOTING.md ("MODULE_NOT_FOUND") says to run npm install in the plugin
# directory. Running npm there rewrites ECC's yarn.lock, so this script runs `npm ci` from the
# pinned package-lock.json in a temporary directory and moves only node_modules into place.
# Install scripts are disabled (--ignore-scripts) and dev dependencies are omitted.
# Pass the installed plugin path, e.g. ~/.claude/plugins/cache/omega-engineering-x10/ecc/2.2.3,
# or plugins/ecc when the marketplace is a local directory (plugins then run in place).
set -euo pipefail
DIR="$(cd "${1:?usage: install-plugin-deps.sh <plugin-dir>}" && pwd)"
[ -f "$DIR/package.json" ] && [ -f "$DIR/package-lock.json" ] || { echo "no package.json + package-lock.json in $DIR" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp "$DIR/package.json" "$DIR/package-lock.json" "$TMP/"
(cd "$TMP" && npm ci --omit=dev --ignore-scripts --no-audit --no-fund)
if [ -e "$DIR/node_modules" ]; then
  echo "replacing existing $DIR/node_modules"
  rm -rf "$DIR/node_modules"
fi
mv "$TMP/node_modules" "$DIR/node_modules"
echo "installed runtime dependencies into $DIR/node_modules (remove that directory to undo)"
