# Validation report

Everything below was executed in this environment; nothing is inferred. Commands are given so each result can be reproduced.

## 1. Structural validation

Command: `python3 tools/validate.py --syntax`

| Check | Status | Detail |
|---|---|---|
| sources | PASS | 10/10 repositories inspected with commit recorded |
| classified | PASS | 10094 files, 0 unclassified; 3337 components, 0 with invalid disposition |
| destinations | PASS | 3829 copied files, 0 missing at destination |
| integrity | PASS | 3828 byte-compared, 0 differ; 1 recorded transform(s) excluded |
| manifests | PASS | 12 marketplace plugins; 14 plugin dirs |
| skills | PASS | 416 loaded skills have frontmatter; 2 keep a non-identifier upstream name (unchanged, indexed by directory) |
| references | PASS | 0 references broken by integration; 27 already unresolved in the source (reported in audit/validation-report.md) |
| json | PASS | 0 unparsable .json files, 0 identical to an unparsable upstream file (e.g. JSONC/templates) |
| syntax | PASS | checked {'.sh': 95, '.mjs': 28, '.cjs': 55, '.py': 300, '.js': 567}; 1 fail, 0 are integration regressions |
| routes | PASS | 0 problem(s) |
| licenses | PASS | plugins without LICENSE: 0 |
| reconcile | PASS | 3337 components across 10 repositories |

Notes on passing checks with examples:

- **skills**: claude-mem-cowork:agent-cost-report: upstream name 'Agent Cost Report'; claude-mem:agent-cost-report: upstream name 'Agent Cost Report'
- **syntax**: upstream-same plugins/claude-mem/skills/version-bump/scripts/generate_changelog.js

References already unresolved upstream (placeholders such as `0001-use-nextjs.md`, or files a skill writes into the user's project such as `assets/design-tokens.json`) are listed in `audit/upstream-unresolved-references.txt`.

## 2. Claude Code plugin validation

Command: `claude plugin validate plugins/<p>` (Claude Code 2.1.309) and `claude plugin validate .`

- 12 listed plugins: pass (ecc, mattpocock-skills, ui-ux-pro-max pass with upstream warnings: root CLAUDE.md not loaded / unknown field `id`; all plugins lack an icon, a directory-listing warning).
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
| graphify semantic extraction (docs/papers/images via subagents) | NOT RUN | Requires an interactive session dispatching extraction subagents; untested |
| claude-mem worker from integrated copy | PASS | /api/health {status: ok, version: 15.0.1, initialized: true, mcpReady: true}; omega doctor detected it; worker stopped |
| claude-mem capture + search through hooks | NOT RUN | Requires installing claude-mem hooks into a session; search endpoint returned an empty body on an empty database, so search behaviour is unverified |
| find-skills search | BLOCKED (environment) | skills.sh denied by this environment's network proxy (CONNECT 403). The CLI prints 'No skills found' instead of a network error |
| UI UX Pro Max search from plugin copy | PASS | 3 palette results; full design-system recommendation printed |
| ECC rules installer | PASS | installed both; second run skipped existing pack without --force |
| Reproducible build | PASS | 10 repos checked out at pinned commits; 3,828 copied files byte-identical |

## 4. Loaded components (from `claude plugin details`)

| Plugin | Inventory | Always-on tokens |
|---|---|---|
| agent-browser | Skills (1) Agents (0) Hooks (0) MCP servers (0) | ~336 |
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

----------------------------------------------------------------------
Ran 11 tests in 1.227s

OK
```

## 6. Baseline comparison

14/17 upstream suites exit 0; every non-zero result was investigated and is environmental or a tool-version difference (see `audit/baseline-results.md`). Integration does not modify any upstream file except the VibeSec frontmatter name, and the integrity check proves the other copied files are byte-identical to the pinned sources, so upstream test outcomes carry over to the integrated copies unchanged.

## 7. Disposition reconciliation

Counts are computed, not typed. Each row sums to the component total for that repository.

| Repository | Components | preserved | merged-with-traceability | adapted-with-traceability | excluded-with-justification | retained-as-external-runtime | blocked-uninspected | unclassified | Sum OK |
|---|---|---|---|---|---|---|---|---|---|
| vercel-labs/agent-browser | 44 | 11 | 1 | 0 | 20 | 12 | 0 | 0 | yes |
| mattpocock/skills | 58 | 55 | 0 | 0 | 3 | 0 | 0 | 0 | yes |
| Jakeschincariol/replica-skill | 15 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| affaan-m/ECC | 2766 | 1266 | 234 | 0 | 1266 | 0 | 0 | 0 | yes |
| vercel-labs/skills | 22 | 3 | 0 | 0 | 15 | 4 | 0 | 0 | yes |
| thedotmack/claude-mem | 261 | 92 | 2 | 0 | 148 | 19 | 0 | 0 | yes |
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

Tracked files: 10090. merged-with-traceability: 3, excluded-with-justification: 5011, preserved: 3824, retained-as-external-runtime: 1251, adapted-with-traceability: 1



## 8. Known limitations and unverified behaviour

- claude-mem full capture/injection loop and memory search were not exercised end to end (requires installing its hooks into a session); only the worker start/health/stop from the integrated copy was verified.
- Graphify semantic extraction for docs/papers/images/video (subagent-driven) was not run; the code-only graph path was.
- find-skills search could not reach skills.sh from this environment (network policy).
- ECC: 311 skills/97 commands/71 agents load (counted by Claude Code); individual ECC skills were not each executed. ECC hooks were installed but not observed firing in a live session.
- Superpowers' SessionStart bootstrap was installed; its hook test passed upstream, but injection in a live session was not separately inspected.
- Replica, UI UX Pro Max design-stack review flow and the remaining specialist skills were validated structurally and by their upstream tests, not by full task runs.
- Routing is keyword/curated; it is a recommendation aid. Final skill choice remains the model's, as shown in the two live routing tests.

