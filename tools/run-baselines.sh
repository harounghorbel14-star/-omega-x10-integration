#!/usr/bin/env bash
# Run each source repository's own tests against a disposable copy of the sources.
#   tools/run-baselines.sh <copy-of-sources-dir> <results.jsonl>
# Never point this at the pristine sources/ dir: some suites install dependencies or write files.
# Each test is recorded as one JSON line: name, cwd, command, exit code, seconds, tail of output.
set -uo pipefail
BASE="$(cd "${1:?usage: run-baselines.sh <sources-copy> <out.jsonl>}" && pwd)"
OUT="${2:?missing output file}"
: > "$OUT"
LOGDIR="$(dirname "$OUT")/baseline-logs"; mkdir -p "$LOGDIR"
PYTEST_ENV="$BASE/.pytest-venv"

run() { # name, dir, timeout-seconds, command...
  local name="$1" dir="$2" to="$3"; shift 3
  local log="$LOGDIR/$name.log" start end rc
  start=$(date +%s)
  (cd "$BASE/$dir" && timeout "$to" bash -c "$*") >"$log" 2>&1; rc=$?
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
run claude-mem-bun-test       thedotmack__claude-mem 1800 "bun install --ignore-scripts >/dev/null 2>&1; bun test tests"
run graphify-pytest           Graphify-Labs__graphify 2400 "uv sync -q >/dev/null 2>&1; uv run --with pytest pytest -q tests"
echo "done -> $OUT"
