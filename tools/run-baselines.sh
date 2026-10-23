#!/usr/bin/env bash
# Run each source repository's own tests against a disposable copy of the sources.
#   tools/run-baselines.sh <copy-of-sources-dir> <results.jsonl>
# Never point this at the pristine sources/ dir: some suites install dependencies or write files.
# Each test is recorded as one JSON line: name, cwd, command, exit code, seconds, tail of output.
set -uo pipefail
BASE="$(cd "${1:?usage: run-baselines.sh <sources-copy> <out.jsonl>}" && pwd)"
OUT="${2:?missing output file}"
[ "${APPEND:-0}" = 1 ] || : > "$OUT"   # APPEND=1 keeps earlier results; ONLY="a b" runs a subset
LOGDIR="$(dirname "$OUT")/baseline-logs"; mkdir -p "$LOGDIR"
PYTEST_ENV="$BASE/.pytest-venv"

# CORRECTED_ENV=1 applies the environment requirements confirmed for this sandbox's failures
# (audit/baseline-results.md): agent env vars unset, TERM=xterm-256color, a UTF-8 locale, and a
# reaping subreaper (tools/subreaper.py) because PID 1 here does not reap orphaned zombies.
# Suite-specific setup (full git history, optional extras, upstream build) is applied below.
# claude-mem's tests always get a throwaway HOME: tests/memory/native-memory-bridge.test.ts writes to
# $HOME/.claude-mem (upstream test-isolation defect, audit/open-items.json U2). Tool caches (~/.cache,
# ~/.local, ~/.bun) are linked in, because a fully empty HOME makes the Chroma tests time out.
ISOHOME='H=$(mktemp -d); for d in .cache .local .bun; do [ -e "$HOME/$d" ] && ln -s "$HOME/$d" "$H/$d"; done; HOME=$H'

if [ "${CORRECTED_ENV:-0}" = 1 ]; then
  for v in $(env | grep -oE '^(CLAUDE[A-Z_]*|AI_AGENT|CLAUDECODE)=' | tr -d =); do unset "$v"; done
  export TERM=xterm-256color LC_ALL=C.UTF-8 LANG=C.UTF-8
  WRAP="python3 $(cd "$(dirname "$0")" && pwd)/subreaper.py"
else
  WRAP=""
fi

run() { # name, dir, timeout-seconds, command...
  local name="$1" dir="$2" to="$3"; shift 3
  if [ -n "${ONLY:-}" ] && [[ " $ONLY " != *" $name "* ]]; then return 0; fi
  local log="$LOGDIR/$name.log" start end rc
  start=$(date +%s)
  (cd "$BASE/$dir" && timeout "$to" $WRAP bash -c "$*") >"$log" 2>&1; rc=$?
  end=$(date +%s)
  python3 - "$name" "$dir" "$*" "$rc" "$((end-start))" "$log" >>"$OUT" <<'PY'
import json, sys
name, d, cmd, rc, secs, log = sys.argv[1:]
lines = open(log, errors="replace").read().splitlines()
print(json.dumps({"name": name, "cwd": d, "command": cmd, "exit": int(rc), "seconds": int(secs),
                  "timed_out": rc == "124", "tail": lines[-15:]}))
PY
  echo "[$rc] $name (${end}s-${start}s)"
}

# shared pytest venv (pytest is not installed system-wide)
uv venv -q "$PYTEST_ENV" >/dev/null 2>&1 && uv pip install -q --python "$PYTEST_ENV/bin/python" pytest pillow >/dev/null 2>&1
PY="$PYTEST_ENV/bin/python"

run replica-pytest            Jakeschincariol__replica-skill 600 "$PY -m pytest -q tests"
run uiux-validate-csv         nextlevelbuilder__ui-ux-pro-max-skill 300 "python3 scripts/validate-csv.py"
run uiux-smoke-domains        nextlevelbuilder__ui-ux-pro-max-skill 300 "bash scripts/smoke-domains.sh"
run uiux-smoke-stacks         nextlevelbuilder__ui-ux-pro-max-skill 300 "bash scripts/smoke-stacks.sh"
run uiux-pytest               nextlevelbuilder__ui-ux-pro-max-skill 300 "$PY -m pytest -q scripts/tests"
run superpowers-skill-size    obra__superpowers 300 "bash tests/skill-size/test-skill-size.sh"
run superpowers-hooks         obra__superpowers 300 "bash tests/hooks/test-session-start.sh"
run superpowers-skill-struct  obra__superpowers 300 "bash tests/diagnosing-superpowers/test-skill-structure.sh"
run superpowers-find-polluter obra__superpowers 300 "bash tests/systematic-debugging/test-find-polluter.sh"
run superpowers-version-bump  obra__superpowers 300 "bash tests/version-bump/test-bump-version.sh"
run superpowers-codex-manifest obra__superpowers 300 "bash tests/codex/test-marketplace-manifest.sh"
run superpowers-shell-lint    obra__superpowers 300 "bash tests/shell-lint/test-lint-shell.sh"
run mattpocock-validate       mattpocock__skills 300 "claude plugin validate . --strict"
run mattpocock-version-check  mattpocock__skills 300 "node scripts/sync-plugin-version.mjs --check"
run agent-browser-launcher    vercel-labs__agent-browser 300 "node --test test/launcher.test.mjs"
run vercel-skills-vitest      vercel-labs__skills 1200 "pnpm install --frozen-lockfile --ignore-scripts >/dev/null 2>&1; pnpm exec vitest run"
run vercel-skills-typecheck   vercel-labs__skills 600 "pnpm exec tsc --noEmit"
run ecc-npm-test              affaan-m__ECC 1800 "npm ci --ignore-scripts --no-audit --no-fund >/dev/null 2>&1; npm test"
if [ "${CORRECTED_ENV:-0}" = 1 ]; then
  # claude-mem: trusted install scripts (tree-sitter CLI download, per package.json trustedDependencies),
  # then upstream's own build, because the committed plugin/scripts artifacts predate src/ (protocol 1 vs 2).
  run claude-mem-bun-test     thedotmack__claude-mem 2400 "bun install >/dev/null 2>&1; npm run build >/dev/null 2>&1; $ISOHOME bun test --timeout 30000 tests"
  run graphify-pytest         Graphify-Labs__graphify 2400 "git fetch -q --unshallow origin 2>/dev/null; uv sync -q --extra sql >/dev/null 2>&1; uv run --extra sql --with pytest pytest -q tests"
else
  run claude-mem-bun-test     thedotmack__claude-mem 1800 "bun install --ignore-scripts >/dev/null 2>&1; $ISOHOME bun test tests"
  run graphify-pytest         Graphify-Labs__graphify 2400 "uv sync -q >/dev/null 2>&1; uv run --with pytest pytest -q tests"
fi
echo "done -> $OUT"
