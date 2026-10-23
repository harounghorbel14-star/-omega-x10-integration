"""Integration rules for OMEGA-ENGINEERING X10.

Every tracked file in every source repository must match exactly one rule:

* a COPY rule: the file is copied into a plugin under ``plugins/`` (its
  destination is recorded in the merge map), or
* a RETAIN rule: the file is not copied into a plugin. It stays in the
  pinned source snapshot (``sources/<repo>`` at the recorded commit) and the
  rule carries the justification and, where relevant, the install command
  that delivers it at runtime.

Rules are evaluated in order; the first matching prefix wins. A file that
matches no rule is reported as ``unclassified`` and fails validation, so a
new upstream directory can never be dropped silently.
"""

# Short ids used in plugin names and reports.
REPOS = {
    "vercel-labs__agent-browser": {
        "slug": "vercel-labs/agent-browser",
        "short": "agent-browser",
        "role": "Browser automation CLI and skills",
    },
    "mattpocock__skills": {
        "slug": "mattpocock/skills",
        "short": "mattpocock",
        "role": "Grill Me and Matt Pocock's engineering skills",
    },
    "Jakeschincariol__replica-skill": {
        "slug": "Jakeschincariol/replica-skill",
        "short": "replica",
        "role": "App clean-room replication pipeline",
    },
    "affaan-m__ECC": {
        "slug": "affaan-m/ECC",
        "short": "ecc",
        "role": "Everything Claude Code: skills, agents, commands, hooks, rules",
    },
    "vercel-labs__skills": {
        "slug": "vercel-labs/skills",
        "short": "find-skills",
        "role": "Skills CLI and find-skills discovery skill",
    },
    "thedotmack__claude-mem": {
        "slug": "thedotmack/claude-mem",
        "short": "claude-mem",
        "role": "Persistent memory plugin (hooks, worker, MCP)",
    },
    "BehiSecc__VibeSec-Skill": {
        "slug": "BehiSecc/VibeSec-Skill",
        "short": "vibesec",
        "role": "Secure coding guide for web applications",
    },
    "nextlevelbuilder__ui-ux-pro-max-skill": {
        "slug": "nextlevelbuilder/ui-ux-pro-max-skill",
        "short": "ui-ux-pro-max",
        "role": "UI/UX design intelligence and design data",
    },
    "obra__superpowers": {
        "slug": "obra/superpowers",
        "short": "superpowers",
        "role": "Structured development workflow skills",
    },
    "Graphify-Labs__graphify": {
        "slug": "Graphify-Labs/graphify",
        "short": "graphify",
        "role": "Knowledge-graph builder for code and documents",
    },
}

# Reason strings reused by several rules.
SNAPSHOT = "Retained unmodified in the pinned source snapshot (sources/<repo>@<commit>)."
OTHER_HARNESS = (
    "Integration for a non-Claude-Code harness (Codex, Cursor, Kiro, OpenCode, Gemini, "
    "Pi, etc.). The Claude Code equivalent is integrated; this variant is not loadable "
    "by Claude Code. " + SNAPSHOT
)
REPO_DEV = "Upstream repository development/CI tooling, not an end-user capability. " + SNAPSHOT
LOCALIZED = (
    "Localized translation of English content that is integrated. Translations are not "
    "separate capabilities. " + SNAPSHOT
)
MEDIA = "Marketing/documentation media (images, demos, site content), not a capability. " + SNAPSHOT

# Each rule: (repo, path_prefix, kind, plugin_or_None, dest_prefix_or_reason, extra)
#   kind = "copy"    -> plugin, dest prefix (path under plugin root that replaces path_prefix)
#   kind = "adapt"   -> like copy but the file content is transformed (see TRANSFORMS)
#   kind = "retain"  -> disposition, reason
# path_prefix "" matches everything (used as a final catch-all per repo only when
# the catch-all is itself justified).
RULES = [
    # ---------------------------------------------------------------- agent-browser
    ("vercel-labs__agent-browser", "skills/agent-browser/", "copy", "agent-browser", "skills/agent-browser/"),
    ("vercel-labs__agent-browser", "skill-data/", "copy", "agent-browser", "skill-data/"),
    ("vercel-labs__agent-browser", "LICENSE", "copy", "agent-browser", "LICENSE"),
    ("vercel-labs__agent-browser", "README.md", "copy", "agent-browser", "UPSTREAM-README.md"),
    ("vercel-labs__agent-browser", ".claude-plugin/marketplace.json", "retain", "merged-with-traceability",
     "Upstream marketplace entry; its plugin definition (skills/agent-browser, strict:false) is reproduced in "
     "plugins/agent-browser/.claude-plugin/plugin.json and the OMEGA marketplace."),
    ("vercel-labs__agent-browser", "cli/", "retain", "retained-as-external-runtime",
     "Rust source of the agent-browser CLI. Delivered at runtime by `npm i -g agent-browser@0.39.2 && agent-browser install`. " + SNAPSHOT),
    ("vercel-labs__agent-browser", "bin/", "retain", "retained-as-external-runtime",
     "npm launcher for the CLI, delivered by the agent-browser npm package. " + SNAPSHOT),
    ("vercel-labs__agent-browser", "packages/", "retain", "retained-as-external-runtime",
     "Observability dashboard package served by the CLI (`agent-browser dashboard`). " + SNAPSHOT),
    ("vercel-labs__agent-browser", "scripts/", "retain", "retained-as-external-runtime",
     "Build/postinstall scripts of the npm package. " + SNAPSHOT),
    ("vercel-labs__agent-browser", "docs/", "retain", "excluded-with-justification",
     "Website documentation (Next.js docs site). Usage content is served by `agent-browser skills get core --full` and preserved in skill-data/. " + SNAPSHOT),
    ("vercel-labs__agent-browser", "examples/", "retain", "excluded-with-justification",
     "Example apps that embed agent-browser (SDK usage demos), not agent skills. " + SNAPSHOT),
    ("vercel-labs__agent-browser", "benchmarks/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "evals/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "test/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "docker/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "patches/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", ".github/", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "agent-browser.schema.json", "copy", "agent-browser", "reference/agent-browser.schema.json"),
    ("vercel-labs__agent-browser", "CHANGELOG.md", "copy", "agent-browser", "reference/CHANGELOG.md"),
    ("vercel-labs__agent-browser", "AGENTS.md", "retain", "excluded-with-justification", REPO_DEV),
    ("vercel-labs__agent-browser", "", "retain", "excluded-with-justification",
     "Root build/config files of the npm package (package.json, lockfiles, workspace config). " + REPO_DEV),

    # ---------------------------------------------------------------- mattpocock
    ("mattpocock__skills", "skills/in-progress/", "copy", "mattpocock-skills-extras", "skills/in-progress/"),
    ("mattpocock__skills", "skills/misc/", "copy", "mattpocock-skills-extras", "skills/misc/"),
    ("mattpocock__skills", ".github/", "retain", "excluded-with-justification", REPO_DEV),
    ("mattpocock__skills", ".changeset/", "retain", "excluded-with-justification", REPO_DEV),
    ("mattpocock__skills", "", "copy", "mattpocock-skills", ""),

    # ---------------------------------------------------------------- replica
    ("Jakeschincariol__replica-skill", "", "copy", "replica-skill", ""),

    # ---------------------------------------------------------------- ECC
    ("affaan-m__ECC", "assets/", "retain", "excluded-with-justification", MEDIA),
] + [
    ("affaan-m__ECC", f"docs/{loc}/", "retain", "excluded-with-justification",
     f"Localized translation ({loc}) of ECC skills/agents/commands/docs. The English originals are integrated; "
     "unique items found only in a translation are listed individually in audit/exclusions.md. " + SNAPSHOT)
    for loc in ("ja-JP", "zh-CN", "zh-TW", "ko-KR", "es", "tr", "pt-BR", "pl", "de-DE", "ar", "vi-VN", "ur",
                "uk-UA", "th", "ru", "bn")
] + [
    ("affaan-m__ECC", "tests/", "retain", "excluded-with-justification",
     "ECC's own test suite. Executed against the source snapshot in audit/baseline-results.md. " + SNAPSHOT),
    ("affaan-m__ECC", ".git", "retain", "excluded-with-justification", REPO_DEV),
    ("affaan-m__ECC", "", "copy", "ecc", ""),

    # ---------------------------------------------------------------- vercel skills
    ("vercel-labs__skills", "skills/find-skills/", "copy", "find-skills", "skills/find-skills/"),
    ("vercel-labs__skills", "LICENSE", "copy", "find-skills", "LICENSE"),
    ("vercel-labs__skills", "ThirdPartyNoticeText.txt", "copy", "find-skills", "ThirdPartyNoticeText.txt"),
    ("vercel-labs__skills", "README.md", "copy", "find-skills", "UPSTREAM-README.md"),
    ("vercel-labs__skills", "docs/", "copy", "find-skills", "reference/docs/"),
    ("vercel-labs__skills", ".vc/", "retain", "excluded-with-justification",
     "Vercel-internal automation workflows (triage, pr-labeling) that act on the vercel-labs/skills GitHub repository "
     "itself. They are bound to that repository's labels and bots. " + SNAPSHOT),
    ("vercel-labs__skills", "src/", "retain", "retained-as-external-runtime",
     "TypeScript source of the `skills` CLI used by find-skills. Delivered by `npx skills@1.7.4`. " + SNAPSHOT),
    ("vercel-labs__skills", "bin/", "retain", "retained-as-external-runtime", "CLI launcher delivered by `npx skills`. " + SNAPSHOT),
    ("vercel-labs__skills", "tests/", "retain", "excluded-with-justification",
     "CLI test suite, executed in the baseline. " + SNAPSHOT),
    ("vercel-labs__skills", "", "retain", "excluded-with-justification",
     "CLI build/CI/config files. " + REPO_DEV),

    # ---------------------------------------------------------------- claude-mem
    ("thedotmack__claude-mem", "plugin/", "copy", "claude-mem", ""),
    ("thedotmack__claude-mem", "cowork/", "copy", "claude-mem-cowork", ""),
    ("thedotmack__claude-mem", "LICENSE", "copy", "claude-mem", "LICENSE"),
    ("thedotmack__claude-mem", "NOTICE", "copy", "claude-mem", "NOTICE"),
    ("thedotmack__claude-mem", "README.md", "copy", "claude-mem", "UPSTREAM-README.md"),
    ("thedotmack__claude-mem", ".claude-plugin/marketplace.json", "retain", "merged-with-traceability",
     "Upstream marketplace (claude-mem ./plugin, claude-mem-cowork ./cowork) reproduced in the OMEGA marketplace."),
    ("thedotmack__claude-mem", ".claude-plugin/plugin.json", "retain", "merged-with-traceability",
     "Root-level duplicate of plugin/.claude-plugin/plugin.json, which is integrated."),
    ("thedotmack__claude-mem", "src/", "retain", "retained-as-external-runtime",
     "TypeScript source compiled into plugin/scripts/*.cjs (integrated) and the `claude-mem` npx CLI. " + SNAPSHOT),
    ("thedotmack__claude-mem", "claude-mem-cursor/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "cursor-hooks/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "claude-mem-grok-bot/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "openclaw/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "hermes/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "omp/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "pi/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "dsh/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", ".codex-plugin/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", ".qoder-plugin/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", ".agents/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("thedotmack__claude-mem", "workers/", "retain", "retained-as-external-runtime",
     "Cloud worker code for the hosted cmem.ai service, not run locally. " + SNAPSHOT),
    ("thedotmack__claude-mem", "services/", "retain", "retained-as-external-runtime",
     "Hosted service code, not run locally. " + SNAPSHOT),
    ("thedotmack__claude-mem", "ragtime/", "retain", "excluded-with-justification",
     "Standalone experimental RAG tool in the repo, not part of the Claude Code plugin. " + SNAPSHOT),
    ("thedotmack__claude-mem", "plans/", "retain", "excluded-with-justification",
     "Upstream planning documents and recorded artifacts (124 MB). " + REPO_DEV),
    ("thedotmack__claude-mem", "docs/", "retain", "excluded-with-justification",
     "Documentation site (docs.claude-mem.ai). " + SNAPSHOT),
    ("thedotmack__claude-mem", ".claude/commands/anti-pattern-czar.md", "adapt", "anti-pattern-czar",
     "commands/anti-pattern-czar.md"),
    ("thedotmack__claude-mem", "scripts/anti-pattern-test/", "copy", "anti-pattern-czar", "scripts/anti-pattern-test/"),
    ("thedotmack__claude-mem", "scripts/export-memories.ts", "retain", "retained-as-external-runtime",
     "User-facing memory export (hybrid search -> portable JSON) documented in docs/public/usage/export-import.mdx. It "
     "imports ../src, so upstream runs it from a repository checkout: `cd sources/thedotmack__claude-mem && bun "
     "scripts/export-memories.ts <query> <out.json>`. See docs/INSTALL.md (memory retention). " + SNAPSHOT),
    ("thedotmack__claude-mem", "scripts/import-memories.ts", "retain", "retained-as-external-runtime",
     "User-facing memory import with duplicate prevention (pairs with export-memories.ts); run from a repository "
     "checkout. " + SNAPSHOT),
    ("thedotmack__claude-mem", "", "retain", "excluded-with-justification",
     "Build, CI, test, eval, docker and dev config files. " + REPO_DEV),

    # ---------------------------------------------------------------- VibeSec
    ("BehiSecc__VibeSec-Skill", "SKILL.md", "adapt", "vibesec", "skills/vibesec/SKILL.md"),
    ("BehiSecc__VibeSec-Skill", "README.md", "copy", "vibesec", "skills/vibesec/README.md"),
    ("BehiSecc__VibeSec-Skill", "LICENSE", "copy", "vibesec", "LICENSE"),

    # ---------------------------------------------------------------- UI UX Pro Max
    ("nextlevelbuilder__ui-ux-pro-max-skill", ".claude/skills/", "copy", "ui-ux-pro-max", ".claude/skills/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", ".claude-plugin/", "copy", "ui-ux-pro-max", ".claude-plugin/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "LICENSE", "copy", "ui-ux-pro-max", "LICENSE"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "README.md", "copy", "ui-ux-pro-max", "README.md"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "skill.json", "copy", "ui-ux-pro-max", "skill.json"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "CLAUDE.md", "copy", "ui-ux-pro-max", "UPSTREAM-CLAUDE.md"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "stack/.claude/agents/", "copy", "ui-ux-pro-max-design-stack", "agents/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "stack/.claude/commands/", "copy", "ui-ux-pro-max-design-stack", "commands/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "stack/.mcp.json", "copy", "ui-ux-pro-max-design-stack", "optional/mcp.json"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "stack/", "copy", "ui-ux-pro-max-design-stack", "stack-template/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "src/ui-ux-pro-max/", "copy", "ui-ux-pro-max", "src/ui-ux-pro-max/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "cli/", "retain", "retained-as-external-runtime",
     "Source of `ui-ux-pro-max-cli` (npm), which installs the same skill bundle for 19 other harnesses. "
     "Its assets duplicate .claude/skills (integrated). Delivered by `npx ui-ux-pro-max-cli init --ai claude`. " + SNAPSHOT),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "gallery/", "retain", "excluded-with-justification", MEDIA),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "preview/", "retain", "excluded-with-justification", MEDIA),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "screenshots/", "retain", "excluded-with-justification", MEDIA),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "projects/", "retain", "excluded-with-justification", MEDIA),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "docs/", "retain", "excluded-with-justification", "Release journals. " + REPO_DEV),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "scripts/", "copy", "ui-ux-pro-max", "repo-scripts/"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "", "retain", "excluded-with-justification",
     "Localized READMEs and repo meta files (CONTRIBUTING, CODE_OF_CONDUCT, workflows). " + REPO_DEV),

    # ---------------------------------------------------------------- superpowers
    ("obra__superpowers", "", "copy", "superpowers", ""),

    # ---------------------------------------------------------------- graphify
    ("Graphify-Labs__graphify", "graphify/skill.md", "copy", "graphify", "skills/graphify/SKILL.md"),
    ("Graphify-Labs__graphify", "graphify/skills/claude/", "copy", "graphify", "skills/graphify/"),
    ("Graphify-Labs__graphify", "graphify/always_on/claude-md.md", "copy", "graphify", "always_on/claude-md.md"),
    ("Graphify-Labs__graphify", "graphify/skill-", "retain", "excluded-with-justification",
     "Per-harness variants of graphify/skill.md generated by tools/skillgen; the upstream installer uses skill.md for Claude Code. " + OTHER_HARNESS),
    ("Graphify-Labs__graphify", "graphify/skills/", "retain", "excluded-with-justification",
     "Per-harness references/ bundles; the Claude bundle (graphify/skills/claude) is integrated. " + OTHER_HARNESS),
    ("Graphify-Labs__graphify", "graphify/always_on/", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("Graphify-Labs__graphify", "graphify/command-kilo.md", "retain", "excluded-with-justification", OTHER_HARNESS),
    ("Graphify-Labs__graphify", "graphify/", "retain", "retained-as-external-runtime",
     "Python package `graphifyy` (extractors, clustering, exporters, MCP server, hooks). Delivered by "
     "`uv tool install graphifyy==0.9.94`; the skill invokes it. " + SNAPSHOT),
    ("Graphify-Labs__graphify", "tools/", "retain", "excluded-with-justification",
     "skillgen: regenerates per-harness skill files. " + REPO_DEV),
    ("Graphify-Labs__graphify", "tests/", "retain", "excluded-with-justification", "Package test suite, run in baseline. " + SNAPSHOT),
    ("Graphify-Labs__graphify", "worked/", "retain", "excluded-with-justification",
     "Worked example corpora and generated graphs used for docs/benchmarks. " + SNAPSHOT),
    ("Graphify-Labs__graphify", "docs/", "retain", "excluded-with-justification", "Translations and media. " + SNAPSHOT),
    ("Graphify-Labs__graphify", "LICENSE", "copy", "graphify", "LICENSE"),
    ("Graphify-Labs__graphify", "LICENSE-MIT", "copy", "graphify", "LICENSE-MIT"),
    ("Graphify-Labs__graphify", "NOTICE", "copy", "graphify", "NOTICE"),
    ("Graphify-Labs__graphify", "README.md", "copy", "graphify", "UPSTREAM-README.md"),
    ("Graphify-Labs__graphify", "ARCHITECTURE.md", "copy", "graphify", "reference/ARCHITECTURE.md"),
    ("Graphify-Labs__graphify", "SECURITY.md", "copy", "graphify", "reference/SECURITY.md"),
    ("Graphify-Labs__graphify", "", "retain", "excluded-with-justification",
     "Package build/release/meta files (pyproject, uv.lock, Dockerfile, CHANGELOG, CONTRIBUTING). " + REPO_DEV),
]

# Files transformed on copy. Each transform documents why.
TRANSFORMS = {
    ("thedotmack__claude-mem", ".claude/commands/anti-pattern-czar.md"): {
        "why": "Upstream runs the detector from the claude-mem repo root (`bun run scripts/anti-pattern-test/...`). Relocated "
               "into its own plugin, the script path now uses ${CLAUDE_PLUGIN_ROOT}; it still scans ./src of the current "
               "project as upstream does. A frontmatter description was added (upstream has none, so the command had no "
               "description in Claude Code's command list). No other change.",
        "replace": [("# Anti-Pattern Czar\n", "---\ndescription: Find and fix TypeScript error-handling anti-patterns "
                     "(empty or silent catch blocks, swallowed promise errors) under ./src, one finding at a time. "
                     "Requires Bun.\n---\n\n# Anti-Pattern Czar\n"),
                    ("bun run scripts/anti-pattern-test/detect-error-handling-antipatterns.ts",
                     'bun run "${CLAUDE_PLUGIN_ROOT}/scripts/anti-pattern-test/detect-error-handling-antipatterns.ts"')],
    },
    ("BehiSecc__VibeSec-Skill", "SKILL.md"): {
        "why": "Frontmatter name `VibeSec-Skill` contains uppercase letters, which the Agent Skills name "
               "rule (lowercase, digits, hyphens; must match the directory) rejects. Renamed to `vibesec`. "
               "Body unchanged.",
        "replace": [("name: VibeSec-Skill\n", "name: vibesec\n")],
    },
}

# Additional copies of a source file into a second plugin (licenses/notices that several plugins
# assembled from one repository must each carry). Recorded in audit/file-map.json with "extra": true.
EXTRA_COPIES = [
    ("mattpocock__skills", "LICENSE", "mattpocock-skills-extras", "LICENSE"),
    ("nextlevelbuilder__ui-ux-pro-max-skill", "LICENSE", "ui-ux-pro-max-design-stack", "LICENSE"),
    ("thedotmack__claude-mem", "LICENSE", "claude-mem-cowork", "LICENSE"),
    ("thedotmack__claude-mem", "NOTICE", "claude-mem-cowork", "NOTICE"),
    ("thedotmack__claude-mem", "LICENSE", "anti-pattern-czar", "LICENSE"),
    ("thedotmack__claude-mem", "NOTICE", "anti-pattern-czar", "NOTICE"),
]
