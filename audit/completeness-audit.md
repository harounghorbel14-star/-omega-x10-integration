# Final completeness audit

Computed from `registry/components.json` (every component of every source) and the recorded test runs.

| Repository | Inspected | Commit | Skills found | Other components | Preserved | Merged | Adapted | Excluded | External runtime | Blocked/unresolved | Upstream tests |
|---|---|---|---|---|---|---|---|---|---|---|---|
| vercel-labs/agent-browser | inspected | `50c34e78c98d` | 10 | 34 | 11 | 1 | 0 | 20 | 12 | 0 | agent-browser-launcher=pass |
| mattpocock/skills | inspected | `5beb35b040e3` | 38 | 20 | 55 | 0 | 0 | 3 | 0 | 0 | mattpocock-validate=exit 1; mattpocock-version-check=pass |
| Jakeschincariol/replica-skill | inspected | `77c9436fb3d1` | 11 | 4 | 15 | 0 | 0 | 0 | 0 | 0 | replica-pytest=pass |
| affaan-m/ECC | inspected | `90606c8315ee` | 1062 | 1704 | 1159 | 338 | 0 | 1269 | 0 | 0 | ecc-npm-test=exit 1 |
| vercel-labs/skills | inspected | `a80e4c9d12d6` | 3 | 19 | 3 | 0 | 0 | 15 | 4 | 0 | vercel-skills-vitest=exit 1; vercel-skills-typecheck=pass |
| thedotmack/claude-mem | inspected | `dcb28a768c6b` | 41 | 220 | 93 | 2 | 1 | 144 | 21 | 0 | claude-mem-bun-test=exit 1 |
| BehiSecc/VibeSec-Skill | inspected | `0590993b35ad` | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | none upstream |
| nextlevelbuilder/ui-ux-pro-max-skill | inspected | `d14efff8ed1f` | 13 | 46 | 32 | 0 | 0 | 16 | 11 | 0 | uiux-validate-csv=pass; uiux-smoke-domains=pass; uiux-smoke-stacks=pass; uiux-pytest=pass |
| obra/superpowers | inspected | `2ce8aa15d05b` | 15 | 51 | 66 | 0 | 0 | 0 | 0 | 0 | superpowers-skill-size=pass; superpowers-hooks=pass; superpowers-skill-struct=pass; superpowers-find-polluter=pass; superpowers-version-bump=exit 3; superpowers-codex-manifest=pass; superpowers-shell-lint=pass |
| Graphify-Labs/graphify | inspected | `c588b72d9369` | 16 | 28 | 3 | 0 | 0 | 37 | 4 | 0 | graphify-pytest=exit 1 |
| **Total** | 10/10 | | 1210 | 2127 | 1438 | 341 | 2 | 1504 | 52 | 0 | |

Skills loadable in Claude Code: **584** (+9 agent-browser skills served by its CLI, +1 omega-core router). 386 come from the 11 source plugins in the OMEGA marketplace; 30 are claude-mem / claude-mem-cowork skills, loadable once claude-mem is installed from its upstream marketplace (identical files are kept in plugins/). The remaining skill files are harness mirrors, translations or per-platform variants, each mapped to its canonical loaded skill or excluded with a reason (`audit/exclusions.md`).

## Specific checks

| Check | Result | How verified |
|---|---|---|
| Missing nested skills | none | every `SKILL.md` (and graphify `skill*.md`) in `git ls-files` is a registry component (`tests/test_omega.py::test_every_source_skill_is_accounted_for`) |
| Unexamined directories | none | every tracked file matched a rule; build fails otherwise (`validate.py` classified) |
| Uncopied resources/data | only by recorded rule | `audit/file-map.json` gives each file a destination or reason |
| Lost unique behaviours | none found | unique mirror-only skills reviewed individually (ecc-council, ecc-conventions, project-guidelines-example x2, 3 claude-mem harness installers) |
| Broken paths | 0 introduced | `validate.py` references check, comparing against source |
| Silent truncation | none | byte-for-byte integrity of 3,828 files against a fresh fetch of the pinned commits |
| Unavailable integrations | recorded | claude-mem/cowork unlisted (name reservation); skills.sh blocked here; see validation-report section 8 |
| Incorrect install/execution claims | guarded | every claim in docs/INSTALL.md was run in the isolated config; unrun items are marked NOT RUN |
| Duplicate capabilities introduced | none | no skill was duplicated into a second plugin; overlaps across sources are upstream overlaps, listed in `audit/merge-map.json` overlap_groups with routing precedence |
| Dependencies made mandatory | none | each runtime is needed only by its plugin; plugins install independently; MCP servers of the design stack moved to optional/ |

