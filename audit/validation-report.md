# Validation report

Everything below was executed in this environment; nothing is inferred. Commands are given so each result can be reproduced.

## 1. Structural validation

Command: `python3 tools/validate.py --syntax`

| Check | Status | Detail |
|---|---|---|
| sources | PASS | 10/10 repositories inspected with commit recorded |
| classified | PASS | 10096 files, 0 unclassified; 3337 components, 0 with invalid disposition |
| destinations | PASS | 3833 copied files, 0 missing at destination |
| integrity | PASS | 3831 byte-compared, 0 differ; 2 recorded transform(s) excluded |
| manifests | PASS | 13 marketplace plugins; 15 plugin dirs |
| skills | PASS | 416 loaded skills have frontmatter; 2 keep a non-identifier upstream name (unchanged, indexed by directory) |
| references | PASS | 0 references broken by integration; 27 already unresolved in the source (reported in audit/validation-report.md) |
| json | PASS | 0 unparsable .json files, 0 identical to an unparsable upstream file (e.g. JSONC/templates) |
| syntax | PASS | checked {'.sh': 95, '.mjs': 28, '.cjs': 55, '.py': 300, '.js': 567}; 1 fail, 0 are integration regressions |
| routes | PASS | 0 problem(s) |
| licenses | PASS | plugins without LICENSE: 0 |
| docs | PASS | 60 path/plugin references checked in README.md and docs/INSTALL.md |
| reconcile | PASS | 3337 components across 10 repositories |

Notes on passing checks with examples:

- **skills**: claude-mem-cowork:agent-cost-report: upstream name 'Agent Cost Report'; claude-mem:agent-cost-report: upstream name 'Agent Cost Report'
- **syntax**: upstream-same plugins/claude-mem/skills/version-bump/scripts/generate_changelog.js

References already unresolved upstream (placeholders such as `0001-use-nextjs.md`, or files a skill writes into the user's project such as `assets/design-tokens.json`) are listed in `audit/upstream-unresolved-references.txt`.

## 2. Claude Code plugin validation

Command: `claude plugin validate plugins/<p>` (Claude Code 2.1.309) and `claude plugin validate .`

- 13 listed plugins: pass (ecc, mattpocock-skills, ui-ux-pro-max pass with upstream warnings: root CLAUDE.md not loaded / unknown field `id`; all plugins lack an icon, a directory-listing warning). Recorded output: `audit/claude-plugin-validate.txt`.
- Marketplace: pass after removing claude-mem and claude-mem-cowork, which fail because names starting with `claude-` are reserved. The upstream claude-mem repository fails the same check (baseline, not a regression).

## 3. Isolated install and functional tests

Throwaway `CLAUDE_CONFIG_DIR`, scratch npm/uv prefixes and a scratch `HOME` for claude-mem.

| Test | Result | Evidence |
|---|---|---|
| Marketplace add (isolated CLAUDE_CONFIG_DIR) | PASS | Successfully added marketplace: omega-engineering-x10 |
| Install all 12 listed plugins | PASS | 12/12 'Successfully installed plugin'; ecc reports 2 userConfig options |
| Loaded component inventory | PASS | audit/plugin-details/*.txt; counts equal registry (tests/test_omega.py::test_loaded_skill_counts_match_claude_plugin_details) |
| ECC with hooks disabled | PASS | settings.json stores hooks_enabled=false; ECC scripts/lib/hook-flags.js reads CLAUDE_PLUGIN_OPTION_HOOKS_ENABLED. Hook short-circuit at runtime not separately observed. |
| Skills visible in a live session | PASS | omega-core:omega-engineering-x10, vibesec:vibesec, graphify:graphify |
| Router used end-to-end by the model | PASS (gap found and fixed) | Model ran omega.py route + doctor, picked superpowers TDD, agent-browser, ui-ux-pro-max, reported agent-browser CLI missing with fix and fallback. Gap: security route not matched for 'password reset'; triggers added + regression test. |
| Requirements discovery avoids unnecessary questioning | PASS | Model declined grill-me/brainstorming ('task is fully specified'), chose TDD + verification-before-completion, asked the user nothing |
| agent-browser real browser session | PASS | snapshot refs e1-e3; fill+click produced 'Sent to dev@example.com'; 14,550-byte PNG saved; browser closed |
| agent-browser CLI-served skills | PASS | CLI lists exactly the 9 skill-data skills recorded in the registry |
| graphify code graph | PASS | 60 nodes, 142 edges, 5 communities; graph.json/graph.html/GRAPH_REPORT.md; explain returned callers/callees. path reported an ambiguous 'main' (3 matches) as designed |
| claude-mem worker from integrated copy | PASS | /api/health {status: ok, version: 15.0.1, initialized: true, mcpReady: true}; omega doctor detected it; worker stopped |
| find-skills search | BLOCKED (environment) | skills.sh denied by this environment's network proxy (CONNECT 403). The CLI prints 'No skills found' instead of a network error |
| UI UX Pro Max search from plugin copy | PASS | 3 palette results; full design-system recommendation printed |
| ECC rules installer | PASS | installed both; second run skipped existing pack without --force |
| Reproducible build | PASS | 10 repos checked out at pinned commits; 3,828 copied files byte-identical |
| anti-pattern-czar command (relocated from claude-mem .claude/commands) | PASS | ${CLAUDE_PLUGIN_ROOT} resolved to the plugin path in the live session; detector flagged src/b.ts:4 NO_LOGGING_IN_CATCH and exited 1; upstream and plugin copies print identical results |
| claude-mem install from pinned source marketplace (isolated HOME + CLAUDE_CONFIG_DIR) | PASS | installed 15.0.1 into plugins/cache/thedotmack/claude-mem/15.0.1 |
| claude-mem first session bootstrap | PASS (documented limitation) | ensure-launcher placed ~/.local/bin/claude-mem (protocol 1) and edited .bashrc; hooks in the same session: 'Executable not found in $PATH: claude-mem' (upstream first-run behaviour) |
| claude-mem capture of a known non-sensitive fact | PASS | claude-mem.db: sdk_sessions 1, user_prompts 1, tool_uses 2, observations 1 (type decision, facts include BLUE-HERON-42 and Tuesdays) |
| claude-mem retrieval via worker API | PASS | each returned observation #1 |
| claude-mem retrieval via mem-search skill in a new session without file access | PASS | Skill claude-mem:mem-search -> mcp search -> get_observations([1]); answered BLUE-HERON-42 / Tuesdays |
| claude-mem unavailable worker | PASS | hook exit 0 with {} and lazily restarted the worker (new PID); stopping again left no worker processes, port closed |
| claude-mem empty database | PASS | 'No results found matching "BLUE-HERON-42"'; observations endpoint HTTP 200 |
| claude-mem export/import retention round-trip | PASS | export: 1 obs, 2 sessions, 3 prompts; import 1: 1 obs imported; import 2: 0 imported, all skipped; search on imported DB finds observation |
| Graphify document + PDF + image extraction | PASS | graph.json 17 nodes / 18 edges: 6 from .md, 7 from paper.pdf (incl. 'Ripple Batching' and the 38 percent finding, present only in the PDF), 4 from diagram.png; `graphify explain 'Ripple Batching'` cites paper.pdf page 1 |
| Graphify missing optional grammar diagnostic | PASS | warning: 1 .sql file(s) contributed nothing ... tree_sitter_sql not installed. Install it with: pip install "graphifyy[sql]" |
| ECC hooks execute (hooks_enabled=true) | PASS | PreToolUse:Bash exit 2 'BLOCKED: --no-verify flag is not allowed with git commit'; commit count unchanged |
| ECC hooks disabled (hooks_enabled=false) | PASS | hooks short-circuit (exit 0), commit succeeded |
| ECC SessionStart hook dependencies | FAIL then FIXED | before: Cannot find module 'js-yaml'; after: 0 'Cannot find module', all SessionStart hooks exit 0; ECC tracked files unchanged |
| ECC TDD workflow | PASS | Skill ecc:tdd-workflow loaded; test written, 3/4 failed before fix; independent re-run: 4 tests OK; hook events SessionStart 9, PreToolUse 54, PostToolUse 22, all exit 0 |
| ECC code review + security review | PASS | flagged SQL injection at app.py:5 (critical, parameterized-query fix) and ZeroDivisionError; files unmodified |
| ECC debugging (build-fix) | PASS | fixed inventory.py only; test file untouched; `python3 -m unittest -v` OK |
| find-skills search (retry) | BLOCKED (environment) | CONNECT tunnel 403 from the proxy; CLI prints 'No skills found'; doctor reports [MISS] skills.sh reachable with fix |
| Clean install from a git-hosted marketplace (fresh HOME + CLAUDE_CONFIG_DIR, local smart-HTTP git server) | PASS | all installed into ~/.claude/plugins/cache/omega-engineering-x10/<plugin>/<version> at commit 3aaadbe/08598a3 |
| Doctor fix path from an installed omega-core | FAIL then FIXED | 1.0.0 pointed to a non-existent cache/.../scripts/install-plugin-deps.sh; after F9 + version bump 1.1.0 the suggested command installed ECC deps and the check turned OK |
| Plugin update flow | PASS after F10 | unchanged version: 'already at the latest version (1.0.0)'; after bump: 'updated from 1.0.0 to 1.1.0' |
| ECC hooks from the cache (git install) | PASS | 0 'Cannot find module'; PreToolUse exit 2 blocked the commit (count stayed 1); 3 Stop hooks reported outcome 'cancelled' at -p shutdown; all 8 ECC Stop hooks exit 0 when run directly |
| Superpowers SessionStart injection | PASS | additionalContext starts '<EXTREMELY_IMPORTANT> You have superpowers. **Below is the full content of your superpowers:using-superpowers skill' |
| ECC rule packs load as context | PASS | before: NONE; after: 80% coverage (testing.md) and CRITICAL Immutability (coding-style.md) |
| Superpowers version-bump upstream test with mikefarah yq v4 | PASS | 'Version-bump tests passed', exit 0 |
| Graphify MCP server | PASS | serverInfo graphify 0.9.94; 10 tools; get_node('Ripple Batching') -> Source paper.pdf page 1 |
| Graphify watch mode | PASS | '1 file(s) changed' -> 'Rebuilt: 3 nodes'; new function beta() in graph.json |
| Graphify exporters + clone | PASS (svg needs matplotlib) | all outputs written; graphml 17 nodes; cypher.txt 35 statements; svg failed with a clear ImportError until matplotlib was added, then written; clone fetched LICENSE/README/SKILL.md |
| Graphify transcription | BLOCKED (environment) | without [video]: clear 'pip install graphifyy[video]' ImportError; with it: model download ProxyError 403 (huggingface.co) |
| agent-browser dogfood QA workflow | PASS (after AGENT_BROWSER_SOCKET_DIR) | first run: 'Socket path would be 10x bytes (max 103)' with the long scratch HOME, skill stopped honestly; with a short socket dir it found both planted bugs, incl. 'ReferenceError: trackSignup is not defined' via `agent-browser errors`, with screenshots |
| claude-mem repair + smart-explore | PASS (git install) / FAIL (local-folder install) | local-folder marketplace: MCP ran in place without deps -> 'tree-sitter CLI is not installed' (reproduced directly with CLAUDE_PLUGIN_ROOT=source dir); git install + repair: RateTable L1-3, lookup L2, quote L5, free_shipping L8 |
| More ECC components | PASS | command injection (shell=True) critical, secret in ENV, unpinned base image, root user, API design issues; files unmodified |
| UI UX Pro Max /design-review | PASS | design-review subagent, 24 Playwright MCP calls, screenshots at 375/768/1440/1920 px; found both planted bugs plus missing live region and viewport meta |
| Replica recon + architect | PASS | recon.md, features.csv, 4 state screenshots; architecture.md and schema.sql derived from the recon |
| find-skills search (retest after reported network settings change) | BLOCKED (environment) | still CONNECT 403; proxy recentRelayFailures: {kind: connect_rejected, host: skills.sh:443, detail: gateway answered 403 to CONNECT (policy denial or upstream failure)} at 2026-10-23T19:41:21Z; CLI prints 'No skills found'; doctor [MISS] skills.sh reachable |
| Install from the real GitHub marketplace (fresh HOME + CLAUDE_CONFIG_DIR) | PASS | all four installed into ~/.claude/plugins/cache/omega-engineering-x10/<plugin>/<version> at gitCommitSha 72e07ab; route -> security+tdd; check-routes 0 problems; doctor fix installed ECC deps (check OK); live session: ECC PreToolUse blocked --no-verify, commit count unchanged, 0 module crashes |

## 4. Loaded components (from `claude plugin details`)

| Plugin | Inventory | Always-on tokens |
|---|---|---|
| agent-browser | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~336 |
| anti-pattern-czar | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~38 |
| ecc | Skills (408) Agents (71) Hooks (8) MCP servers (1) | ~47,561 |
| find-skills | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~100 |
| graphify | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~118 |
| mattpocock-skills-extras | Skills (11) Agents (0) Hooks (0) MCP servers (0) | ~746 |
| mattpocock-skills | Skills (27) Agents (0) Hooks (0) MCP servers (0) | ~1,651 |
| omega-core | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~239 |
| replica-skill | Skills (11) Agents (0) Hooks (0) MCP servers (0) | ~1,806 |
| superpowers | Skills (15) Agents (0) Hooks (1) MCP servers (0) | ~848 |
| ui-ux-pro-max-design-stack | Skills (2) Agents (1) Hooks (0) MCP servers (0) | ~236 |
| ui-ux-pro-max | Skills (7) Agents (0) Hooks (0) MCP servers (0) | ~1,067 |
| vibesec | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~65 |

## 5. Unit tests

Command: `python3 -m unittest discover -s tests -v`

```
test_rebuild_with_different_hash_seed_is_identical (test_omega.BuildDeterminismTest.test_rebuild_with_different_hash_seed_is_identical) ... ok
test_doctor_has_skills_sh_check_with_fix (test_omega.DoctorRegressionTests.test_doctor_has_skills_sh_check_with_fix) ... ok
test_ecc_missing_runtime_deps_detected (test_omega.DoctorRegressionTests.test_ecc_missing_runtime_deps_detected) ... ok
test_unreachable_host_is_reported_not_swallowed (test_omega.DoctorRegressionTests.test_unreachable_host_is_reported_not_swallowed) ... ok
test_core_registry_matches_root_registry (test_omega.RegistryTests.test_core_registry_matches_root_registry) ... ok
test_every_component_has_valid_disposition (test_omega.RegistryTests.test_every_component_has_valid_disposition) ... ok
test_every_source_skill_is_accounted_for (test_omega.RegistryTests.test_every_source_skill_is_accounted_for) ... ok
test_invocation_namespace_is_plugin_manifest_name (test_omega.RegistryTests.test_invocation_namespace_is_plugin_manifest_name) ... ok
test_loaded_skill_counts_match_claude_plugin_details (test_omega.RegistryTests.test_loaded_skill_counts_match_claude_plugin_details) ... ok
test_non_preserved_items_carry_a_reason (test_omega.RegistryTests.test_non_preserved_items_carry_a_reason) ... ok
test_check_routes_clean (test_omega.RouteTests.test_check_routes_clean) ... ok
test_cli_exit_codes (test_omega.RouteTests.test_cli_exit_codes) ... ok
test_curated_routes (test_omega.RouteTests.test_curated_routes) ... ok
test_doctor_reports_every_check_with_fix (test_omega.RouteTests.test_doctor_reports_every_check_with_fix) ... ok
test_keyword_search_reaches_long_tail (test_omega.RouteTests.test_keyword_search_reaches_long_tail) ... ok
test_killed_orphan_is_reaped (test_omega.SubreaperTests.test_killed_orphan_is_reaped) ... ok
test_returns_command_status_without_waiting_for_daemons (test_omega.SubreaperTests.test_returns_command_status_without_waiting_for_daemons) ... ok

----------------------------------------------------------------------
Ran 17 tests in 9.492s

OK
```

## 6. Baseline comparison

Default run: 14/20 upstream suites exit 0. Every failing test was reproduced individually and its cause confirmed (see `audit/baseline-results.md`, including the corrected-environment run). No failure involves a file changed by the integration: apart from two recorded transforms (VibeSec frontmatter name, anti-pattern-czar command path), every copied file is byte-identical to the pinned source, so upstream outcomes carry over to the integrated copies.

## 7. Disposition reconciliation

Counts are computed, not typed. Each row sums to the component total for that repository.

| Repository | Components | preserved | merged-with-traceability | adapted-with-traceability | excluded-with-justification | retained-as-external-runtime | blocked-uninspected | unclassified | Sum OK |
|---|---|---|---|---|---|---|---|---|---|
| vercel-labs/agent-browser | 44 | 11 | 1 | 0 | 20 | 12 | 0 | 0 | yes |
| mattpocock/skills | 58 | 55 | 0 | 0 | 3 | 0 | 0 | 0 | yes |
| Jakeschincariol/replica-skill | 15 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| affaan-m/ECC | 2766 | 1159 | 338 | 0 | 1269 | 0 | 0 | 0 | yes |
| vercel-labs/skills | 22 | 3 | 0 | 0 | 15 | 4 | 0 | 0 | yes |
| thedotmack/claude-mem | 261 | 93 | 2 | 1 | 144 | 21 | 0 | 0 | yes |
| BehiSecc/VibeSec-Skill | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | yes |
| nextlevelbuilder/ui-ux-pro-max-skill | 59 | 32 | 0 | 0 | 16 | 11 | 0 | 0 | yes |
| obra/superpowers | 66 | 66 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Graphify-Labs/graphify | 44 | 3 | 0 | 0 | 37 | 4 | 0 | 0 | yes |

## Skills only

| Repository | Skills | preserved | merged-with-traceability | adapted-with-traceability | excluded-with-justification | retained-as-external-runtime | blocked-uninspected | unclassified | Loaded |
|---|---|---|---|---|---|---|---|---|---|
| vercel-labs/agent-browser | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| mattpocock/skills | 38 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 38 |
| Jakeschincariol/replica-skill | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| affaan-m/ECC | 1062 | 311 | 234 | 0 | 517 | 0 | 0 | 0 | 311 |
| vercel-labs/skills | 3 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 1 |
| thedotmack/claude-mem | 41 | 30 | 0 | 0 | 11 | 0 | 0 | 0 | 30 |
| BehiSecc/VibeSec-Skill | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| nextlevelbuilder/ui-ux-pro-max-skill | 13 | 7 | 0 | 0 | 0 | 6 | 0 | 0 | 7 |
| obra/superpowers | 15 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 15 |
| Graphify-Labs/graphify | 16 | 1 | 0 | 0 | 15 | 0 | 0 | 0 | 1 |

## Files

Tracked files: 10090. merged-with-traceability: 3, excluded-with-justification: 5007, preserved: 3825, retained-as-external-runtime: 1253, adapted-with-traceability: 2



## 8. Open items

Rendered from `audit/open-items.json`; the same list is in `audit/unresolved-items.md`.

**Fixed in the release gate (11)**

| Id | Issue | Fix | Regression test |
|---|---|---|---|
| F1 | Nondeterministic build output (registry/audit ordering depended on PYTHONHASHSEED) | tools/build.py sorts skill directories by (depth, path) | tests/test_omega.py::BuildDeterminismTest |
| F2 | ECC SessionStart hook crash (Cannot find module 'js-yaml') with no OMEGA guidance | scripts/install-plugin-deps.sh (npm ci in a temp dir; ECC tracked files untouched) + doctor check + docs/INSTALL.md | tests/test_omega.py::DoctorRegressionTests::test_ecc_missing_runtime_deps_detected |
| F3 | find-skills network failures indistinguishable from empty results | omega.py doctor checks skills.sh reachability and explains the 'No skills found' symptom | DoctorRegressionTests::test_unreachable_host_is_reported_not_swallowed, ::test_doctor_has_skills_sh_check_with_fix |
| F4 | tools/subreaper.py waited for every descendant, so a daemon left by a test suite hung the runner until timeout (claude-mem exit 124 after 0 failures) | return as soon as the command exits, after reaping pending zombies | tests/test_omega.py::SubreaperTests |
| F5 | Baseline runner let claude-mem's tests write to the real $HOME/.claude-mem | tools/run-baselines.sh runs claude-mem tests with a throwaway HOME that links only ~/.cache, ~/.local and ~/.bun (a fully empty HOME made the Chroma connection-failure test time out: 0/1 vs 1/1 with the real HOME); stray /root/.claude-mem (default settings + fixture log lines) removed | manual: chroma-vector-sync 15/15 and native-memory-bridge writes contained in the throwaway HOME; /root/.claude-mem absent after the corrected re-run |
| F6 | docs/INSTALL.md: claude-mem export/import used wrong runner (bun) and paths that looked repo-relative | commands replaced by the ones actually run (npx tsx ./scripts/... from a source copy with deps) | tools/validate.py docs check (60 references) |
| F7 | unresolved-items.md reported 'none' while capabilities were unverified | report now has registry and runtime levels rendered from audit/open-items.json | - |
| F8 | `tools/build.py --no-copy` rewrote audit/transforms.json (and merge-map transforms) as empty, which would break the integrity check | transform records collected for every matching rule, independent of copy mode | tests/test_omega.py::BuildDeterminismTest (now also compares transforms.json and requires 2 records) |
| F9 | Doctor told cached installs to run scripts/install-plugin-deps.sh from a path that only exists in a checkout (found by the clean git install) | helper now ships in plugins/omega-core/scripts; scripts/ keeps a wrapper | DoctorRegressionTests::test_ecc_missing_runtime_deps_detected asserts the suggested helper exists |
| F10 | omega-core changed without a version bump, so `claude plugin update` kept the stale 1.0.0 copy | omega-core 1.1.0; INSTALL documents bumping versions | manual: update reported 1.0.0 -> 1.1.0 and the doctor fix then ran from the cache |
| F11 | Docs missing verified operational steps | INSTALL.md: AGENT_BROWSER_SOCKET_DIR for long paths, claude-mem repair/telemetry/install-from-git, graphify extras (video, svg) | tools/validate.py docs check |

**Implementation blockers (0)**: none.

**Environment-restricted (8)**
- E1: find-skills search (`npx skills find`)
- E2: Graphify upstream tests/test_security.py (7 tests)
- E5: Graphify audio/video transcription
- E6: claude-mem cloud sync and the claude-mem-cowork plugin
- E7: claude-mem OpenRouter/Gemini observer providers
- E8: Graphify Neo4j/FalkorDB push
- E9: agent-browser electron, slack, vercel-sandbox, agentcore, protected-vercel-deployments skills
- E10: macOS and Windows

**Upstream limitations (7)**
- U1: claude-mem committed build artifacts lag src/ (LAUNCHER_PROTOCOL 2 in src, 1 in plugin/scripts)
- U2: claude-mem test tests/memory/native-memory-bridge.test.ts writes to the real $HOME/.claude-mem
- U3: `npx skills find` reports network failures as 'No skills found'
- U4: ECC hooks need npm dependencies that plugin installs do not provide
- U5: claude-mem plain `/plugin install` leaves the plugin's npm deps (tree-sitter grammars, zod) uninstalled
- U6: claude-mem first session after install: hooks cannot find the `claude-mem` launcher
- U7: mattpocock `claude plugin validate . --strict`

**Not verified (6)**
- N1: Install on a second physical machine
- N2: ECC: 307 of 311 skills, 95 of 97 commands and 70 of 71 agents not individually exercised
- N3: claude-mem Chroma vector search specifically
- N4: agent-browser derive-client and webmcp-gen
- N5: Replica steps 3-11 (design, backend, build, test, diff, entrepreneur, brand, launch, deploy)
- N6: Individual UI UX Pro Max skills beyond search scripts and /design-review

Routing is keyword/curated and is a recommendation aid; final skill choice stays with the model, as shown in the live routing tests.

