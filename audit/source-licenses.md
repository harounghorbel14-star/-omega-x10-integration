# Source licenses and attribution

All ten sources use permissive licenses that allow redistribution with attribution. Each plugin directory keeps its upstream LICENSE (and NOTICE where present). No source was relicensed.

| Repository | License | Files carried | Plugin(s) |
|---|---|---|---|
| vercel-labs/agent-browser | Apache-2.0 | LICENSE; also bundles axe-core notices under cli/src/native/a11y (runtime only) | agent-browser |
| mattpocock/skills | MIT | LICENSE | mattpocock-skills, mattpocock-skills-extras |
| Jakeschincariol/replica-skill | MIT | LICENSE | replica-skill |
| affaan-m/ECC | MIT | LICENSE | ecc |
| vercel-labs/skills | MIT | LICENSE + ThirdPartyNoticeText.txt | find-skills |
| thedotmack/claude-mem | Apache-2.0 | LICENSE + NOTICE | anti-pattern-czar, claude-mem, claude-mem-cowork |
| BehiSecc/VibeSec-Skill | Apache-2.0 | LICENSE | vibesec |
| nextlevelbuilder/ui-ux-pro-max-skill | MIT | LICENSE; .claude/skills/ui-styling/LICENSE.txt and canvas-fonts carry their own (OFL) notices | ui-ux-pro-max, ui-ux-pro-max-design-stack |
| obra/superpowers | MIT | LICENSE | superpowers |
| Graphify-Labs/graphify | Apache-2.0 (LICENSE) with MIT also offered (LICENSE-MIT) | LICENSE, LICENSE-MIT, NOTICE | graphify |

## Obligations

- **Apache-2.0** (agent-browser, claude-mem, VibeSec, Graphify): LICENSE and NOTICE retained in each plugin; modified files are marked. The only modified file is `plugins/vibesec/skills/vibesec/SKILL.md` (frontmatter `name` changed; see `audit/transforms.json`).
- **MIT** (mattpocock, replica, ECC, vercel skills, UI UX Pro Max, superpowers): copyright notice and license text retained in each plugin.
- Third-party notices bundled by upstream (vercel skills ThirdPartyNoticeText.txt, ui-styling LICENSE.txt and canvas-fonts OFL files) are copied unchanged.
- Generated files (`plugin.json` for assembled plugins, `OMEGA-PROVENANCE.json`, omega-core) are new work under MIT and identify their upstream source and commit.
