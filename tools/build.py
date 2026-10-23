#!/usr/bin/env python3
"""Build OMEGA-ENGINEERING X10 from the ten pinned source repositories.

Usage:  python3 tools/build.py [--sources ../sources] [--no-copy]

Steps:
  1. Enumerate every tracked file of every source (git ls-files) and match it
     against tools/rules.py. Unmatched files are recorded as `unclassified`.
  2. Copy matched files into plugins/<plugin>/ (symlinks preserved, transforms
     applied and recorded).
  3. Derive components (skills, agents, commands, hooks, MCP configs, rules,
     manifests, scripts, resource bundles) and give each a disposition.
  4. Write registry/ and audit/ outputs.

The build is deterministic: re-running it on the same commits yields the
same outputs. plugins/omega-core is hand-written and never overwritten,
except for its generated registry copy.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules import EXTRA_COPIES, REPOS, RULES, TRANSFORMS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
AUDIT = ROOT / "audit"
REGISTRY = ROOT / "registry"
HAND_WRITTEN_PLUGINS = {"omega-core"}


def git(repo_dir, *args):
    return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, check=True).stdout


def match_rule(repo, path):
    for rule in RULES:
        r_repo, prefix = rule[0], rule[1]
        if r_repo != repo:
            continue
        if prefix == "" or path == prefix or (prefix.endswith("/") and path.startswith(prefix)) or (
            not prefix.endswith("/") and path.startswith(prefix) and prefix.endswith("-")
        ):
            return rule
    return None


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    data, key = {}, None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val in (">-", ">", "|", "|-"):
                val = ""
            data[key] = val.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------- step 1
def enumerate_sources(src_root):
    manifest, files = [], []
    for repo_dir_name, meta in REPOS.items():
        repo_dir = src_root / repo_dir_name
        if not repo_dir.exists():
            manifest.append({"repo": meta["slug"], "dir": repo_dir_name, "status": "blocked-uninspected",
                             "reason": "clone missing"})
            continue
        commit = git(repo_dir, "rev-parse", "HEAD").strip()
        branch = git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD").strip()
        date = git(repo_dir, "log", "-1", "--format=%cI").strip()
        tag = subprocess.run(["git", "-C", str(repo_dir), "describe", "--tags", "--exact-match"],
                             capture_output=True, text=True).stdout.strip()
        remote = git(repo_dir, "remote", "get-url", "origin").strip()
        entries = git(repo_dir, "ls-files", "-s", "-z").split("\0")
        n = 0
        for e in entries:
            if not e:
                continue
            mode, _obj, _stage_path = e.split(" ", 2)
            path = _stage_path.split("\t", 1)[1]
            files.append({"repo": repo_dir_name, "path": path, "symlink": mode == "120000",
                          "executable": mode == "100755"})
            n += 1
        manifest.append({"repo": meta["slug"], "dir": repo_dir_name, "remote": remote, "default_branch": branch,
                         "commit": commit, "commit_date": date, "tag": tag or None, "tracked_files": n,
                         "role": meta["role"], "status": "inspected"})
    return manifest, files


# --------------------------------------------------------------------- step 2
def classify_and_copy(src_root, files, do_copy):
    transforms_applied = []
    for f in files:
        rule = match_rule(f["repo"], f["path"])
        if rule is None:
            f.update(kind="unclassified", disposition="unclassified", plugin=None, dest=None,
                     reason="No rule matched")
            continue
        _repo, prefix, kind = rule[0], rule[1], rule[2]
        if kind == "retain":
            f.update(kind="retain", disposition=rule[3], plugin=None, dest=None, reason=rule[4])
            continue
        plugin, dest_prefix = rule[3], rule[4]
        if prefix == "" or prefix.endswith("/"):
            rel = f["path"][len(prefix):]
            dest = dest_prefix + rel
        else:
            dest = dest_prefix
        f.update(kind=kind, plugin=plugin, dest=f"plugins/{plugin}/{dest}", reason=None,
                 disposition="preserved")
        key = (f["repo"], f["path"])
        if key in TRANSFORMS:
            f["disposition"] = "adapted-with-traceability"
            f["transform"] = TRANSFORMS[key]["why"]
            # recorded in every mode: a --no-copy rebuild must not drop the transform audit trail
            transforms_applied.append({"source": f"{f['repo']}/{f['path']}", "dest": f["dest"],
                                       "why": TRANSFORMS[key]["why"]})
        if do_copy:
            src = src_root / f["repo"] / f["path"]
            dst = ROOT / f["dest"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            if f["symlink"]:
                os.symlink(os.readlink(src), dst)
            elif key in TRANSFORMS:
                text = src.read_text()
                for old, new in TRANSFORMS[key]["replace"]:
                    if old not in text:
                        raise SystemExit(f"transform anchor missing in {key}: {old!r}")
                    text = text.replace(old, new, 1)
                dst.write_text(text)
            else:
                shutil.copy2(src, dst)
    for repo, path, plugin, dest in EXTRA_COPIES:
        src, dst = src_root / repo / path, PLUGINS / plugin / dest
        if not src.exists():
            raise SystemExit(f"extra copy source missing: {repo}/{path}")
        if do_copy:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        extra_files.append({"repo": repo, "path": path, "disposition": "preserved", "dest": f"plugins/{plugin}/{dest}",
                            "reason": "extra copy (license/notice for a second plugin built from this repository)",
                            "extra": True})
    return transforms_applied


extra_files = []


# --------------------------------------------------------------------- step 3
DEP_PATTERNS = {
    "agent-browser CLI": r"\bagent-browser\b",
    "npx/npm": r"\bnpx\b|\bnpm (i|install)\b",
    "uv": r"\buv (tool|run|pip)\b",
    "python3": r"\bpython3?\b",
    "node": r"\bnode\b",
    "bun": r"\bbun\b",
    "docker": r"\bdocker\b",
    "gh CLI": r"\bgh (pr|issue|api|repo)\b",
    "git": r"\bgit (status|diff|commit|worktree|log|checkout|branch)\b",
    "playwright": r"\bplaywright\b",
    "graphify CLI": r"\bgraphify\b",
    "claude-mem worker": r"\bclaude-mem\b|localhost:37777|mem-search",
    "MCP server": r"\bmcp__|MCP server",
    "network/web": r"https?://(?!github\.com)",
}


def skill_dependencies(text):
    return sorted(k for k, p in DEP_PATTERNS.items() if re.search(p, text))


def outline(text, limit=12):
    heads = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", text, re.M)]
    return heads[:limit]


def plugin_loaded_skill_dirs(plugin_root):
    """Return the skill directories (relative to plugin root) Claude Code loads."""
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    roots = []
    if manifest.exists():
        data = json.loads(manifest.read_text())
        s = data.get("skills")
        if isinstance(s, str):
            s = [s]
        if s:
            roots = [x.removeprefix("./").rstrip("/") for x in s]
    if not roots:
        roots = ["skills"]  # default plugin convention
    loaded = set()
    for r in roots:
        base = plugin_root / r if r else plugin_root
        if (base / "SKILL.md").exists():
            loaded.add(r)
            continue
        if base.is_dir():
            for child in sorted(base.iterdir()):
                if (child / "SKILL.md").exists():
                    loaded.add(str(child.relative_to(plugin_root)))
    return loaded


def derive_components(src_root, files, commits):
    comps = []
    by_repo = defaultdict(list)
    for f in files:
        by_repo[f["repo"]].append(f)
    claimed = set()

    def make(f_list, ctype, name, primary, extra=None):
        dests = sorted({x["dest"] for x in f_list if x["dest"]})
        disp_counts = Counter(x["disposition"] for x in f_list)
        p = primary
        if p["disposition"] == "unclassified" or "unclassified" in disp_counts:
            disposition = "unclassified"
        elif p["kind"] == "retain":
            disposition = p["disposition"]
        elif "adapted-with-traceability" in disp_counts:
            disposition = "adapted-with-traceability"
        else:
            disposition = "preserved"
        c = {
            "id": f"{REPOS[p['repo']]['slug']}:{p['path'] if ctype != 'resource-bundle' else name}",
            "source_repository": REPOS[p["repo"]]["slug"],
            "source_commit": commits[p["repo"]],
            "source_path": p["path"] if ctype not in ("resource-bundle",) else name,
            "item_name": name,
            "item_type": ctype,
            "file_count": len(f_list),
            "destination_paths": dests[:50] + ([f"... {len(dests) - 50} more"] if len(dests) > 50 else []),
            "primary_destination": p["dest"],
            "disposition": disposition,
            "reason": p.get("reason"),
            "transform": p.get("transform"),
            "plugin": p.get("plugin"),
            "validation_status": "pending",
            "notes": [],
        }
        if extra:
            c.update(extra)
        for x in f_list:
            claimed.add((x["repo"], x["path"]))
        comps.append(c)
        return c

    for repo, flist in by_repo.items():
        paths = {f["path"]: f for f in flist}
        # ---- skills: any directory holding SKILL.md (incl. graphify skill.md)
        skill_dirs = sorted({p.rsplit("/", 1)[0] if "/" in p else "" for p in paths if p.endswith("SKILL.md")
                             and p.split("/")[-1] == "SKILL.md"}, key=lambda d: (-d.count("/"), d))
        if repo == "Graphify-Labs__graphify":
            skill_files = ["graphify/skill.md"] + sorted(p for p in paths if re.match(r"graphify/skill-[a-z]+\.md$", p))
        else:
            skill_files = []
        for d in skill_dirs:
            prefix = d + "/" if d else ""
            members = [f for p, f in paths.items() if (p.startswith(prefix) or not d) and (repo, p) not in claimed]
            if not d:  # root skill (VibeSec): only root-level files belong to it
                members = [paths["SKILL.md"]]
            primary = paths[prefix + "SKILL.md"]
            text = (src_root / repo / primary["path"]).read_text(errors="replace") if not primary["symlink"] else ""
            fm = parse_frontmatter(text)
            make(members, "skill", fm.get("name") or d.split("/")[-1], primary, {
                "description": fm.get("description", ""),
                "frontmatter": {k: v for k, v in fm.items() if k not in ("description",)},
                "dependencies": skill_dependencies(text),
                "section_outline": outline(text),
                "symlink": primary["symlink"],
            })
        for sf in skill_files:
            primary = paths[sf]
            text = (src_root / repo / sf).read_text(errors="replace")
            fm = parse_frontmatter(text)
            members = [primary]
            if sf == "graphify/skill.md":
                members += [f for p, f in paths.items() if p.startswith("graphify/skills/claude/")]
            make(members, "skill", fm.get("name", "graphify") + ("" if sf.endswith("/skill.md") else
                 "@" + sf.split("skill-")[1][:-3]), primary, {
                "description": fm.get("description", ""), "frontmatter": {k: v for k, v in fm.items() if k != "description"},
                "dependencies": skill_dependencies(text), "section_outline": outline(text), "symlink": False})
        # ---- hooks: each matcher group in each hooks json
        for p, f in paths.items():
            if (repo, p) in claimed:
                continue
            if re.search(r"(^|/)hooks/[^/]*hooks[^/]*\.json$|(^|/)hooks\.json$|codex-hooks\.json$|qoder-hooks\.json$", p) \
                    and "schema" not in p and "metadata" not in p and not f["symlink"]:
                try:
                    data = json.loads((src_root / repo / p).read_text())
                except Exception:
                    continue
                hooks = data.get("hooks", data) if isinstance(data, dict) else {}
                if not isinstance(hooks, dict):
                    continue
                for event, groups in hooks.items():
                    if not isinstance(groups, list):
                        continue
                    for i, g in enumerate(groups):
                        cmds = []
                        for h in (g.get("hooks", []) if isinstance(g, dict) else []):
                            cmd = h.get("command", "")
                            if h.get("args"):
                                cmd += " " + " ".join(h["args"])
                            cmds.append(cmd[:160])
                        c = make([f], "hook", f"{event}[{i}]", f, {
                            "hook_event": event, "matcher": g.get("matcher") if isinstance(g, dict) else None,
                            "hook_commands": cmds, "hook_file": p})
                        c["id"] += f"#{event}[{i}]"
                        claimed.discard((repo, p))  # hooks file still also forms a manifest component
                claimed.add((repo, p))
        # ---- agents and commands (markdown in agents/ or commands/ dirs, outside skills)
        for p, f in sorted(paths.items()):
            if (repo, p) in claimed or not p.endswith(".md"):
                continue
            parts = p.split("/")
            if len(parts) >= 2 and parts[-2] in ("agents", "commands"):
                ctype = "agent" if parts[-2] == "agents" else "command"
                text = (src_root / repo / p).read_text(errors="replace") if not f["symlink"] else ""
                fm = parse_frontmatter(text)
                make([f], ctype, fm.get("name") or parts[-1][:-3], f, {
                    "description": fm.get("description", "")[:400]})
        # ---- rules (ECC rules/ tree and .claude/rules)
        for p, f in sorted(paths.items()):
            if (repo, p) in claimed:
                continue
            if (p.startswith("rules/") or "/rules/" in p) and p.endswith(".md") and repo == "affaan-m__ECC":
                make([f], "rule", p.split("/", 1)[1] if p.startswith("rules/") else p, f)
        # ---- MCP configs, plugin manifests
        for p, f in sorted(paths.items()):
            if (repo, p) in claimed:
                continue
            base = p.split("/")[-1]
            if base in (".mcp.json", "qoder.mcp.json") or p.startswith("mcp-configs/"):
                make([f], "mcp-config", p, f)
            elif re.search(r"(^|/)\.[a-z-]*plugin/[^/]+\.json$", p) or base in ("gemini-extension.json", "agent.yaml"):
                make([f], "plugin-manifest", p, f)
        # ---- scripts / executables outside skills
        for p, f in sorted(paths.items()):
            if (repo, p) in claimed:
                continue
            if re.search(r"\.(sh|py|js|cjs|mjs|ts|ps1|cmd)$", p) and (
                    p.startswith(("scripts/", "plugin/scripts/", "hooks/", "plugin/hooks/", "bin/", "cowork/"))
                    or p.count("/") == 0):
                if "/test" in p or p.startswith("tests/"):
                    continue
                make([f], "script", p, f)
        # ---- everything else: resource bundles grouped by first two dirs
        groups = defaultdict(list)
        for p, f in paths.items():
            if (repo, p) in claimed:
                continue
            parts = p.split("/")
            key = "/".join(parts[:2]) + "/" if len(parts) > 2 else (parts[0] + "/" if len(parts) == 2 else "(root files)")
            groups[key].append(f)
        for key, fl in sorted(groups.items()):
            fl.sort(key=lambda x: x["path"])
            # a bundle may mix dispositions only if every file shares one rule outcome
            sub = defaultdict(list)
            for x in fl:
                sub[(x["kind"], x["disposition"], x.get("plugin"))].append(x)
            for (_k, disp, plug), members in sub.items():
                c = make(members, "resource-bundle", key, members[0])
                if len(sub) > 1:
                    c["id"] += f" [{disp}{'->' + plug if plug else ''}]"
                c["sample_files"] = [m["path"] for m in members[:8]]
    return comps


# --------------------------------------------------------------------- step 4
def loaded_flags(comps):
    loaded_cache = {}
    for c in comps:
        if c["item_type"] != "skill":
            continue
        c["loaded_by_claude_code"] = False
        c["invocation"] = None
        if not c["plugin"] or c["disposition"] in ("excluded-with-justification", "retained-as-external-runtime",
                                                  "merged-with-traceability"):
            continue
        plugin_root = PLUGINS / c["plugin"]
        if c["plugin"] not in loaded_cache:
            loaded_cache[c["plugin"]] = plugin_loaded_skill_dirs(plugin_root)
        rel_dir = str(Path(c["primary_destination"]).parent.relative_to(f"plugins/{c['plugin']}"))
        if rel_dir in loaded_cache[c["plugin"]]:
            c["loaded_by_claude_code"] = True
            dest_text = (ROOT / c["primary_destination"]).read_text(errors="replace")
            name = parse_frontmatter(dest_text).get("name") or Path(rel_dir).name
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
                c["notes"].append(f"Frontmatter name {name!r} is not a valid skill identifier; it is indexed under "
                                  f"its directory name {Path(rel_dir).name!r}. The file is unchanged.")
                name = Path(rel_dir).name
            c["invocation"] = f"{c['plugin']}:{name}"
        else:
            c["notes"].append("Copied into the plugin to preserve upstream layout, but not on the plugin's "
                              "skill load path (harness variant or CLI-served content). See disposition notes.")
    return comps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=str(ROOT.parent / "sources"))
    ap.add_argument("--no-copy", action="store_true")
    args = ap.parse_args()
    src_root = Path(args.sources).resolve()

    if not args.no_copy:
        for p in PLUGINS.iterdir() if PLUGINS.exists() else []:
            if p.name not in HAND_WRITTEN_PLUGINS:
                shutil.rmtree(p)
    manifest, files = enumerate_sources(src_root)
    commits = {m["dir"]: m.get("commit") for m in manifest}
    transforms = classify_and_copy(src_root, files, not args.no_copy)

    import manifests  # generated plugin manifests for plugins without upstream ones
    manifests.write_generated_manifests(ROOT, manifest)

    comps = derive_components(src_root, files, commits)
    comps = loaded_flags(comps)
    import overlay
    overlap_groups = overlay.apply(comps, src_root)

    AUDIT.mkdir(exist_ok=True)
    REGISTRY.mkdir(exist_ok=True)
    (AUDIT / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (REGISTRY / "components.json").write_text(json.dumps(comps, indent=1) + "\n")
    file_map = [{"repo": REPOS[f["repo"]]["slug"], "path": f["path"], "disposition": f["disposition"],
                 "dest": f["dest"], "reason": f.get("reason")} for f in files]
    file_map += [{**e, "repo": REPOS[e["repo"]]["slug"]} for e in extra_files]
    (AUDIT / "file-map.json").write_text(json.dumps(file_map) + "\n")
    (AUDIT / "transforms.json").write_text(json.dumps(transforms, indent=2) + "\n")

    import reports
    reports.write_all(ROOT, manifest, files, comps, transforms, overlap_groups)
    reports.write_manifest(ROOT, manifest, comps)
    unclassified = [f for f in files if f["disposition"] == "unclassified"]
    print(f"files={len(files)} components={len(comps)} unclassified={len(unclassified)}")
    for u in unclassified[:20]:
        print("  UNCLASSIFIED", u["repo"], u["path"])
    return 1 if unclassified else 0


if __name__ == "__main__":
    sys.exit(main())
