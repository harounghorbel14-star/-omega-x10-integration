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
| superpowers-version-bump | obra__superpowers | `bash tests/version-bump/test-bump-version.sh` | 3 | 0 | environment (confirmed: passes with mikefarah yq v4) |
| superpowers-codex-manifest | obra__superpowers | `bash tests/codex/test-marketplace-manifest.sh` | 0 | 0 | pass |
| superpowers-shell-lint | obra__superpowers | `bash tests/shell-lint/test-lint-shell.sh` | 0 | 0 | pass |
| mattpocock-validate | mattpocock__skills | `claude plugin validate . --strict` | 1 | 2 | environment/tool-version |
| mattpocock-version-check | mattpocock__skills | `node scripts/sync-plugin-version.mjs --check` | 0 | 0 | pass |
| agent-browser-launcher | vercel-labs__agent-browser | `node --test test/launcher.test.mjs` | 0 | 1 | pass |
| vercel-skills-vitest | vercel-labs__skills | `pnpm install --frozen-lockfile --ignore-scripts >/dev/null 2>&1; pnpm exec vitest run` | 1 | 96 | 4/978 fail: all environmental (confirmed) |
| vercel-skills-typecheck | vercel-labs__skills | `pnpm exec tsc --noEmit` | 0 | 6 | pass |
| ecc-npm-test | affaan-m__ECC | `npm ci --ignore-scripts --no-audit --no-fund >/dev/null 2>&1; npm test` | 1 | 1217 | 2/8879 fail: both environmental (confirmed) |
| graphify-pytest | Graphify-Labs__graphify | `uv sync -q >/dev/null 2>&1; uv run --with pytest pytest -q tests` | 1 | 775 | 25/8471 fail: all environmental (confirmed) |
| claude-mem-bun-test | thedotmack__claude-mem | `bun install --ignore-scripts >/dev/null 2>&1; bun test tests` | 1 | 801 | 71/10120 fail: 67 environmental + 4 upstream build skew (all confirmed) |

**14/20 suites exit 0.**

## superpowers-version-bump (exit 3)

Needs mikefarah yq v4 (`strenv`); this machine's /usr/bin/yq is the jq wrapper. With yq v4.44.3 (release binary, SHA-256 verified) first on PATH the test passes ('Version-bump tests passed'). Script under test (scripts/bump-version.sh) is release tooling, not a skill.

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

3 detect-agent tests read AI_AGENT/CLAUDE_CODE_* env vars set by this harness. 1 Notion test: @clack/prompts isUnicodeSupported() returns false when TERM=linux (this container's TERM), so it draws '|' instead of the box character the test strips. With the env vars unset and TERM=xterm-256color: 978/978 pass.

```
     45| });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/4]⎯


 Test Files  2 failed | 68 passed (70)
      Tests  4 failed | 974 passed (978)
   Start at  13:56:57
   Duration  86.75s (transform 5.45s, setup 0ms, import 15.54s, tests 204.47s, environment 12ms)

```

## ecc-npm-test (exit 1)

8877/8879 tests passed across 428 files. (1) hooks/hooks.test.js 'observe.sh falls back to legacy output fields': with this harness's CLAUDE_*/AI_AGENT env vars unset the file passes 258/258 (observe.sh skips non-CLI entrypoints by design). (2) scripts/install-sh.test.js 'leader exit cannot hide an owned descendant retaining captured pipes' ('owned fixture process survived cleanup'): the descendant IS killed (State Z, zombie, 500 ms after SIGKILL) but this sandbox's PID 1 (`process_api`) never reaps orphans, and the test's kill(pid, 0) succeeds on a zombie. Under a reaping subreaper (tools/subreaper.py, equivalent to tini / docker --init) the file passes 19/19. ECC's cleanup safeguards were not changed. Requirement elsewhere: an init that reaps zombies.

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

9753 pass, 71 fail, 296 skip across 977 files. 61: tree-sitter CLI binary missing because install scripts were skipped (--ignore-scripts); fixed by upstream's trustedDependencies install. Remaining 10, each reproduced: 4 launcher tests (ensure-launcher x3, launcher --version) expect LAUNCHER_PROTOCOL 2 from src/ but the committed plugin/scripts artifacts were last rebuilt 2026-10-20, before the bump in 8eb3dabc (2026-10-22); after upstream `npm run build`: 96/96 launcher tests pass. Upstream main == pinned commit, and published npm 15.0.1 ships an ensure-launcher.cjs byte-identical to the integrated copy, so shipped artifacts are self-consistent. 1 plugin-distribution test needs the git-ignored dist/ build output (passes after build). 2 observation semantic-row-filter tests take 7.1 s and 7.9 s on this 4-core machine, over bun's 5 s default (pass with --timeout 60000). 1 Chroma connection-failure test and 1 Codex PreToolUse transport test fail only under full-suite load (pass alone at the default timeout). 1 processesStillUsingArm test: the container locale is POSIX, so pgrep cannot match the emoji in its regex (passes with LC_ALL=C.UTF-8).

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

## Corrected-environment run

`CORRECTED_ENV=1 tools/run-baselines.sh <fresh copy> audit/corrected/baseline-results.jsonl` applies only the requirements confirmed above: agent env vars unset, TERM=xterm-256color, LC_ALL=C.UTF-8, a reaping subreaper, claude-mem trusted install scripts + upstream `npm run build` + `--timeout 30000`, Graphify full git history + `--extra sql`. Network policy, yq and --strict validator rules are unchanged.

| Suite | Exit (default run) | Exit (corrected) | Tail |
|---|---|---|---|
| replica-pytest | 0 | 0 | .........................................................                [100%] / 57 passed in 1.49s |
| uiux-validate-csv | 0 | 0 | CSV validation passed: 35 runtime CSV files checked. |
| uiux-smoke-domains | 0 | 0 | PASS  google-fonts   1 / OK: 12/12 domains returned ≥1 result |
| uiux-smoke-stacks | 0 | 0 | PASS  uwp                1 / OK: 22/22 stacks returned ≥1 result |
| uiux-pytest | 0 | 0 | .                                                                        [100%] / 1 passed in 0.02s |
| superpowers-skill-size | 0 | 0 | PASS: every SKILL.md is under 20000 bytes |
| superpowers-hooks | 0 | 0 | [PASS] session-start with cat on PATH emits nested additionalContext / [PASS] session-start pipes its JSON through cat when cat is on PATH / STATUS: PASSED |
| superpowers-skill-struct | 0 | 0 | [PASS] skill files say 'your human partner', not 'the user' / Passed: 46  Failed: 0 |
| superpowers-find-polluter | 0 | 0 | [PASS] empty result exits via the clean path / All tests passed |
| superpowers-version-bump | 3 | 3 | jq: error: strenv/1 is not defined at <top-level>, line 1: / .[strenv(FIELD)] / select(tag == "!!str") / jq: 1 compile error |
| superpowers-codex-manifest | 0 | 0 | Codex marketplace manifest looks good |
| superpowers-shell-lint | 0 | 0 | [PASS] --all includes tracked .sh file / [PASS] --all ignores untracked shell files / All shell lint script tests passed |
| mattpocock-validate | 1 | 1 | The directory also runs a safety scan and a policy review that this command does not. / ✘ Validation failed (--strict treats warnings as errors) |
| mattpocock-version-check | 0 | 0 | plugin.json version is 1.3.1 (already in sync) |
| agent-browser-launcher | 0 | 0 | # skipped 0 / # todo 0 / # duration_ms 380.863745 |
| vercel-skills-vitest | 1 | 0 | Start at  17:12:57 / Duration  95.32s (transform 6.46s, setup 0ms, import 15.34s, tests 198.19s, environment 20 |
| vercel-skills-typecheck | 0 | 0 |  |
| ecc-npm-test | 1 | 0 | ╚══════════════════════════════════════════════════════════╝ / Passed: 8879, Failed: 0 |
| graphify-pytest | 1 | 1 | FAILED tests/test_security.py::test_safe_fetch_text_decodes_utf8 - ValueError... / FAILED tests/test_security.py::test_safe_fetch_text_replaces_bad_bytes - Valu... / 7 failed, 8371 passed, 154 skipped, 2087 warnings in 666.26s (0:11:06) |
| claude-mem-bun-test | 1 | 0 | 0 fail / 44932 expect() calls / Ran 10120 tests across 977 files. [836.23s] |

**Corrected run: 17/20 suites exit 0.**

## Not run, with reason

- superpowers `tests/claude-code`, `tests/explicit-skill-requests`, `tests/opencode`, `tests/kimi`, `tests/antigravity`, `tests/devin`, `tests/hermes`, `tests/pi`: drive live model sessions or other harnesses (paid, non-deterministic, or not installed).
- superpowers `tests/brainstorm-server`: needs its own npm install and a browser; the brainstorming skill's optional visual server is not used by OMEGA routing.
- ECC `test:plugin-setup-platform` (docker), `test:python` (needs ECC's Python test deps).
- agent-browser Rust tests (`cargo test`): the CLI is consumed as a published binary; its launcher test ran.
- claude-mem evals and docker e2e; Graphify benchmarks.
- VibeSec: no tests upstream (single Markdown skill).

