"""Plugin and marketplace manifests for OMEGA-ENGINEERING X10.

Plugins copied with their upstream .claude-plugin/plugin.json keep it
unchanged. Plugins assembled from parts of a repository get a generated
manifest here; each one records the upstream source and commit.
"""
import json
from pathlib import Path

MARKETPLACE_NAME = "omega-engineering-x10"

# Plugins kept in plugins/ for audit and offline reference but NOT listed in the OMEGA marketplace.
# claude-mem: Claude Code's validator reserves names starting with "claude-" for Anthropic, so a third-party
# marketplace cannot list it (the upstream repo fails the same check). Its runtime (worker, launcher, PATH
# setup) also expects its own marketplace id. Install it from upstream instead; see docs/INSTALL.md.
UNLISTED = {
    "claude-mem": "Install from upstream: /plugin marketplace add thedotmack/claude-mem ; /plugin install claude-mem@thedotmack",
    "claude-mem-cowork": "Install from upstream marketplace thedotmack (plugin claude-mem-cowork); sends data to cmem.ai.",
}

# name -> (source repo dir, description, category, extra manifest fields, upstream version)
PLUGIN_INFO = {
    "omega-core": ("(omega)", "OMEGA-ENGINEERING X10 master router: maps any engineering task to the right "
                   "specialist skill across all ten integrated sources, with a searchable registry and doctor checks.",
                   "engineering", None, None),
    "agent-browser": ("vercel-labs__agent-browser", "Vercel agent-browser: browser automation CLI skill "
                      "(navigate, snapshot, click, fill, screenshot, sessions, Electron, Slack, dogfood QA). "
                      "Requires the agent-browser CLI.", "development",
                      {"skills": ["./skills/agent-browser"]}, "0.39.2"),
    "mattpocock-skills": ("mattpocock__skills", None, "engineering", None, None),
    "mattpocock-skills-extras": ("mattpocock__skills", "Matt Pocock's non-promoted skills: misc/ (rarely used) and "
                                 "in-progress/ (beta, feedback wanted). Upstream ships these outside its plugin.",
                                 "engineering", "AUTO_SKILLS", "1.3.1"),
    "replica-skill": ("Jakeschincariol__replica-skill", None, "product", None, None),
    "ecc": ("affaan-m__ECC", None, "engineering", None, None),
    "find-skills": ("vercel-labs__skills", "Vercel find-skills: discover and install skills from the open agent "
                    "skills ecosystem via the `npx skills` CLI.", "productivity",
                    {"skills": ["./skills/find-skills"]}, "1.7.4"),
    "claude-mem": ("thedotmack__claude-mem", None, "productivity", None, None),
    "anti-pattern-czar": ("thedotmack__claude-mem", "Anti-Pattern Czar (from claude-mem's own dev tooling): /anti-pattern-czar "
                          "runs a TypeScript error-handling anti-pattern detector over ./src and walks you through fixing "
                          "each finding. Needs Bun.", "engineering", {}, "15.0.1"),
    "claude-mem-cowork": ("thedotmack__claude-mem", None, "productivity", None, None),
    "vibesec": ("BehiSecc__VibeSec-Skill", "VibeSec: secure coding guide for web applications from a bug hunter's "
                "perspective (access control, XSS, CSRF, SSRF, uploads, SQLi, XXE, path traversal, JWT, API, headers).",
                "security", {"skills": ["./skills/vibesec"]}, "0.0.0+0590993"),
    "ui-ux-pro-max": ("nextlevelbuilder__ui-ux-pro-max-skill", None, "design", None, None),
    "ui-ux-pro-max-design-stack": ("nextlevelbuilder__ui-ux-pro-max-skill",
                                   "UI UX Pro Max 'Claude Website Design Stack': design-review subagent plus "
                                   "/design-plan and /design-review commands. Optional MCP servers in optional/mcp.json.",
                                   "design", {}, "2.15.0"),
    "superpowers": ("obra__superpowers", None, "engineering", None, None),
    "graphify": ("Graphify-Labs__graphify", "Graphify: turn code, docs, papers, images or video into a queryable "
                 "knowledge graph (/graphify, query, path, explain, MCP, exports). Requires `uv tool install graphifyy`.",
                 "development", {"skills": ["./skills/graphify"]}, "0.9.94"),
}

AUTHORS = {
    "vercel-labs__agent-browser": {"name": "Vercel", "url": "https://github.com/vercel-labs/agent-browser"},
    "mattpocock__skills": {"name": "Matt Pocock", "url": "https://www.aihero.dev"},
    "vercel-labs__skills": {"name": "Vercel", "url": "https://github.com/vercel-labs/skills"},
    "BehiSecc__VibeSec-Skill": {"name": "BehiSecc", "url": "https://github.com/BehiSecc/VibeSec-Skill"},
    "nextlevelbuilder__ui-ux-pro-max-skill": {"name": "nextlevelbuilder"},
    "Graphify-Labs__graphify": {"name": "Safi Shamsi and the Graphify contributors", "url": "https://graphify.com"},
    "thedotmack__claude-mem": {"name": "Alex Newman", "url": "https://github.com/thedotmack/claude-mem"},
}
LICENSES = {
    "vercel-labs__agent-browser": "Apache-2.0", "mattpocock__skills": "MIT", "vercel-labs__skills": "MIT",
    "BehiSecc__VibeSec-Skill": "Apache-2.0", "nextlevelbuilder__ui-ux-pro-max-skill": "MIT",
    "thedotmack__claude-mem": "Apache-2.0",
    "Graphify-Labs__graphify": "Apache-2.0",
}


def write_generated_manifests(root: Path, source_manifest):
    commits = {m["dir"]: m for m in source_manifest}
    plugins_dir = root / "plugins"
    entries = []
    for name, (repo, desc, category, extra, version) in PLUGIN_INFO.items():
        pdir = plugins_dir / name
        mpath = pdir / ".claude-plugin" / "plugin.json"
        if extra is not None and name != "omega-core":
            m = commits[repo]
            data = {
                "name": name,
                "version": version,
                "description": desc,
                "author": AUTHORS.get(repo, {"name": repo}),
                "homepage": m["remote"].removesuffix(".git"),
                "repository": m["remote"].removesuffix(".git"),
                "license": LICENSES.get(repo, "MIT"),
                "keywords": ["omega-engineering-x10", REPOS_SHORT(repo)],
            }
            if extra == "AUTO_SKILLS":
                skills = sorted("./" + str(p.parent.relative_to(pdir)) for p in pdir.glob("skills/*/*/SKILL.md"))
                data["skills"] = skills
            else:
                data.update(extra)
            mpath.parent.mkdir(parents=True, exist_ok=True)
            mpath.write_text(json.dumps(data, indent=2) + "\n")
            (pdir / "OMEGA-PROVENANCE.json").write_text(json.dumps({
                "generated_manifest": True, "source_repository": m["remote"], "source_commit": m["commit"],
                "note": "plugin.json generated by OMEGA-ENGINEERING X10 tools/manifests.py; all other files are "
                        "copied from the source commit (see audit/merge-map.json)."}, indent=2) + "\n")
        elif name != "omega-core":
            m = commits[repo]
            (pdir / "OMEGA-PROVENANCE.json").write_text(json.dumps({
                "generated_manifest": False, "source_repository": m["remote"], "source_commit": m["commit"],
                "note": "Upstream .claude-plugin/plugin.json kept unchanged."}, indent=2) + "\n")
        if not mpath.exists():
            raise SystemExit(f"plugin {name} has no manifest at {mpath}")
        pdata = json.loads(mpath.read_text())
        if name in UNLISTED:
            continue
        entries.append({
            "name": pdata["name"],
            "source": f"./plugins/{name}",
            "description": desc or pdata.get("description", ""),
            "version": pdata.get("version"),
            "category": category,
            "strict": True,
        })
    market = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": MARKETPLACE_NAME,
        "owner": {"name": "OMEGA-ENGINEERING X10 integrators"},
        "metadata": {
            "description": "OMEGA-ENGINEERING X10: ten engineering skill sources integrated as separately "
                           "installable plugins with one master router (omega-core).",
            "version": "1.0.0",
        },
        "plugins": entries,
    }
    (root / ".claude-plugin").mkdir(exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(market, indent=2) + "\n")


def REPOS_SHORT(repo):
    from rules import REPOS
    return REPOS[repo]["short"]
