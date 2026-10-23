# Unresolved items

Two levels: (1) registry accounting of source components, computed by the build; (2) runtime items from live verification, from `audit/open-items.json`. Zero registry gaps does not mean every capability was verified; see level 2.

## 1. Registry accounting

No component is unclassified, blocked, or an unreviewed unique variant (3337 of 3337 accounted for).

## 2. Runtime items

### Implementation blockers (OMEGA integration defects still open): 0

None.

### Environment-restricted (cannot be verified in this sandbox; requirement given): 4

- **E1** find-skills search (`npx skills find`). Evidence: https://skills.sh CONNECT 403 from this environment's proxy (curl + omega.py doctor). Network policy allowing https://skills.sh; re-run `npx skills@1.7.4 find react` and `omega.py doctor`
- **E2** Graphify upstream tests/test_security.py (7 tests). Evidence: ValueError: DNS resolution failed for 'example.com'. DNS + HTTP egress to example.com
- **E3** Superpowers upstream tests/version-bump/test-bump-version.sh. Evidence: /usr/bin/yq is the jq-wrapper yq 0.0.0; script uses mikefarah yq v4 syntax (strenv). mikefarah yq v4 on PATH
- **E4** mattpocock `claude plugin validate . --strict`. Evidence: --strict promotes two warnings (root CLAUDE.md not loaded; missing icon) to errors; non-strict validation passes. Upstream adds an icon / validator version that does not flag these; not an integration issue

### Upstream limitations (present in the pinned source; not integration regressions): 6

- **U1** claude-mem committed build artifacts lag src/ (LAUNCHER_PROTOCOL 2 in src, 1 in plugin/scripts). Evidence: 4 launcher tests fail at pinned commit dcb28a7 (= upstream main); pass 96/96 after upstream `npm run build`; published npm 15.0.1 ships ensure-launcher.cjs byte-identical to the integrated copy (protocol 1, self-consistent). Repo tests only; shipped artifacts are internally consistent. Live install placed a protocol-1 launcher and hooks worked.
- **U2** claude-mem test tests/memory/native-memory-bridge.test.ts writes to the real $HOME/.claude-mem. Evidence: Run with an isolated HOME creates $HOME/.claude-mem/settings.json and a log line. Test isolation only. Baseline runner isolates HOME.
- **U3** `npx skills find` reports network failures as 'No skills found'. Evidence: vercel-labs/skills src/find.ts: catch { return [] }. Misleading output; omega.py doctor now checks skills.sh reachability
- **U4** ECC hooks need npm dependencies that plugin installs do not provide. Evidence: SessionStart: Cannot find module 'js-yaml' (scripts/lib/project-detect.js); upstream TROUBLESHOOTING.md MODULE_NOT_FOUND. Mitigated: scripts/install-plugin-deps.sh + doctor check; verified hooks exit 0 afterwards
- **U5** claude-mem plain `/plugin install` leaves the plugin's npm deps (tree-sitter grammars, zod) uninstalled. Evidence: SessionStart: 'plugin dependencies are missing (zod, tree-sitter-cli, ...)'. Capture/search still worked; tree-sitter features need `npx claude-mem install`
- **U6** claude-mem first session after install: hooks cannot find the `claude-mem` launcher. Evidence: Executable not found in $PATH: "claude-mem" in session 1; works from session 2 with ~/.local/bin on PATH. Documented upstream-style restart requirement (docs/INSTALL.md)

### Not verified (capability present, not exercised end to end): 8

- **N1** Clean install from a git-hosted copy of the OMEGA marketplace. No remote exists and pushing was not authorized; only the local-directory marketplace was installed (where plugins run in place)
- **N2** ECC: 309 of 311 skills and 95 of 97 commands not individually exercised. Exercised live: ecc:tdd-workflow, ecc:security-review, /ecc:python-review, /ecc:build-fix, and the pre-bash hook path. All 311 skills, 97 commands and 71 agents are counted as loaded by `claude plugin details`
- **N3** claude-mem: smart-explore/tree-sitter features, cloud-sync, claude-mem-cowork, Chroma vector search, OpenRouter/Gemini providers. Needs `npx claude-mem install` or external services (cmem.ai) / API keys; capture, persistence, search, export/import, shutdown were verified
- **N4** Graphify: video/audio transcription, Neo4j/FalkorDB push, MCP server, watch mode, GitHub clone mode. Optional extras/services; code, Markdown, PDF and PNG extraction and querying were verified
- **N5** agent-browser specialised CLI skills (electron, slack, vercel-sandbox, agentcore, derive-client, webmcp-gen, protected-vercel-deployments). Need Electron apps, Slack/Vercel/AWS accounts; core open/snapshot/fill/click/screenshot was verified
- **N6** Full Replica pipeline, UI UX Pro Max /design-review agent run, Superpowers SessionStart injection content. Only structural checks, upstream tests and (for UI UX) the search scripts were run
- **N7** macOS and Windows. Linux container only
- **N8** ECC rule packs loaded as context in a session. Installer verified (copy, no-overwrite); loading into a session not observed

