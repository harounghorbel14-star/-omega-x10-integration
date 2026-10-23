# Baseline results (upstream test suites)

Each source's own tests, run by `tools/run-baselines.sh` on a disposable copy of the sources (dependency installs with `--ignore-scripts`). These establish what already passes or fails upstream, so integration regressions can be told apart from baseline problems. Logs: `audit/baseline-logs/` (not committed; regenerate with the script).

| Suite | Repository dir | Command | Exit | Seconds | Classification |
|---|---|---|---|---|---|
| replica-pytest | Jakeschincariol__replica-skill | `/home/user/omega-x10/baseline/.pytest-venv/bin/python -m pytest -q tests` | 0 | 2 | pass |
| uiux-validate-csv | nextlevelbuilder__ui-ux-pro-max-skill | `python3 scripts/validate-csv.py` | 0 | 1 | pass |
| uiux-smoke-domains | nextlevelbuilder__ui-ux-pro-max-skill | `bash scripts/smoke-domains.sh` | 0 | 2 | pass |
| uiux-smoke-stacks | nextlevelbuilder__ui-ux-pro-max-skill | `bash scripts/smoke-stacks.sh` | 0 | 3 | pass |
| uiux-pytest | nextlevelbuilder__ui-ux-pro-max-skill | `/home/user/omega-x10/baseline/.pytest-venv/bin/python -m pytest -q scripts/tests` | 0 | 0 | pass |
| superpowers-skill-size | obra__superpowers | `bash tests/skill-size/test-skill-size.sh` | 0 | 0 | pass |
| superpowers-hooks | obra__superpowers | `bash tests/hooks/test-session-start.sh` | 0 | 1 | pass |
| superpowers-skill-struct | obra__superpowers | `bash tests/diagnosing-superpowers/test-skill-structure.sh` | 0 | 0 | pass |
| superpowers-find-polluter | obra__superpowers | `bash tests/systematic-debugging/test-find-polluter.sh` | 0 | 1 | pass |
| superpowers-version-bump | obra__superpowers | `bash tests/version-bump/test-bump-version.sh` | 3 | 0 | environment (confirmed: wrong yq variant installed) |
| superpowers-codex-manifest | obra__superpowers | `bash tests/codex/test-marketplace-manifest.sh` | 0 | 0 | pass |
| superpowers-shell-lint | obra__superpowers | `bash tests/shell-lint/test-lint-shell.sh` | 0 | 0 | pass |
| mattpocock-validate | mattpocock__skills | `claude plugin validate . --strict` | 1 | 2 | environment/tool-version |
| mattpocock-version-check | mattpocock__skills | `node scripts/sync-plugin-version.mjs --check` | 0 | 0 | pass |
| agent-browser-launcher | vercel-labs__agent-browser | `node --test test/launcher.test.mjs` | 0 | 1 | pass |
| vercel-skills-vitest | vercel-labs__skills | `pnpm install --frozen-lockfile --ignore-scripts >/dev/null 2>&1; pnpm exec vitest run` | 1 | 96 | 4/978 fail: 3 environmental (confirmed), 1 likely terminal formatting |
| vercel-skills-typecheck | vercel-labs__skills | `pnpm exec tsc --noEmit` | 0 | 6 | pass |
| ecc-npm-test | affaan-m__ECC | `npm ci --ignore-scripts --no-audit --no-fund >/dev/null 2>&1; npm test` | 1 | 1217 | 2/8879 fail: 1 environmental (confirmed), 1 undiagnosed |
| graphify-pytest | Graphify-Labs__graphify | `uv sync -q >/dev/null 2>&1; uv run --with pytest pytest -q tests` | 1 | 775 | 25/8471 fail: all environmental (confirmed) |
| claude-mem-bun-test | thedotmack__claude-mem | `bun install --ignore-scripts >/dev/null 2>&1; bun test tests` | 1 | 801 | 71/10120 fail: 61 environmental (confirmed), 10 undiagnosed |

**14/20 suites exit 0.**

## superpowers-version-bump (exit 3)

Needs mikefarah yq v4 (`strenv`); this machine's yq/jq lacks it. Script under test (scripts/bump-version.sh) is release tooling, not a skill.

```
jq: error: strenv/1 is not defined at <top-level>, line 1:
.[strenv(FIELD)] | select(tag == "!!str")  
jq: 1 compile error
```

## mattpocock-validate (exit 1)

`--strict` turns two warnings into errors: root CLAUDE.md not loaded, and missing plugin icon (a newer validator rule). No errors without --strict; the OMEGA copy validates.

```

About these checks:

  > This folder also holds a marketplace manifest. The plugin directory treats such a folder as a plugin, so these checks cover only the plugin in this folder. To check another plugin that the marketp

These plugin directory checks do not change the result below.

The directory also runs a safety scan and a policy review that this command does not.

× Validation failed (--strict treats warnings as errors)
```

## vercel-skills-vitest (exit 1)

4/978 failed. 3 detect-agent tests fail because this harness sets AI_AGENT/CLAUDE_CODE_* env vars; re-run with those unset: they pass. 1 Notion test compares terminal-formatted output and still fails. Tests cover the `skills` CLI source, which is an external runtime here.

```
     45| });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/4]⎯


 Test Files  2 failed | 68 passed (70)
      Tests  4 failed | 974 passed (978)
   Start at  13:56:57
   Duration  86.75s (transform 5.45s, setup 0ms, import 15.54s, tests 204.47s, environment 12ms)

```

## ecc-npm-test (exit 1)

8877/8879 tests passed across 428 files. (1) hooks/hooks.test.js 'observe.sh falls back to legacy output fields': re-run with this harness's CLAUDE_*/AI_AGENT env vars unset, the file passes 258/258, so it is environmental (observe.sh skips non-CLI entrypoints by design). (2) scripts/install-sh.test.js 'leader exit cannot hide an owned descendant retaining captured pipes' ('owned fixture process survived cleanup') still fails with the env cleared. It exercises ECC's install.sh process cleanup, which the plugin install path does not use; likely sandbox process-group behaviour, not confirmed.

```
║  Total Tests: 8879                                       ║
║  Passed:      8877  ✓                                    ║
║  Failed:         2  ✗                                    ║
║  Files: 426 passed, 2 failed                             ║
╠══════════════════════════════════════════════════════════╣
║  ✗ hooks/hooks.test.js                                   ║
║  ✗ scripts/install-sh.test.js                            ║
╚══════════════════════════════════════════════════════════╝

Passed: 8877, Failed: 2
```

## graphify-pytest (exit 1)

8246 passed, 25 failed, 200 skipped. All three groups confirmed: test_security.py (7) needs DNS for example.com, blocked by this environment's network policy; test_skillgen.py (11) reads the v8 baseline from git history, absent from the shallow clone; after `git fetch --unshallow` it passes 71/71; test_ext_tagged_id_clash.py (7) needs the optional `sql` extra (tree-sitter-sql); with `uv run --extra sql` it passes 14/14.

```
FAILED tests/test_skillgen.py::test_all_progressive_hosts_check_and_audit_clean
FAILED tests/test_skillgen.py::test_monolith_roundtrip_passes_for_aider_and_devin
FAILED tests/test_skillgen.py::test_monoliths_change_only_sanctioned_lines - ...
FAILED tests/test_skillgen.py::test_always_on_roundtrip_is_byte_faithful - Sy...
FAILED tests/test_skillgen.py::test_audit_coverage_passes_for_every_split_host
FAILED tests/test_skillgen.py::test_audit_catches_an_induced_per_host_drop - ...
FAILED tests/test_skillgen.py::test_audit_catches_a_dropped_non_allowlisted_heading
FAILED tests/test_skillgen.py::test_amp_audit_coverage_passes_against_its_own_v8
FAILED tests/test_skillgen.py::test_agents_audit_baseline_is_amps_v8_body - S...
25 failed, 8246 passed, 200 skipped, 2082 warnings in 740.46s (0:12:20)
```

## claude-mem-bun-test (exit 1)

9753 pass, 71 fail, 296 skip across 977 files. 61 failures (smart-file-read outlines, tree-sitter CLI provisioning) came from installing dependencies with --ignore-scripts, which skips tree-sitter-cli's install.js binary download. After running only that script (tree-sitter 0.26.13) and re-running the 17 failing files with the harness env vars unset: 350 pass, 10 fail. The 10 remaining (ensure-launcher x3, observation semantic row filters x2, Chroma connection-failure handling, npm tarball contents, launcher --version, Codex PreToolUse transport, processesStillUsingArm with real pgrep/lsof) were not individually diagnosed; they involve compiling the launcher, Chroma, npm pack and host process tools. Note: the worker started and served /api/health from the integrated copy (functional test).

```
[SETTINGS] Created settings file with defaults: /tmp/claude-mem-merge-route-dCnAFK/settings.json

tests/worker/http/routes/work-state-routes.test.ts:
[SETTINGS] Created settings file with defaults: /tmp/claude-mem-corrupt-KBrAVn/settings.json

 9753 pass
 296 skip
 71 fail
 43936 expect() calls
Ran 10120 tests across 977 files. [800.71s]
```

## Not run, with reason

- superpowers `tests/claude-code`, `tests/explicit-skill-requests`, `tests/opencode`, `tests/kimi`, `tests/antigravity`, `tests/devin`, `tests/hermes`, `tests/pi`: drive live model sessions or other harnesses (paid, non-deterministic, or not installed).
- superpowers `tests/brainstorm-server`: needs its own npm install and a browser; the brainstorming skill's optional visual server is not used by OMEGA routing.
- ECC `test:plugin-setup-platform` (docker), `test:python` (needs ECC's Python test deps).
- agent-browser Rust tests (`cargo test`): the CLI is consumed as a published binary; its launcher test ran.
- claude-mem evals and docker e2e; Graphify benchmarks.
- VibeSec: no tests upstream (single Markdown skill).

