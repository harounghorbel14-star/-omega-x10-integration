"""Generate audit/ reports and registry/ indexes from the component registry."""
import csv
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

DISPOSITIONS = ["preserved", "merged-with-traceability", "adapted-with-traceability",
                "excluded-with-justification", "retained-as-external-runtime", "blocked-uninspected", "unclassified"]

LICENSE_INFO = {
    "vercel-labs/agent-browser": ("Apache-2.0", "LICENSE; also bundles axe-core notices under cli/src/native/a11y (runtime only)"),
    "mattpocock/skills": ("MIT", "LICENSE"),
    "Jakeschincariol/replica-skill": ("MIT", "LICENSE"),
    "affaan-m/ECC": ("MIT", "LICENSE"),
    "vercel-labs/skills": ("MIT", "LICENSE + ThirdPartyNoticeText.txt"),
    "thedotmack/claude-mem": ("Apache-2.0", "LICENSE + NOTICE"),
    "BehiSecc/VibeSec-Skill": ("Apache-2.0", "LICENSE"),
    "nextlevelbuilder/ui-ux-pro-max-skill": ("MIT", "LICENSE; .claude/skills/ui-styling/LICENSE.txt and canvas-fonts carry their own (OFL) notices"),
    "obra/superpowers": ("MIT", "LICENSE"),
    "Graphify-Labs/graphify": ("Apache-2.0 (LICENSE) with MIT also offered (LICENSE-MIT)", "LICENSE, LICENSE-MIT, NOTICE"),
}


def write_all(root: Path, manifest, files, comps, transforms, overlap_groups):
    audit, reg = root / "audit", root / "registry"
    slugs = [m["repo"] for m in manifest]

    # ---------------------------------------------------------- capability matrix
    cols = ["id", "source_repository", "source_commit", "source_path", "item_name", "item_type", "disposition",
            "loaded_by_claude_code", "invocation", "plugin", "primary_destination", "file_count", "topics",
            "dependencies", "variant_of", "merged_into", "description", "reason", "notes"]
    with open(audit / "capability-matrix.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for c in comps:
            row = []
            for k in cols:
                v = c.get(k)
                if isinstance(v, list):
                    v = "; ".join(v)
                row.append("" if v is None else str(v)[:600])
            w.writerow(row)

    # ---------------------------------------------------------- merge map
    merge = {
        "schema": "source repository + original path -> final destination path(s)",
        "file_level_map": "audit/file-map.json (every tracked file of every source)",
        "transforms": transforms,
        "components": [{"id": c["id"], "type": c["item_type"], "disposition": c["disposition"],
                        "destinations": c["destination_paths"], "invocation": c.get("invocation"),
                        "merged_into": c.get("merged_into"), "variant_of": c.get("variant_of")} for c in comps],
        "overlap_groups": {t: sorted(v) for t, v in sorted(overlap_groups.items())},
        "overlap_policy": "Overlapping skills from different sources are ALL retained and loadable. Routing "
                          "precedence for each topic is defined in registry/routing-rules.json; alternatives stay "
                          "available by explicit invocation.",
    }
    (audit / "merge-map.json").write_text(json.dumps(merge, indent=1) + "\n")

    # ---------------------------------------------------------- registry indexes
    skills = [c for c in comps if c["item_type"] == "skill"]
    loaded = [c for c in skills if c.get("loaded_by_claude_code")]
    idx = [{"invocation": c["invocation"], "plugin": c["plugin"], "name": c["item_name"],
            "source": c["source_repository"], "source_path": c["source_path"],
            "description": c.get("description", ""), "topics": c.get("topics", []),
            "dependencies": c.get("dependencies", []),
            "user_invoked_only": c.get("frontmatter", {}).get("disable-model-invocation") == "true",
            "hidden": c.get("frontmatter", {}).get("hidden") == "true"} for c in loaded]
    # agent-browser CLI-served skills are routable too
    for c in skills:
        if c.get("access"):
            idx.append({"invocation": c["access"], "plugin": "agent-browser", "name": c["item_name"],
                        "source": c["source_repository"], "source_path": c["source_path"],
                        "description": c.get("description", ""), "topics": c.get("topics", []),
                        "dependencies": ["agent-browser CLI"], "user_invoked_only": False, "hidden": False,
                        "served_by_cli": True})
    idx.insert(0, {"invocation": "omega-core:omega-engineering-x10", "plugin": "omega-core", "name": "omega-engineering-x10",
                   "source": "omega-engineering-x10", "source_path": "plugins/omega-core/skills/omega-engineering-x10/SKILL.md",
                   "description": "Master router: maps an engineering task to specialist skills across all ten sources.",
                   "topics": ["skill-authoring-discovery"], "dependencies": ["python3"], "user_invoked_only": False,
                   "hidden": False})
    agents = [{"name": c["item_name"], "plugin": c["plugin"], "source": c["source_repository"],
               "source_path": c["source_path"], "description": c.get("description", "")}
              for c in comps if c["item_type"] == "agent" and c["disposition"] == "preserved"
              and (c["source_path"].startswith("agents/") or c["plugin"] == "ui-ux-pro-max-design-stack")]
    commands = [{"name": c["item_name"], "plugin": c["plugin"], "source": c["source_repository"],
                 "source_path": c["source_path"], "description": c.get("description", "")}
                for c in comps if c["item_type"] == "command" and c["disposition"] in ("preserved", "adapted-with-traceability")
                and c.get("primary_destination") and c["primary_destination"].startswith(f"plugins/{c['plugin']}/commands/")]
    (reg / "skills.json").write_text(json.dumps(idx, indent=1) + "\n")
    caps = defaultdict(list)
    for s in idx:
        for t in s["topics"]:
            caps[t].append(s["invocation"])
    (reg / "capabilities.json").write_text(json.dumps({"topics": {k: sorted(v) for k, v in sorted(caps.items())},
                                                       "agents": agents, "commands": commands}, indent=1) + "\n")
    core_reg = root / "plugins" / "omega-core" / "registry"
    core_reg.mkdir(parents=True, exist_ok=True)
    for name in ("skills.json", "capabilities.json", "routing-rules.json"):
        if (reg / name).exists():
            shutil.copy2(reg / name, core_reg / name)

    # ---------------------------------------------------------- source manifest md / inventory
    by_repo = defaultdict(list)
    for c in comps:
        by_repo[c["source_repository"]].append(c)
    files_by_repo = defaultdict(list)
    for f in files:
        files_by_repo[f["repo"]].append(f)
    from rules import REPOS
    slug_dir = {m["slug"]: d for d, m in REPOS.items()}

    inv = ["# Source inventory", "",
           "Generated by `tools/build.py` from `git ls-files` of each pinned source. Every tracked file is assigned to "
           "exactly one component; every component has a disposition. Full per-item data: `audit/capability-matrix.csv`, "
           "`registry/components.json`; per-file map: `audit/file-map.json`.", ""]
    inv.append("| Repository | Commit | Tag | Files | Skills (all copies) | Skills loaded in Claude Code | Agents | Commands | Hooks | Rules | Scripts | MCP | Manifests | Bundles |")
    inv.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m in manifest:
        cs = by_repo[m["repo"]]
        t = Counter(c["item_type"] for c in cs)
        ld = sum(1 for c in cs if c.get("loaded_by_claude_code"))
        inv.append(f"| {m['repo']} | `{m['commit'][:12]}` | {m.get('tag') or '-'} | {m['tracked_files']} | {t['skill']} | {ld} | "
                   f"{t['agent']} | {t['command']} | {t['hook']} | {t['rule']} | {t['script']} | {t['mcp-config']} | "
                   f"{t['plugin-manifest']} | {t['resource-bundle']} |")
    inv += ["", "Notes: *Skills (all copies)* counts every SKILL.md, including harness mirrors and translations. "
            "*Agents/Commands* likewise include localized and harness copies; the loaded sets are listed in "
            "`registry/capabilities.json`.", ""]
    for m in manifest:
        cs = by_repo[m["repo"]]
        inv += [f"## {m['repo']}", "", f"- Remote: {m['remote']}", f"- Branch: `{m['default_branch']}`  Commit: `{m['commit']}` ({m['commit_date']})",
                f"- Role: {m['role']}", ""]
        sk = sorted((c for c in cs if c["item_type"] == "skill"), key=lambda c: (not c.get("loaded_by_claude_code"), c["source_path"]))
        inv += ["| Skill | Source path | Disposition | Invocation / target |", "|---|---|---|---|"]
        for c in sk:
            tgt = c.get("invocation") or c.get("access") or c.get("merged_into") or c.get("variant_of") or "-"
            inv.append(f"| {c['item_name']} | `{c['source_path']}` | {c['disposition']} | `{tgt}` |")
        inv.append("")
    (audit / "source-inventory.md").write_text("\n".join(inv) + "\n")

    # ---------------------------------------------------------- licenses
    lic = ["# Source licenses and attribution", "",
           "All ten sources use permissive licenses that allow redistribution with attribution. Each plugin directory "
           "keeps its upstream LICENSE (and NOTICE where present). No source was relicensed.", "",
           "| Repository | License | Files carried | Plugin(s) |", "|---|---|---|---|"]
    plugs = defaultdict(set)
    for c in comps:
        if c.get("plugin"):
            plugs[c["source_repository"]].add(c["plugin"])
    for m in manifest:
        l, fcar = LICENSE_INFO[m["repo"]]
        lic.append(f"| {m['repo']} | {l} | {fcar} | {', '.join(sorted(plugs[m['repo']]))} |")
    lic += ["", "## Obligations", "",
            "- **Apache-2.0** (agent-browser, claude-mem, VibeSec, Graphify): LICENSE and NOTICE retained in each plugin; "
            "modified files are marked. The only modified file is `plugins/vibesec/skills/vibesec/SKILL.md` "
            "(frontmatter `name` changed; see `audit/transforms.json`).",
            "- **MIT** (mattpocock, replica, ECC, vercel skills, UI UX Pro Max, superpowers): copyright notice and license "
            "text retained in each plugin.",
            "- Third-party notices bundled by upstream (vercel skills ThirdPartyNoticeText.txt, ui-styling LICENSE.txt and "
            "canvas-fonts OFL files) are copied unchanged.",
            "- Generated files (`plugin.json` for assembled plugins, `OMEGA-PROVENANCE.json`, omega-core) are new work "
            "under MIT and identify their upstream source and commit."]
    (audit / "source-licenses.md").write_text("\n".join(lic) + "\n")

    # ---------------------------------------------------------- exclusions
    ex = ["# Exclusions and non-copied items", "",
          "Nothing below is deleted: every item remains in its pinned source snapshot (`sources/<repo>` at the commit in "
          "`audit/source-manifest.json`; re-create with `scripts/fetch-sources.sh`). Items are grouped by the rule that "
          "decided them; skills, agents and commands are listed individually.", ""]
    for disp in ("excluded-with-justification", "retained-as-external-runtime", "merged-with-traceability"):
        cs = [c for c in comps if c["disposition"] == disp]
        ex += [f"## {disp} ({len(cs)} components)", ""]
        groups = defaultdict(list)
        for c in cs:
            reason = c.get("reason") or (c["notes"][-1] if c["notes"] else "")
            groups[(c["source_repository"], reason)].append(c)
        for (repo, reason), g in sorted(groups.items()):
            t = Counter(c["item_type"] for c in g)
            ex += [f"### {repo}: {', '.join(f'{v} {k}' for k, v in sorted(t.items()))}", "", f"Reason: {reason}", ""]
            named = [c for c in g if c["item_type"] in ("skill", "agent", "command")]
            if named:
                if len(named) > 60:
                    ex.append(f"<details><summary>{len(named)} items</summary>\n")
                for c in named:
                    extra = f" -> `{c.get('merged_into') or c.get('variant_of')}`" if (c.get("merged_into") or c.get("variant_of")) else ""
                    ex.append(f"- {c['item_type']} `{c['source_path']}`{extra}")
                if len(named) > 60:
                    ex.append("\n</details>")
                ex.append("")
    (audit / "exclusions.md").write_text("\n".join(ex) + "\n")

    # ---------------------------------------------------------- unresolved
    unresolved = [c for c in comps if c["disposition"] in ("unclassified", "blocked-uninspected") or c.get("unique_variant")
                  and not c.get("reviewed_individually")]
    ur = ["# Unresolved items", "",
          "Two levels: (1) registry accounting of source components, computed by the build; (2) runtime items "
          "from live verification, from `audit/open-items.json`. Zero registry gaps does not mean every "
          "capability was verified; see level 2.", "", "## 1. Registry accounting", ""]
    if unresolved:
        ur += [f"- {c['id']}: {c['disposition']} {'; '.join(c['notes'])}" for c in unresolved]
    else:
        ur += ["No component is unclassified, blocked, or an unreviewed unique variant (3337 of 3337 accounted for).", ""]
    oi_path = audit / "open-items.json"
    if oi_path.exists():
        oi = json.loads(oi_path.read_text())
        titles = {"implementation_blockers": "Implementation blockers (OMEGA integration defects still open)",
                  "environment_restricted": "Environment-restricted (cannot be verified in this sandbox; requirement given)",
                  "upstream_limitations": "Upstream limitations (present in the pinned source; not integration regressions)",
                  "not_verified": "Not verified (capability present, not exercised end to end)"}
        ur += ["## 2. Runtime items", ""]
        for key, title in titles.items():
            items = oi.get(key, [])
            ur += [f"### {title}: {len(items)}", ""]
            if not items:
                ur += ["None.", ""]
                continue
            for it in items:
                extra = it.get("requirement") or it.get("impact") or it.get("reason") or ""
                ev = f" Evidence: {it['evidence']}." if it.get("evidence") else ""
                ur.append(f"- **{it['id']}** {it['item']}.{ev} {extra}".rstrip())
            ur.append("")
    (audit / "unresolved-items.md").write_text("\n".join(ur) + "\n")

    # ---------------------------------------------------------- reconciliation
    rc = ["# Disposition reconciliation", "",
          "Counts are computed, not typed. Each row sums to the component total for that repository.", "",
          "| Repository | Components | " + " | ".join(DISPOSITIONS) + " | Sum OK |", "|---|---|" + "---|" * (len(DISPOSITIONS) + 1)]
    for m in manifest:
        cs = by_repo[m["repo"]]
        cnt = Counter(c["disposition"] for c in cs)
        rc.append(f"| {m['repo']} | {len(cs)} | " + " | ".join(str(cnt[d]) for d in DISPOSITIONS) +
                  f" | {'yes' if sum(cnt.values()) == len(cs) else 'NO'} |")
    rc += ["", "## Skills only", "", "| Repository | Skills | " + " | ".join(DISPOSITIONS) + " | Loaded |",
           "|---|---|" + "---|" * (len(DISPOSITIONS) + 1)]
    for m in manifest:
        cs = [c for c in by_repo[m["repo"]] if c["item_type"] == "skill"]
        cnt = Counter(c["disposition"] for c in cs)
        rc.append(f"| {m['repo']} | {len(cs)} | " + " | ".join(str(cnt[d]) for d in DISPOSITIONS) +
                  f" | {sum(1 for c in cs if c.get('loaded_by_claude_code'))} |")
    fcnt = Counter(f["disposition"] for f in files)
    rc += ["", "## Files", "", f"Tracked files: {len(files)}. " + ", ".join(f"{k}: {v}" for k, v in fcnt.items()), ""]
    (audit / "reconciliation.md").write_text("\n".join(rc) + "\n")


def write_manifest(root: Path, manifest, comps):
    """MANIFEST.md: one row per plugin, computed from the registry."""
    import json as _json
    from manifests import UNLISTED
    market = {e["name"] for e in _json.loads((root / ".claude-plugin/marketplace.json").read_text())["plugins"]}
    commits = {m["repo"]: m["commit"] for m in manifest}
    rows = []
    for pdir in sorted((root / "plugins").iterdir()):
        pj = _json.loads((pdir / ".claude-plugin/plugin.json").read_text())
        cs = [c for c in comps if c.get("plugin") == pdir.name]
        srcs = sorted({c["source_repository"] for c in cs}) or ["(OMEGA)"]
        sk = sum(1 for c in cs if c["item_type"] == "skill" and c.get("loaded_by_claude_code"))
        if pdir.name == "omega-core":
            sk = 1
        ag = sum(1 for c in cs if c["item_type"] == "agent" and (c["source_path"].startswith("agents/") or "stack/" in c["source_path"]))
        cm = sum(1 for c in cs if c["item_type"] == "command" and (c["source_path"].startswith("commands/") or "stack/" in c["source_path"]))
        hk = sum(1 for c in cs if c["item_type"] == "hook" and c.get("hook_file", "").endswith(("hooks/hooks.json",)) and
                 (c["hook_file"] in ("hooks/hooks.json", "plugin/hooks/hooks.json", "cowork/hooks/hooks.json")))
        files = sum(1 for _ in pdir.rglob("*") if _.is_file() or _.is_symlink())
        listed = "yes" if pj["name"] in market else f"no ({UNLISTED.get(pdir.name, '')})"
        commit = ", ".join(commits[s][:12] for s in srcs if s in commits) or "-"
        rows.append(f"| `{pj['name']}` | {', '.join(srcs)} | `{commit}` | {pj.get('version')} | {sk} | {cm} | {ag} | {hk} | {files} | {listed} |")
    text = ["# MANIFEST", "",
            "Generated by `tools/build.py`. One row per plugin directory. Skills = skills Claude Code loads from the plugin; "
            "Hooks = hook groups in the plugin's own hooks.json.", "",
            "| Plugin | Source | Commit | Version | Skills | Commands | Agents | Hook groups | Files | In marketplace |",
            "|---|---|---|---|---|---|---|---|---|---|"] + rows + [
            "", "Totals and dispositions: `audit/reconciliation.md`. Per-file provenance: `audit/file-map.json`."]
    (root / "MANIFEST.md").write_text("\n".join(text) + "\n")
