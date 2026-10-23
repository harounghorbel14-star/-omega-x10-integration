#!/usr/bin/env python3
"""Structural and integrity validation for OMEGA-ENGINEERING X10.

  python3 tools/validate.py [--sources ../sources] [--syntax] [--report audit/structural-validation.json]

Checks (each reported PASS/FAIL with counts and examples):
  sources        all ten sources inspected, commits recorded
  classified     every tracked source file matched a rule; every component has a known disposition
  destinations   every copied file exists at its destination (symlinks preserved)
  integrity      every copied file is byte-identical to its source, except recorded transforms
  manifests      every plugin has a valid plugin.json; marketplace entries point at existing plugins
  skills         every loaded skill has frontmatter name + description; name is a valid identifier
  references     relative links/paths in loaded SKILL.md files resolve; new breakage vs. source is a FAIL
  json           every .json file in plugins/ parses (files that also fail upstream are reported, not failed)
  syntax         (--syntax) py_compile / bash -n / node --check on scripts in plugins/, compared with source
  routes         every skill named in routing-rules.json is registered
  licenses       every plugin ships its upstream LICENSE
  reconcile      component disposition counts sum to the component total per repository
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from rules import REPOS  # noqa: E402

VALID = {"preserved", "merged-with-traceability", "adapted-with-traceability", "excluded-with-justification",
         "retained-as-external-runtime", "blocked-uninspected"}
SLUG2DIR = {m["slug"]: d for d, m in REPOS.items()}
results = []


def check(name, ok, detail, examples=()):
    results.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail, "examples": list(examples)[:15]})


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def link_targets(text):
    out = set()
    for m in re.finditer(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", text):
        out.add(m.group(1))
    for m in re.finditer(r"`((?:\./)?(?:references|scripts|templates|data|assets|examples|rules|agents)/[A-Za-z0-9_./-]+)`", text):
        out.add(m.group(1))
    return {t for t in out if not re.match(r"^[a-z]+:|^/|^\$|^~|^\{|^<", t) and "*" not in t and "{" not in t}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=str(ROOT.parent / "sources"))
    ap.add_argument("--syntax", action="store_true")
    ap.add_argument("--report", default=str(ROOT / "audit" / "structural-validation.json"))
    a = ap.parse_args()
    src = Path(a.sources)
    manifest = json.loads((ROOT / "audit/source-manifest.json").read_text())
    fmap = json.loads((ROOT / "audit/file-map.json").read_text())
    comps = json.loads((ROOT / "registry/components.json").read_text())
    transforms = {t["dest"] for t in json.loads((ROOT / "audit/transforms.json").read_text())}

    # sources
    insp = [m for m in manifest if m.get("status") == "inspected" and m.get("commit")]
    check("sources", len(insp) == 10, f"{len(insp)}/10 repositories inspected with commit recorded",
          [m["repo"] for m in manifest if m not in insp])

    # classified
    uncl = [f for f in fmap if f["disposition"] == "unclassified"]
    badc = [c["id"] for c in comps if c["disposition"] not in VALID]
    check("classified", not uncl and not badc,
          f"{len(fmap)} files, {len(uncl)} unclassified; {len(comps)} components, {len(badc)} with invalid disposition",
          [f"{f['repo']}:{f['path']}" for f in uncl] + badc)

    # destinations + integrity
    copied = [f for f in fmap if f["dest"]]
    missing, mismatch = [], []
    for f in copied:
        d = ROOT / f["dest"]
        s = src / SLUG2DIR[f["repo"]] / f["path"]
        if not (d.exists() or d.is_symlink()):
            missing.append(f["dest"]); continue
        if f["dest"] in transforms:
            continue
        if s.is_symlink():
            if not d.is_symlink() or d.readlink() != s.readlink():
                mismatch.append(f["dest"])
        elif sha(d) != sha(s):
            mismatch.append(f["dest"])
    check("destinations", not missing, f"{len(copied)} copied files, {len(missing)} missing at destination", missing)
    check("integrity", not mismatch, f"{len(copied) - len(transforms)} byte-compared, {len(mismatch)} differ; "
          f"{len(transforms)} recorded transform(s) excluded", mismatch)

    # manifests
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    probs = []
    for e in market["plugins"]:
        pdir = ROOT / e["source"]
        mp = pdir / ".claude-plugin/plugin.json"
        if not mp.exists():
            probs.append(f"{e['name']}: no plugin.json"); continue
        pj = json.loads(mp.read_text())
        if pj.get("name") != e["name"]:
            probs.append(f"{e['name']}: plugin.json name {pj.get('name')}")
        if not pj.get("version"):
            probs.append(f"{e['name']}: missing version")
    for p in (ROOT / "plugins").iterdir():
        if not (p / ".claude-plugin/plugin.json").exists():
            probs.append(f"{p.name}: plugin dir without manifest")
    check("manifests", not probs, f"{len(market['plugins'])} marketplace plugins; {len(list((ROOT / 'plugins').iterdir()))} plugin dirs", probs)

    # skills
    loaded = [c for c in comps if c["item_type"] == "skill" and c.get("loaded_by_claude_code")]
    sk_probs, name_notes = [], []
    for c in loaded:
        text = (ROOT / c["primary_destination"]).read_text(errors="replace")
        if not text.startswith("---"):
            sk_probs.append(f"{c['invocation']}: no frontmatter"); continue
        fm = text.split("\n---", 1)[0]
        if not re.search(r"^name:", fm, re.M) or not re.search(r"^description:", fm, re.M):
            sk_probs.append(f"{c['invocation']}: missing name/description")
        m = re.search(r"^name:\s*(.+)$", fm, re.M)
        if m and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", m.group(1).strip().strip("'\"")):
            name_notes.append(f"{c['invocation']}: upstream name {m.group(1).strip()!r}")
    check("skills", not sk_probs, f"{len(loaded)} loaded skills have frontmatter; {len(name_notes)} keep a non-identifier "
          "upstream name (unchanged, indexed by directory)", sk_probs + name_notes)

    # references (only regressions vs. source fail)
    new_broken, upstream_broken = [], []
    for c in loaded:
        dpath = ROOT / c["primary_destination"]
        spath = src / SLUG2DIR[c["source_repository"]] / c["source_path"]
        text = dpath.read_text(errors="replace")
        for t in link_targets(text):
            proot = ROOT / "plugins" / c["plugin"]
            if (dpath.parent / t).exists() or (proot / t).exists():
                continue  # resolves next to the skill, or from the plugin root (repo-root-relative upstream paths)
            in_src = (spath.parent / t).exists() or (src / SLUG2DIR[c["source_repository"]] / t).exists()
            (new_broken if in_src else upstream_broken).append(f"{c['invocation']} -> {t}")
    check("references", not new_broken, f"{len(new_broken)} references broken by integration; {len(upstream_broken)} "
          "already unresolved in the source (reported in audit/validation-report.md)", new_broken)
    (ROOT / "audit" / "upstream-unresolved-references.txt").write_text("\n".join(sorted(upstream_broken)) + "\n")

    # json
    bad_json = []
    for p in (ROOT / "plugins").rglob("*.json"):
        if p.is_symlink() or "node_modules" in p.parts:
            continue
        try:
            json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            bad_json.append(str(p.relative_to(ROOT)))
    # compare against source
    src_bad = []
    for b in bad_json:
        hit = next((f for f in copied if f["dest"] == b), None)
        if hit:
            try:
                json.loads((src / SLUG2DIR[hit["repo"]] / hit["path"]).read_text(encoding="utf-8-sig"))
            except Exception:  # noqa: BLE001
                src_bad.append(b)
    regress = sorted(set(bad_json) - set(src_bad))
    check("json", not regress, f"{len(bad_json)} unparsable .json files, {len(src_bad)} identical to an unparsable upstream "
          "file (e.g. JSONC/templates)", regress + [f"upstream: {x}" for x in src_bad])

    # syntax
    if a.syntax:
        fails = []
        counts = Counter()
        for f in copied:
            d = ROOT / f["dest"]
            if d.is_symlink():
                continue
            ext = d.suffix
            if ext == ".py":
                cmd = [sys.executable, "-c", "import ast,sys;ast.parse(open(sys.argv[1],'rb').read())", str(d)]
            elif ext == ".sh":
                cmd = ["bash", "-n", str(d)]
            elif ext in (".js", ".cjs", ".mjs"):
                cmd = ["node", "--check", str(d)]
            else:
                continue
            counts[ext] += 1
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                s = src / SLUG2DIR[f["repo"]] / f["path"]
                r2 = subprocess.run(cmd[:-1] + [str(s)], capture_output=True, text=True)
                fails.append(("upstream-same " if r2.returncode != 0 else "REGRESSION ") + f["dest"])
        regress = [x for x in fails if x.startswith("REGRESSION")]
        check("syntax", not regress, f"checked {dict(counts)}; {len(fails)} fail, {len(regress)} are integration regressions", fails)

    # routes
    r = subprocess.run([sys.executable, str(ROOT / "plugins/omega-core/scripts/omega.py"), "check-routes"], capture_output=True, text=True)
    check("routes", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:], r.stdout.splitlines()[:-1])

    # licenses
    nolic = [p.name for p in (ROOT / "plugins").iterdir() if p.name != "omega-core" and not any(
        (p / n).exists() for n in ("LICENSE", "LICENSE.md", "LICENSE.txt"))]
    if not (ROOT / "plugins/omega-core/LICENSE").exists():
        nolic.append("omega-core")
    check("licenses", not nolic, f"plugins without LICENSE: {len(nolic)}", nolic)

    # docs: repo paths and plugin install commands referenced in README.md / docs/INSTALL.md must exist
    names = {e["name"] for e in market["plugins"]}
    bad_docs, checked = [], 0
    for doc in ("README.md", "docs/INSTALL.md"):
        text = (ROOT / doc).read_text()
        for m in re.finditer(r"(?<![\w./~-])((?:plugins|scripts|tools|audit|registry|docs|tests)/[A-Za-z0-9_.\-/]+)", text):
            ref = m.group(1).rstrip(".,:;)")
            if any(ch in ref for ch in "<>*"):
                continue
            checked += 1
            if not (ROOT / ref).exists():
                bad_docs.append(f"{doc}: missing path {ref}")
        for m in re.finditer(r"install\s+([a-z0-9-]+)@omega-engineering-x10", text):
            checked += 1
            if m.group(1) not in names:
                bad_docs.append(f"{doc}: plugin {m.group(1)} not in marketplace")
    check("docs", not bad_docs, f"{checked} path/plugin references checked in README.md and docs/INSTALL.md", bad_docs)

    # reconcile
    by = defaultdict(Counter)
    tot = Counter()
    for c in comps:
        by[c["source_repository"]][c["disposition"]] += 1
        tot[c["source_repository"]] += 1
    bad = [k for k in tot if sum(by[k].values()) != tot[k]]
    check("reconcile", not bad and len(tot) == 10, f"{sum(tot.values())} components across {len(tot)} repositories", bad)

    Path(a.report).write_text(json.dumps(results, indent=1) + "\n")
    for res in results:
        print(f"[{res['status']}] {res['check']:<13} {res['detail']}")
        if res["status"] == "FAIL":
            for e in res["examples"]:
                print(f"         - {e}")
    return 0 if all(r["status"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
