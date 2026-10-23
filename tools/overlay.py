"""Per-item analysis applied after component derivation.

1. Variant resolution: every skill that is not on a Claude Code load path is
   compared with the loaded skill of the same name from the same source.
   Identical or edited copies get a `variant_of` pointer; copies with no
   loaded counterpart are flagged `unique_variant` and handled individually in
   SPECIAL below, so no unique skill can hide inside a mirror directory.
2. Topic tagging and overlap groups across sources (used by routing and by
   audit/merge-map.json).
"""
import re
from collections import defaultdict
from pathlib import Path

# Individually reviewed items (source id -> override). Each records the decision and evidence.
SPECIAL = {
    "affaan-m/ECC:pi/core/skills/ecc-council/SKILL.md": {
        "disposition": "merged-with-traceability",
        "merged_into": "ecc:council",
        "note": "Pi-harness rename of skills/council. Body after frontmatter is byte-identical to skills/council/SKILL.md "
                "(verified with diff). Capability reachable as ecc:council.",
    },
    "affaan-m/ECC:.agents/skills/ecc-conventions/SKILL.md": {
        "disposition": "excluded-with-justification",
        "note": "Auto-generated conventions for contributing to the ECC repository itself (its commit style and "
                "file layout). Not applicable to other projects. Copied (inside plugins/ecc/.agents) but not loaded.",
    },
    "affaan-m/ECC:docs/ja-JP/skills/project-guidelines-example/SKILL.md": {
        "disposition": "merged-with-traceability",
        "merged_into": "plugins/ecc/docs/examples/project-guidelines-template.md",
        "note": "Japanese translation of the English template docs/examples/project-guidelines-template.md, which is "
                "integrated. It is an example to copy into a project, not a reusable skill.",
    },
    "affaan-m/ECC:docs/zh-TW/skills/project-guidelines-example/SKILL.md": {
        "disposition": "merged-with-traceability",
        "merged_into": "plugins/ecc/docs/examples/project-guidelines-template.md",
        "note": "Traditional Chinese translation of docs/examples/project-guidelines-template.md (integrated).",
    },
    "thedotmack/claude-mem:claude-mem-cursor/skills/install/SKILL.md": {
        "disposition": "excluded-with-justification",
        "note": "Installs claude-mem into Cursor (worker setup for Cursor hooks). Cursor-only; the Claude Code "
                "equivalent is the claude-mem plugin install documented in docs/INSTALL.md.",
    },
    "thedotmack/claude-mem:claude-mem-grok-bot/skills/install/SKILL.md": {
        "disposition": "excluded-with-justification",
        "note": "Installs claude-mem into Grok Bot (chat-log watcher, no host hooks). Grok-Bot-only.",
    },
    "thedotmack/claude-mem:claude-mem-grok-bot/skills/host-observer/SKILL.md": {
        "disposition": "excluded-with-justification",
        "note": "Lets Grok Bot itself act as the claude-mem observer model. In Claude Code the observer runs in the "
                "claude-mem worker (plugin/scripts/worker-service.cjs, integrated), so this role has no Claude Code use.",
    },
}

# Map a variant directory to (source repo, canonical loaded-dir prefix, reason)
VARIANT_HOMES = [
    ("affaan-m/ECC", r"^(\.agents|\.kiro|\.cursor|pi/core|docs/[^/]+)/skills/([^/]+)/SKILL\.md$", "skills/{n}/SKILL.md",
     "ECC harness/translation copy"),
    ("thedotmack/claude-mem", r"^(claude-mem-cursor|claude-mem-grok-bot|openclaw|cowork)/skills/([^/]+)/SKILL\.md$",
     "plugin/skills/{n}/SKILL.md", "claude-mem per-harness copy"),
    ("nextlevelbuilder/ui-ux-pro-max-skill", r"^(cli/assets|src)/(?:skills/)?([^/]+)/SKILL\.md$",
     ".claude/skills/{n}/SKILL.md", "UI UX Pro Max CLI template copy"),
    ("Graphify-Labs/graphify", r"^graphify/(skill)-([a-z]+)\.md$", "graphify/skill.md", "graphify per-harness skill"),
]

TOPICS = {
    "tdd-testing": r"\btdd\b|test-driven|\btesting\b|e2e|unit test|verification-loop|test-plan|replica-test",
    "code-review": r"code[- ]review|review(ing)? (a |the )?(pr|code|diff)|receiving-code-review|requesting-code-review",
    "debugging": r"debug|diagnos|root cause|bug hunt|troubleshoot",
    "planning": r"\bplan(s|ning)?\b|roadmap|to-spec|to-tickets|spec\b|wayfinder|blueprint",
    "requirements-discovery": r"grill|brainstorm|clarif|interview|questionnaire|requirements|wait-what",
    "session-memory-handoff": r"memory|handoff|session|context (preserv|persist)|continuous-learning|mem-search|timeline",
    "security": r"security|secure|vulnerab|owasp|xss|csrf|ssrf|injection|secret|vibesec|threat",
    "browser-automation": r"browser|playwright|screenshot|electron|dogfood|scrap|web automation",
    "ui-ux-design": r"\bui\b|\bux\b|design system|typograph|color palette|frontend|tailwind|banner|brand|slides|styling|accessib",
    "architecture-repo-analysis": r"architect|codebase|knowledge graph|graphify|repo(sitory)? (map|analysis)|codemap|smart-explore|learn-codebase|deep module|domain model",
    "git-workflow": r"\bgit\b|worktree|branch|pull request|\bpr\b|commit",
    "skill-authoring-discovery": r"skill(s)? (creat|author|writ|discover|find)|writing-skills|find-skills|skill-create|mode-creator",
    "agents-orchestration": r"subagent|parallel agents|dispatch|orchestrat|multi-agent|council",
    "app-replication": r"replica|clone (any|this|an) app|reverse[- ]engineer",
    "performance": r"performance|optimi[sz]|latency|profil|benchmark|web vitals",
    "deployment-release": r"deploy|release|ci/cd|launch|version-bump|docker",
    "documentation-writing": r"\bdocs?\b|documentation|article|writing|readme",
}


def tag_topics(c):
    hay = (c["item_name"] + " " + c.get("description", "")).lower()
    return sorted(t for t, p in TOPICS.items() if re.search(p, hay))


def apply(comps, src_root):
    by_id = {c["id"]: c for c in comps}
    loaded_by_src_path = {(c["source_repository"], c["source_path"]): c for c in comps
                          if c["item_type"] == "skill" and c.get("loaded_by_claude_code")}
    for c in comps:
        if c["item_type"] != "skill":
            continue
        c["topics"] = tag_topics(c)
        if c["id"] in SPECIAL:
            s = SPECIAL[c["id"]]
            c["disposition"] = s["disposition"]
            c["notes"].append(s["note"])
            if "merged_into" in s:
                c["merged_into"] = s["merged_into"]
            c["reviewed_individually"] = True
            continue
        if c.get("loaded_by_claude_code"):
            continue
        if c["source_repository"] == "vercel-labs/agent-browser" and c["source_path"].startswith("skill-data/"):
            c["notes"].append("Served at runtime by `agent-browser skills get " + c["source_path"].split("/")[1] +
                              "` (the upstream design: the installed CLI serves version-matched content). A copy of the "
                              "file is kept at the destination for offline reading and routing.")
            c["access"] = "agent-browser skills get " + c["source_path"].split("/")[1]
            c["reviewed_individually"] = True
            continue
        matched = False
        for repo, pat, canon_tpl, label in VARIANT_HOMES:
            if c["source_repository"] != repo:
                continue
            m = re.match(pat, c["source_path"])
            if not m:
                continue
            canon_path = canon_tpl.format(n=m.group(2))
            canon = loaded_by_src_path.get((repo, canon_path))
            if canon is None and repo == "Graphify-Labs/graphify":
                canon = loaded_by_src_path.get((repo, "graphify/skill.md"))
            if canon:
                same = "unknown"
                try:
                    a = (src_root / dir_of(repo) / c["source_path"]).read_bytes()
                    b = (src_root / dir_of(repo) / canon["source_path"]).read_bytes()
                    same = "identical" if a == b else "differs"
                except OSError:
                    pass
                c["variant_of"] = canon["invocation"]
                c["variant_relation"] = same
                c["notes"].append(f"{label}; canonical loaded skill is {canon['invocation']} ({same}).")
                if c["disposition"] == "preserved":
                    c["disposition"] = "merged-with-traceability"
                    c["merged_into"] = canon["invocation"]
                matched = True
            else:
                c["unique_variant"] = True
                c["notes"].append(f"{label} with NO loaded counterpart: needs individual review.")
                matched = True
            break
        if not matched and c["disposition"] == "preserved":
            c["unique_variant"] = True
            c["notes"].append("Copied but not loaded and no variant rule matched: needs individual review.")
    map_ecc_commands_and_agents(comps, src_root)
    for c in comps:
        if c["id"] == "mattpocock/skills:docs/agents/triage-labels.md":
            c["item_type"] = "reference"
            c["reviewed_individually"] = True
            c["notes"].append("Not an agent definition despite its docs/agents/ path: the label mapping that the triage "
                              "skill reads for the mattpocock/skills tracker. Copied unchanged.")
    # overlap groups across sources (loaded skills only)
    groups = defaultdict(list)
    for c in comps:
        if c["item_type"] == "skill" and c.get("loaded_by_claude_code"):
            for t in c["topics"]:
                groups[t].append(c["invocation"])
    return groups


def dir_of(slug):
    from rules import REPOS
    for d, m in REPOS.items():
        if m["slug"] == slug:
            return d
    raise KeyError(slug)


# ECC legacy slash-command shims point at the maintained skill (read from each shim's text).
ECC_SHIM_TARGET = {
    "agent-sort": "ecc:agent-sort", "claw": "ecc:nanoclaw-repl", "context-budget": "ecc:context-budget",
    "devfleet": "ecc:claude-devfleet", "docs": "ecc:documentation-lookup", "e2e": "ecc:e2e-testing",
    "eval": "ecc:eval-harness", "orchestrate": "ecc:dmux-workflows", "prompt-optimize": "ecc:prompt-optimizer",
    "rules-distill": "ecc:rules-distill", "tdd": "ecc:tdd-workflow", "verify": "ecc:verification-loop",
    # OpenCode-only command: "Run comprehensive security review", agent: security-reviewer
    "security": "ecc:security-review (and agent ecc:security-reviewer)",
}


def map_ecc_commands_and_agents(comps, src_root):
    """Every ECC command/agent copy that Claude Code does not load gets a pointer to its loaded equivalent."""
    ecc = src_root / dir_of("affaan-m/ECC")
    for c in comps:
        if c["source_repository"] != "affaan-m/ECC" or c["item_type"] not in ("command", "agent"):
            continue
        p = c["source_path"]
        if c["item_type"] == "command" and p.startswith("commands/"):
            c["loaded_by_claude_code"] = True
            c["invocation"] = "ecc:/" + p.split("/")[-1][:-3]
            continue
        if c["item_type"] == "agent" and p.startswith("agents/"):
            c["loaded_by_claude_code"] = True
            c["invocation"] = "ecc agent " + p.split("/")[-1][:-3]
            continue
        n = p.split("/")[-1][:-3]
        if p.startswith(".claude/commands/"):
            general = {"add-language-rules": "scripts/install-ecc-rules.sh / ecc rules/ README",
                       "database-migration": "ecc:database-migrations", "feature-development": "ecc:orch-add-feature"}[n]
            c["disposition"] = "excluded-with-justification"
            c["reviewed_individually"] = True
            c["notes"].append(f"Project-local workflow scaffold for contributing to the ECC repository itself (\"Use this workflow "
                              f"when working on {n} in ECC\"). Copied into plugins/ecc/.claude/commands but not loaded; the "
                              f"general-purpose capability is {general}.")
            continue
        kind = "commands" if c["item_type"] == "command" else "agents"
        if (ecc / kind / f"{n}.md").exists():
            target = ("ecc:/" if kind == "commands" else "ecc agent ") + n
        elif kind == "commands" and n in ECC_SHIM_TARGET:
            target = ECC_SHIM_TARGET[n]
        elif kind == "agents" and n == "observer":
            target = "ecc:continuous-learning-v2 (skills/continuous-learning-v2/agents/observer.md)"
        elif n == "README":
            c["notes"].append("Index page of a translated commands directory, not a command.")
            continue
        else:
            c["unique_variant"] = True
            c["notes"].append("ECC command/agent copy with no canonical equivalent: needs individual review.")
            continue
        c["variant_of"] = target
        c["notes"].append(f"Not loaded by Claude Code (harness copy, translation or legacy shim); capability is {target}.")
        if c["disposition"] == "preserved":
            c["disposition"] = "merged-with-traceability"
            c["merged_into"] = target
