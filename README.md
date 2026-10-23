# OMEGA-ENGINEERING X10

Ten engineering skill sources integrated into one Claude Code plugin marketplace, with a master
router (`omega-core`), a complete capability registry and a full provenance audit.

| # | Source | Plugin(s) | What you get |
|---|---|---|---|
| 1 | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | `agent-browser` | Browser automation skill + 9 CLI-served specialised skills (core, dogfood, electron, slack, derive-client, vercel-sandbox, protected-vercel-deployments, agentcore, webmcp-gen) |
| 2 | [mattpocock/skills](https://github.com/mattpocock/skills) | `mattpocock-skills`, `mattpocock-skills-extras` | grill-me and 26 promoted skills; 11 misc/beta skills in the extras plugin |
| 3 | [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) | `replica-skill` | 11-step clean-room app replication pipeline with Python helpers |
| 4 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | `ecc` | 311 skills, 97 commands, 71 agents, hooks, 22 rule packs |
| 5 | [vercel-labs/skills](https://github.com/vercel-labs/skills) | `find-skills` | Skill discovery via `npx skills` |
| 6 | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | `claude-mem`, `claude-mem-cowork` (install from upstream), `anti-pattern-czar` | Persistent memory: hooks, worker, MCP, 27 skills; plus its error-handling anti-pattern command |
| 7 | [BehiSecc/VibeSec-Skill](https://github.com/BehiSecc/VibeSec-Skill) | `vibesec` | Secure-coding guide for web apps |
| 8 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `ui-ux-pro-max`, `ui-ux-pro-max-design-stack` | 7 design skills with searchable style/palette/font/UX databases; design-review agent + commands |
| 9 | [obra/superpowers](https://github.com/obra/superpowers) | `superpowers` | 15 workflow skills (brainstorm, plan, TDD, debug, review, worktrees, verification) |
| 10 | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | `graphify` | Knowledge-graph skill for code and documents |

## Quick start

```bash
claude plugin marketplace add harounghorbel14-star/-omega-x10-integration   # or a local checkout path
claude plugin install omega-core@omega-engineering-x10
claude plugin install superpowers@omega-engineering-x10
claude plugin install mattpocock-skills@omega-engineering-x10
claude plugin install vibesec@omega-engineering-x10
# then add the specialists you need; see docs/INSTALL.md
python3 plugins/omega-core/scripts/omega.py doctor
```

In Claude Code, ask for `omega-core:omega-engineering-x10` (or just describe a task; the skill's
description triggers on multi-phase engineering work). It routes to the right specialist:

```bash
python3 plugins/omega-core/scripts/omega.py route "add a password reset flow with tests and check the page in a browser"
```

## Design

- **One plugin per source.** Plugins stay separately installable, keep their upstream layout (so
  `${CLAUDE_PLUGIN_ROOT}` paths, relative references and hooks keep working), and keep their own
  namespace, so overlapping skill names (`tdd`, `code-review`, `handoff`...) never collide.
- **Nothing silently dropped.** `tools/rules.py` assigns every one of the 10,090 tracked source
  files to a copy rule or a justified retain rule; the build fails on an unmatched file.
  `registry/components.json` gives each of 3,337 components (skills, agents, commands, hooks, rules,
  scripts, manifests, MCP configs, resource bundles) a disposition.
- **Overlaps kept, not flattened.** Overlapping workflows from different sources all stay loadable.
  `registry/routing-rules.json` sets a primary per phase, keeps the alternatives with "when to use"
  notes, and defines precedence (one owner per phase, security is additive, verification is mandatory).
- **Honest runtime handling.** Skills that need a CLI or service (agent-browser, graphify,
  claude-mem, npx) are flagged; `omega.py doctor` checks them and the router uses a fallback
  instead of pretending.

## Layout

```
.claude-plugin/marketplace.json   13 installable plugins
plugins/<plugin>/                 integrated plugins (upstream files + provenance)
plugins/omega-core/               master router skill, omega.py, registry copy
registry/                         components.json, skills.json, capabilities.json, routing-rules.json
audit/                            manifests, inventory, matrix, merge map, exclusions, reports
tools/                            build.py, rules.py, validate.py, run-baselines.sh, subreaper.py, render_reports.py,
                                  package_skill.py (router-only ZIP for the claude.ai Skills uploader)
scripts/                          fetch-sources.sh, install-ecc-rules.sh, install-plugin-deps.sh
tests/                            unittest suite
docs/INSTALL.md                   install, update, remove, troubleshooting
```

## Audit trail

| File | Contents |
|---|---|
| `audit/source-manifest.json` | repo, remote, branch, commit, date, tag, file count |
| `audit/source-inventory.md` | per-repo counts and every skill with disposition and target |
| `audit/source-licenses.md` | licenses and obligations |
| `audit/baseline-results.md` | upstream test suites run on a scratch copy |
| `audit/capability-matrix.csv` | every component, one row each |
| `audit/merge-map.json` | source path -> destination(s), overlap groups, transforms |
| `audit/file-map.json` | every tracked source file -> destination or reason |
| `audit/exclusions.md` | every non-copied item, grouped by justification |
| `audit/unresolved-items.md` | unresolved items (none) |
| `audit/reconciliation.md` | disposition counts per repo |
| `audit/security-report.md` | hooks, data flows, installers, secrets, dependency risk |
| `audit/validation-report.md` | commands run, results, limitations |

## Rebuild

```bash
scripts/fetch-sources.sh ../sources
python3 tools/build.py --sources ../sources
python3 tools/validate.py --syntax
python3 -m unittest discover -s tests
```

## Licenses

Each plugin keeps its upstream license (MIT or Apache-2.0) and NOTICE files. OMEGA's own code
(`omega-core`, `tools/`, `scripts/`, `tests/`) is MIT. See `audit/source-licenses.md`.
