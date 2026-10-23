# Installing OMEGA-ENGINEERING X10

OMEGA-ENGINEERING X10 is a **Claude Code plugin marketplace**. Each of the ten sources is a separate
plugin, plus `omega-core` (the master router). Install only what you need: every plugin adds its
skill descriptions to every session (see "Context cost").

All commands below were run in an isolated `CLAUDE_CONFIG_DIR` during validation (see
`audit/validation-report.md`). They do not modify anything outside Claude Code's config directory
except where a step says so.

## 1. Add the marketplace

From GitHub (verified):

```bash
claude plugin marketplace add harounghorbel14-star/-omega-x10-integration
```

From a local checkout:

```bash
claude plugin marketplace add /path/to/OMEGA-ENGINEERING-X10
# or inside Claude Code:
/plugin marketplace add /path/to/OMEGA-ENGINEERING-X10
```

### Upload the router to claude.ai (single skill)

The claude.ai Skills uploader takes one skill folder per ZIP and rejects symbolic links, so do not
upload a ZIP of this repository (GitHub's "Download ZIP" stores `plugins/mattpocock-skills/AGENTS.md`
as a link). Build the router-only ZIP instead:

```bash
python3 tools/package_skill.py                  # writes and verifies dist/omega-engineering-x10.zip
python3 tools/package_skill.py --verify any.zip # check another skill ZIP before uploading
```

Then in claude.ai: Settings → Capabilities → Skills → Upload skill, and choose
`dist/omega-engineering-x10.zip` (code execution must be enabled). On claude.ai the router can only
route: the specialist plugins are Claude Code plugins, so it names the right one and uses the
route's fallback. Use the marketplace above for the full system.

## 2. Install plugins

Recommended core set (about 3.2k always-on tokens):

```bash
claude plugin install omega-core@omega-engineering-x10
claude plugin install superpowers@omega-engineering-x10
claude plugin install mattpocock-skills@omega-engineering-x10
claude plugin install vibesec@omega-engineering-x10
claude plugin install find-skills@omega-engineering-x10
```

Add specialists as needed:

```bash
claude plugin install agent-browser@omega-engineering-x10            # needs the agent-browser CLI (step 3)
claude plugin install graphify@omega-engineering-x10                 # needs the graphify CLI (step 3)
claude plugin install ui-ux-pro-max@omega-engineering-x10
claude plugin install ui-ux-pro-max-design-stack@omega-engineering-x10
claude plugin install replica-skill@omega-engineering-x10
claude plugin install mattpocock-skills-extras@omega-engineering-x10 # misc + beta skills
claude plugin install anti-pattern-czar@omega-engineering-x10        # TS error-handling audit (needs Bun)
claude plugin install ecc@omega-engineering-x10                      # large: ~47.6k always-on tokens
```

ECC asks for two options (`hooks_enabled`, `hook_profile`). To keep its skills and commands without
its lifecycle hooks:

```bash
claude plugin install ecc@omega-engineering-x10 --config hooks_enabled=false
```

**ECC hooks need npm runtime dependencies** (`js-yaml`, `ajv`, `@iarna/toml`, `sql.js`) that a plugin
install does not provide. Without them its SessionStart hook fails with
`Cannot find module 'js-yaml'` (upstream TROUBLESHOOTING.md, "MODULE_NOT_FOUND"). Install them into
the installed plugin directory with the OMEGA helper, which runs `npm ci` from ECC's pinned
`package-lock.json` in a temporary directory so ECC's tracked files (npm would rewrite its
`yarn.lock`) stay unchanged:

```bash
# the helper ships in omega-core, so it is available without a checkout:
~/.claude/plugins/cache/omega-engineering-x10/omega-core/1.0.0/scripts/install-plugin-deps.sh \
    ~/.claude/plugins/cache/omega-engineering-x10/ecc/2.2.3
# from a checkout (wrapper): scripts/install-plugin-deps.sh <installed ecc dir>
# when the marketplace was added from a local directory, plugins run in place:
scripts/install-plugin-deps.sh plugins/ecc
```

`omega.py doctor` prints the exact command for each installed ECC copy that lacks the dependencies.

`omega.py doctor` reports every installed ECC copy that is missing these dependencies.

### claude-mem (persistent memory)

claude-mem is **not** listed in the OMEGA marketplace. Claude Code reserves plugin names that start
with `claude-` for Anthropic in third-party marketplaces (the upstream repository fails the same
validator check), and its runtime expects its own marketplace id. Install it from upstream; the
copy in `plugins/claude-mem` is the same commit and is kept for audit and offline reading.

```bash
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem@thedotmack
```

or `npx claude-mem@15.0.1 install`. Privacy notes:

- The upstream installer offers a hosted observer (cmem.ai sign-in). To stay local, pass an explicit
  `--provider`, or set `CLAUDE_MEM_ONLINE_OPTIN=false`.
- Data lives in `~/.claude-mem/` (`claude-mem.db`, `chroma/`, `settings.json`); override with
  `CLAUDE_MEM_DATA_DIR`. Delete that directory to erase all memory.
- `claude-mem:cloud-sync` and the `claude-mem-cowork` plugin send data to cmem.ai. Opt-in only.
- Its SessionStart hook may add the `claude-mem` launcher to your shell PATH (it edits a shell rc
  file and says so).
- First session after install: the launcher is placed in `~/.local/bin/claude-mem`, but hooks in that
  same session report `Executable not found in $PATH: "claude-mem"`. Start a new shell (or add
  `~/.local/bin` to PATH) and restart Claude Code; capture works from the next session (verified).
- To install exactly the pinned commit instead of upstream `main`, add the source snapshot as the
  marketplace: `claude plugin marketplace add ../sources/thedotmack__claude-mem` then
  `claude plugin install claude-mem@thedotmack` (this is how the capture/search loop was verified).
- A plain `/plugin install` leaves the plugin's own npm dependencies (tree-sitter grammars, zod...)
  uninstalled; the SessionStart hook says "plugin dependencies are missing". Memory capture and search
  still work. Run `npx claude-mem@15.0.1 repair` once (non-interactive; it runs `bun install` in the
  plugin cache) and `smart-explore` works (verified: function/method outline of a Python file).
- Telemetry is **on by default** (anonymous, opt-out; `npx claude-mem help`). Disable it with
  `npx claude-mem@15.0.1 telemetry disable` (writes `~/.claude-mem/telemetry.json`).
- Install claude-mem from a git URL (GitHub or a git server), not from a local folder: a local-folder
  marketplace runs the plugin in place, so its MCP tools (smart-explore) use the folder without the
  dependencies `repair` installed in the cache (verified failure and fix).
- The worker listens on `127.0.0.1:<37700 + uid % 100>` unless `CLAUDE_MEM_WORKER_PORT` is set.
- Retention: upstream ships export/import scripts, documented in
  `../sources/thedotmack__claude-mem/docs/public/usage/export-import.mdx`. They import claude-mem's
  `src/` and talk to the running worker, so run them from a copy of the pinned source with its
  dependencies installed (`bun install`), while the worker is running:
  `npx tsx ./scripts/export-memories.ts "<query>" backup.json` and
  `npx tsx ./scripts/import-memories.ts backup.json` (verified: export, import, and re-import
  skipping every duplicate). Review exports before sharing; they are plain text.

### ECC rules (optional)

Claude Code plugins cannot ship rules. Copy only the packs you want:

```bash
scripts/install-ecc-rules.sh --list
scripts/install-ecc-rules.sh common typescript              # -> ~/.claude/rules/ecc/
scripts/install-ecc-rules.sh --project common python        # -> ./.claude/rules/ecc/
```

It never overwrites an existing pack unless you pass `--force`.

## 3. Runtime dependencies

| Needed by | Install | Verify |
|---|---|---|
| agent-browser | `npm i -g agent-browser@0.39.2 && agent-browser install` (downloads Chrome). To reuse an existing Chromium: `export AGENT_BROWSER_EXECUTABLE_PATH=/path/to/chrome` | `agent-browser --version`; `agent-browser skills list` |
| graphify | `uv tool install graphifyy==0.9.94` (or `pipx install graphifyy==0.9.94`). Extras: `graphifyy[pdf]` (PDF papers), `[sql]` (SQL files), `[mcp]` (`graphify-mcp` server), `[watch]` (`graphify watch`), `[video]` (audio/video transcription; downloads a Whisper model from huggingface.co on first use), `[neo4j]`, `[falkordb]`; `graphify export svg` also needs `matplotlib`. Docs, PDFs and images are extracted by `/graphify` subagents inside Claude Code; code-only builds need no LLM (`graphify update .`) | `graphify --help` |
| graphify always-on (optional) | `graphify install --platform claude` adds a CLAUDE.md section and a PreToolUse hook (upstream behaviour). Remove with `graphify uninstall`. The snippet is also in `plugins/graphify/always_on/claude-md.md` | |
| find-skills | Node.js with `npx` (runs `npx skills@1.7.4`); needs network access to skills.sh | `npx skills find react` |
| ui-ux-pro-max | Python 3 (scripts use the standard library) | `python3 <skill>/scripts/search.py "saas" --design-system` |
| replica-skill | Python 3; `pillow` for `replica-diff/imgdiff.py` | |
| claude-mem | Bun and uv (auto-installed by claude-mem), Node.js | `omega.py doctor` |
| ui-ux-pro-max-design-stack MCP (optional) | `plugins/ui-ux-pro-max-design-stack/optional/mcp.json` lists Playwright, Chrome DevTools and shadcn MCP servers. Not auto-enabled; copy into your project's `.mcp.json` if wanted | |

Check everything at once:

```bash
python3 plugins/omega-core/scripts/omega.py doctor
```

## Context cost

Measured with `claude plugin details` (always-on tokens added to every session):

| Plugin | Skills | Agents | Hooks | Always-on |
|---|---|---|---|---|
| omega-core | 1 | 0 | 0 | ~239 |
| agent-browser | 1 | 0 | 0 | ~336 |
| mattpocock-skills | 27 | 0 | 0 | ~1,651 |
| mattpocock-skills-extras | 11 | 0 | 0 | ~746 |
| replica-skill | 11 | 0 | 0 | ~1,806 |
| ecc | 408 (311 skills + 97 commands) | 71 | 8 events | ~47,561 |
| find-skills | 1 | 0 | 0 | ~100 |
| vibesec | 1 | 0 | 0 | ~65 |
| ui-ux-pro-max | 7 | 0 | 0 | ~1,067 |
| ui-ux-pro-max-design-stack | 2 commands | 1 | 0 | ~236 |
| superpowers | 15 | 0 | 1 (SessionStart) | ~848 |
| graphify | 1 | 0 | 0 | ~118 |
| anti-pattern-czar | 1 command | 0 | 0 | ~38 |

## Hooks you get

| Plugin | Events | What runs |
|---|---|---|
| superpowers | SessionStart | injects the `using-superpowers` bootstrap |
| ecc | PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, PreCompact, SessionStart, Stop, SessionEnd | local Node scripts in `plugins/ecc/scripts/hooks` (quality gates, git safety, cost tracking, session memory). Disable with `hooks_enabled=false`; tune with `hook_profile=minimal|standard|strict` |
| claude-mem (upstream install) | Setup, SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd | the claude-mem launcher/worker |

Superpowers and ECC both inject SessionStart context; that is upstream behaviour and they do not
conflict, but if you want only one bootstrap, disable ECC hooks.

## Update

```bash
scripts/fetch-sources.sh ../sources      # or move sources to newer commits yourself
python3 tools/build.py --sources ../sources
python3 tools/validate.py --syntax
python3 -m unittest discover -s tests
claude plugin marketplace update omega-engineering-x10
claude plugin update <plugin>@omega-engineering-x10
```

`tools/build.py` fails if an upstream file matches no rule in `tools/rules.py`, so new upstream
content cannot be dropped silently. When you change a plugin, bump its `version`:
`claude plugin update` keeps an installed copy whose version is unchanged (verified with omega-core
1.0.0 -> 1.1.0).

## Remove

```bash
claude plugin uninstall <plugin>@omega-engineering-x10
claude plugin marketplace remove omega-engineering-x10
rm -rf ~/.claude/rules/ecc            # only if you installed ECC rules
uv tool uninstall graphifyy; npm rm -g agent-browser   # runtimes, if installed
# claude-mem: /plugin uninstall claude-mem@thedotmack ; rm -rf ~/.claude-mem to delete memory
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `omega.py doctor` shows `agent-browser not on PATH` | Install the CLI (step 3). If you installed it with `npm i --prefix`, add that `node_modules/.bin` to PATH |
| agent-browser cannot launch Chrome | Run `agent-browser install` or set `AGENT_BROWSER_EXECUTABLE_PATH` |
| `npx skills find` prints "No skills found" for every query | The CLI reports network failures this way. Check that `https://skills.sh` is reachable (it was blocked by this validation environment's proxy) |
| claude-mem worker not reachable | It starts on the first session after install. Check `~/.claude-mem/settings.json` for `CLAUDE_MEM_WORKER_PORT`; run `omega.py doctor` |
| graphify says no graph | Run `/graphify` (full, uses subagents for docs) or `graphify update .` (code only, no LLM) |
| ECC SessionStart hook: `Cannot find module 'js-yaml'` | Run `scripts/install-plugin-deps.sh <installed ecc dir>` (see section 2) |
| claude-mem hooks: `Executable not found in $PATH: "claude-mem"` | First run only: add `~/.local/bin` to PATH (the hook already edited your shell rc) and restart Claude Code |
| graphify warns `.sql file(s) contributed nothing ... tree_sitter_sql not installed` | Optional grammar: `uv tool install --force 'graphifyy[sql]==0.9.94'` |
| agent-browser: `Socket path would be N bytes (max 103)` | Your HOME/working path is too long for a Unix socket. `export AGENT_BROWSER_SOCKET_DIR=/tmp/ab` (any short directory) |
| claude-mem `smart_outline`: "the tree-sitter CLI is not installed" | Run `npx claude-mem@15.0.1 repair`; if claude-mem was installed from a local folder, reinstall it from a git URL |
| `claude plugin update` says "already at the latest version" after a change | Plugins update by version number; maintainers must bump `version` in the changed plugin's `plugin.json` |
| Session feels slow / context full | ECC adds ~47.6k tokens always-on. Uninstall it or disable plugins you are not using (`claude plugin disable`) |
| `claude plugin validate` warns "CLAUDE.md at the plugin root is not loaded" (ecc, mattpocock-skills) | Upstream layout; harmless |
| Skills uploader: `Zip file contains a symbolic link` | The ZIP was made from the repository. Upload the ZIP built by `python3 tools/package_skill.py` (see "Upload the router to claude.ai") |
