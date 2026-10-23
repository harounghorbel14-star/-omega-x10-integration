# Unresolved items

Two levels: (1) registry accounting of source components, computed by the build; (2) runtime items from live verification, from `audit/open-items.json`. Zero registry gaps does not mean every capability was verified; see level 2.

## 1. Registry accounting

No component is unclassified, blocked, or an unreviewed unique variant (3337 of 3337 accounted for).

## 2. Runtime items

### Implementation blockers (OMEGA integration defects still open): 0

None.

### Environment-restricted (cannot be verified in this sandbox; requirement given): 8

- **E1** find-skills search (`npx skills find`). Evidence: https://skills.sh CONNECT 403 (proxy log: connect_rejected, policy denial) on the initial test and again on the 2026-10-23T19:41Z retest after a reported network settings change; `npx skills find` prints 'No skills found'. Network policy allowing https://skills.sh in the session that runs the test (start a session after changing the environment's network access); re-run `npx skills@1.7.4 find react` and `omega.py doctor`
- **E2** Graphify upstream tests/test_security.py (7 tests). Evidence: ValueError: DNS resolution failed for 'example.com'. DNS + HTTP egress to example.com
- **E5** Graphify audio/video transcription. Evidence: With graphifyy[video] installed, transcribe('standup.wav') starts ('transcribing ... model=base') and fails downloading the Whisper model: ProxyError 403 (huggingface.co blocked). Network access to huggingface.co
- **E6** claude-mem cloud sync and the claude-mem-cowork plugin. Evidence: https://cmem.ai unreachable (proxy 403); also needs a cmem.ai account. cmem.ai access and an account; opt-in by design
- **E7** claude-mem OpenRouter/Gemini observer providers. Evidence: openrouter.ai unreachable; no provider API keys in this environment. Provider API key and network access
- **E8** Graphify Neo4j/FalkorDB push. Evidence: No database server; docker CLI present but no daemon (/var/run/docker.sock missing). Cypher export (35 statements) verified. A reachable Neo4j or FalkorDB instance
- **E9** agent-browser electron, slack, vercel-sandbox, agentcore, protected-vercel-deployments skills. Evidence: Need Electron apps, Slack workspace, Vercel or AWS accounts. Those apps/accounts
- **E10** macOS and Windows. Evidence: Linux container only. Run docs/INSTALL.md steps on those OSes

### Upstream limitations (present in the pinned source; not integration regressions): 7

- **U1** claude-mem committed build artifacts lag src/ (LAUNCHER_PROTOCOL 2 in src, 1 in plugin/scripts). Evidence: 4 launcher tests fail at pinned commit dcb28a7 (= upstream main); pass 96/96 after upstream `npm run build`; published npm 15.0.1 ships ensure-launcher.cjs byte-identical to the integrated copy (protocol 1, self-consistent). Repo tests only; shipped artifacts are internally consistent. Live install placed a protocol-1 launcher and hooks worked.
- **U2** claude-mem test tests/memory/native-memory-bridge.test.ts writes to the real $HOME/.claude-mem. Evidence: Run with an isolated HOME creates $HOME/.claude-mem/settings.json and a log line. Test isolation only. Baseline runner isolates HOME.
- **U3** `npx skills find` reports network failures as 'No skills found'. Evidence: vercel-labs/skills src/find.ts: catch { return [] }. Misleading output; omega.py doctor now checks skills.sh reachability
- **U4** ECC hooks need npm dependencies that plugin installs do not provide. Evidence: SessionStart: Cannot find module 'js-yaml' (scripts/lib/project-detect.js); upstream TROUBLESHOOTING.md MODULE_NOT_FOUND. Mitigated: scripts/install-plugin-deps.sh + doctor check; verified hooks exit 0 afterwards
- **U5** claude-mem plain `/plugin install` leaves the plugin's npm deps (tree-sitter grammars, zod) uninstalled. Evidence: SessionStart: 'plugin dependencies are missing (zod, tree-sitter-cli, ...)'. Capture/search still worked; tree-sitter features need `npx claude-mem install`
- **U6** claude-mem first session after install: hooks cannot find the `claude-mem` launcher. Evidence: Executable not found in $PATH: "claude-mem" in session 1; works from session 2 with ~/.local/bin on PATH. Documented upstream-style restart requirement (docs/INSTALL.md)
- **U7** mattpocock `claude plugin validate . --strict`. Evidence: --strict promotes two warnings (root CLAUDE.md not loaded; missing icon) to errors; non-strict validation passes. Upstream metadata vs. current validator rules; not an integration issue

### Not verified (capability present, not exercised end to end): 6

- **N1** Install on a second physical machine. Verified on this machine from the real GitHub repo (harounghorbel14-star/-omega-x10-integration @ 72e07ab) in a fresh HOME and config; a different machine/OS was not used (see E10)
- **N2** ECC: 307 of 311 skills, 95 of 97 commands and 70 of 71 agents not individually exercised. Exercised live: ecc:tdd-workflow, ecc:security-review, ecc:docker-patterns, ecc:api-design, /ecc:python-review, /ecc:build-fix, agent ecc:security-reviewer, the pre-bash hook path and all 8 Stop hooks. All components are counted as loaded by `claude plugin details`
- **N3** claude-mem Chroma vector search specifically. Search returned correct results, but whether the hybrid path used Chroma embeddings or FTS5 alone was not isolated
- **N4** agent-browser derive-client and webmcp-gen. Not run; core browser actions and the dogfood QA workflow were verified
- **N5** Replica steps 3-11 (design, backend, build, test, diff, entrepreneur, brand, launch, deploy). recon and architect were run live; the remaining steps build and deploy a full app and were not run (upstream helper scripts pass their tests)
- **N6** Individual UI UX Pro Max skills beyond search scripts and /design-review. design-system, ui-styling, brand, banner-design, slides, design not run individually

