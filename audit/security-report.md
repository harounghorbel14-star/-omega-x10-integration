# Security, privacy and dependency report

Scope: everything copied into `plugins/` plus the runtimes those plugins invoke. Sources were
treated as untrusted: install scripts were read before anything ran, dependency installs used
`--ignore-scripts`, and all runtime tests used scratch prefixes, a throwaway `CLAUDE_CONFIG_DIR`
and a throwaway `HOME` (claude-mem). Nothing was installed globally and no user config was touched.

This is a review of behaviour and configuration, not a full code audit of ~3,800 copied files.

## What executes automatically once a plugin is installed

| Plugin | Mechanism | Behaviour | Control |
|---|---|---|---|
| superpowers | SessionStart hook `hooks/run-hook.cmd session-start` | Prints the `using-superpowers` skill into context. Reviewed: local file read, no network. | Uninstall or disable the plugin |
| ecc | 27 hook groups over 8 events, Node scripts in `scripts/hooks/` | Quality gates, `--no-verify` blocking, config protection, cost tracking, session summaries, optional GateGuard. URLs found in hook scripts are documentation links, not requests. `insaits-security-monitor.py` only runs with `ECC_ENABLE_INSAITS=1`. | `--config hooks_enabled=false` (exported as `CLAUDE_PLUGIN_OPTION_HOOKS_ENABLED`, read by `scripts/lib/hook-flags.js`), `hook_profile`, `ECC_DISABLED_HOOKS` |
| ecc | `.mcp.json` | Starts `npx -y chrome-devtools-mcp@1.10.1` (downloads from npm on first use; pinned version). | `claude plugin disable ecc` or deny the MCP server |
| claude-mem (upstream install) | Setup, SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd hooks | Captures tool use into a local worker and SQLite/Chroma store, injects past observations. `ensure-launcher.cjs` may append the launcher directory to PATH in a shell rc file. | Uninstall; delete `~/.claude-mem` |
| all others | none | Skills load only when invoked | |

## Data leaving the machine

| Component | Destination | When |
|---|---|---|
| claude-mem observer | Anthropic (your plan) by default in this test; the installer offers cmem.ai hosted observer, OpenRouter or Gemini | Every compressed observation. Choose the provider at install; `CLAUDE_MEM_ONLINE_OPTIN=false` skips sign-in |
| claude-mem `cloud-sync`, `claude-mem-cowork` | cmem.ai | Only if set up. Not listed in the OMEGA marketplace |
| find-skills | skills.sh search API; GitHub for installs | On `npx skills find/add` |
| graphify | GitHub (`graphify clone`), arbitrary URLs (`graphify add <url>`), optional Gemini/LLM APIs for semantic extraction, Neo4j/FalkorDB if pushed | On those commands only |
| ui-ux-pro-max `design` | Gemini / Atlas Cloud / MuAPI for logo generation (needs the user's API key) | Only when generating logos |
| agent-browser | Sites you open; Chrome download on `agent-browser install` | On use |
| ECC skills | Many integrate external APIs (x-api, exa-search, fal-ai, jira, etc.) using the user's own keys | On use |

## Network installers and auto-installs (all require user approval in practice)

- `plugins/graphify/skills/graphify/SKILL.md` runs `uv tool install --upgrade graphifyy` or
  `pip install graphifyy` when graphify is missing (upstream behaviour). The OMEGA router tells the
  model to ask first; pin with `graphifyy==0.9.94`.
- `find-skills` documents `npx skills add <pkg> -g -y` (skips the CLI's confirmation). The OMEGA
  router requires showing the user the source repository and asking before any install.
- claude-mem auto-installs Bun and uv if missing.
- The upstream README for claude-mem's OpenClaw integration uses `curl ... | bash`; not used here.

## Secrets

- No real credentials found. A regex scan of `plugins/` for AWS (`AKIA…`), GitHub (`ghp_`,
  `github_pat_`), OpenAI/Anthropic/OpenRouter (`sk-…`), Slack (`xox?-`), Google (`AIza…`) keys and
  PEM private-key headers matched only three test fixtures:
  `claude-mem/skills/agent-cost-report/scripts/tests/test_measure.py` (and its cowork copy),
  `sk-or-v1-testkeytestkey…0000`, and `ecc/examples/unified-memory/conformance.cjs`, a string
  labelled "Synthetic non-key fixture". Environment variable names such as `GEMINI_API_KEY` appear
  only as documentation.
- agent-browser has an authentication vault and session state persistence; those live in the
  user's agent-browser data directory, never in this repo.
- claude-mem must not be used to store secrets. Its observations include tool inputs/outputs; if a
  secret appears in a tool call it can be captured. Mitigation: exclude sensitive projects (see
  upstream docs) or do not install claude-mem for them.

## Dependency risks

| Dependency | Pinned? | Note |
|---|---|---|
| agent-browser 0.39.2 (npm, native binary) | yes (install command) | `postinstall` downloads the platform binary |
| skills 1.7.4 (npx) | yes in OMEGA docs; find-skills itself calls `npx skills` unpinned | |
| graphifyy 0.9.94 (PyPI) | yes in OMEGA docs | many tree-sitter wheels; `serve.py` floors starlette above two CVE fixes |
| chrome-devtools-mcp 1.10.1 | yes (ECC `.mcp.json`) | |
| claude-mem 15.0.1 | yes via commit; upstream marketplace tracks `main` | Pin by installing from a checkout at the recorded commit |
| ECC / superpowers / mattpocock / replica / UI UX / VibeSec | vendored at recorded commits | Plain files; scripts run only when invoked |

## Integration decisions with security impact

- Hooks are never merged across plugins; each plugin keeps its own `hooks.json`, so disabling a
  plugin removes exactly its hooks.
- `ui-ux-pro-max-design-stack`'s MCP servers are placed in `optional/mcp.json` instead of the
  auto-loaded `.mcp.json`, so they do not start unless the user copies them.
- claude-mem and claude-mem-cowork are not listed in the marketplace (name reservation plus the
  cowork plugin's cloud data flow); they must be installed deliberately from upstream.
- Routing rule 5: security guidance is additive and the stricter requirement wins; routing rule 7:
  missing tools are reported, never faked.
- VibeSec is guidance and checklists. Findings based on it are static and must be labelled
  "potential" until exploitability is verified (routing-rules.json, security route).
