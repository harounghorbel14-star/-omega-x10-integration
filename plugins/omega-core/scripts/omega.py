#!/usr/bin/env python3
"""OMEGA-ENGINEERING X10 router and environment doctor.

  omega.py route "<task description>" [--limit N] [--json]
  omega.py doctor [--json]
  omega.py list [--plugin NAME] [--topic TOPIC]
  omega.py show <invocation-or-name>
  omega.py check-routes          # every skill named in routing-rules.json exists

Pure standard library. Reads registry/*.json next to this script's plugin.
Exit codes: 0 ok, 1 problems found (check-routes / doctor --strict), 2 usage.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parent / "registry"
STOP = set("a an the to of for in on and or with my this that is it be can how do i we you please me use".split())


def load(name):
    with open(REG / name) as fh:
        return json.load(fh)


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]*", text.lower()) if t not in STOP and len(t) > 1]


# ------------------------------------------------------------------ doctor
def _which(cmd):
    return shutil.which(cmd)


def _version(cmd, args=("--version",)):
    try:
        out = subprocess.run([cmd, *args], capture_output=True, text=True, timeout=15)
        return (out.stdout or out.stderr).strip().splitlines()[0][:80] if (out.stdout or out.stderr) else "?"
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return f"error: {exc.__class__.__name__}"


def doctor():
    checks = []

    def add(name, ok, detail, fix, needed_by):
        checks.append({"check": name, "ok": bool(ok), "detail": detail, "fix": fix, "needed_by": needed_by})

    for cmd, fix, by in [
        ("python3", "Install Python 3.10+", "omega-core, ui-ux-pro-max, replica scripts, graphify"),
        ("node", "Install Node.js 18+ (agent-browser package wants 24+ for building only)", "ECC hooks, claude-mem, npx skills"),
        ("npx", "Install Node.js (ships npx)", "find-skills (npx skills), ui-ux-pro-max-cli"),
        ("git", "Install git", "superpowers worktrees, ECC, all git workflows"),
        ("agent-browser", "npm i -g agent-browser@0.39.2 && agent-browser install", "agent-browser"),
        ("graphify", "uv tool install graphifyy==0.9.94   (or: pipx install graphifyy==0.9.94)", "graphify"),
        ("uv", "curl -LsSf https://astral.sh/uv/install.sh | sh  (review the script first)", "graphify (recommended installer)"),
        ("bun", "Installed on demand by claude-mem; or https://bun.sh", "claude-mem worker"),
        ("claude-mem", "Install the claude-mem plugin from its upstream marketplace (docs/INSTALL.md)", "claude-mem hooks"),
        ("gh", "https://cli.github.com", "PR workflows (mattpocock pr, claude-mem babysit, ecc github-ops)"),
    ]:
        path = _which(cmd)
        add(cmd, path, f"{path} ({_version(cmd)})" if path else "not on PATH", None if path else fix, by)

    # claude-mem worker health. Mirrors upstream src/shared/SettingsDefaultsManager.ts: env var, then
    # ~/.claude-mem/settings.json, then the default 37700 + (uid % 100) (77 when there is no uid).
    port = host = None
    settings_path = Path(os.environ.get("CLAUDE_MEM_DATA_DIR", Path.home() / ".claude-mem")).expanduser() / "settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        settings = settings.get("env", settings) if isinstance(settings, dict) else {}
        port, host = settings.get("CLAUDE_MEM_WORKER_PORT"), settings.get("CLAUDE_MEM_WORKER_HOST")
    except (OSError, ValueError):
        pass
    port = os.environ.get("CLAUDE_MEM_WORKER_PORT") or port or str(37700 + ((os.getuid() if hasattr(os, "getuid") else 77) % 100))
    host = os.environ.get("CLAUDE_MEM_WORKER_HOST") or host or "127.0.0.1"
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=2) as r:
            add("claude-mem worker", r.status == 200, f"http://{host}:{port}/api/health -> {r.status}", None, "claude-mem:mem-search")
    except Exception as exc:  # noqa: BLE001
        add("claude-mem worker", False, f"not reachable on {host}:{port} ({exc.__class__.__name__})",
            "Start a Claude Code session with the claude-mem plugin enabled (its SessionStart hook starts the worker)",
            "claude-mem:mem-search and other memory skills")

    # graphify output present in cwd?
    gout = Path.cwd() / "graphify-out" / "graph.json"
    add("graphify-out/graph.json in cwd", gout.exists(), str(gout) if gout.exists() else "no graph built here",
        None if gout.exists() else "Run /graphify in this repo to build one", "graphify query/path/explain")

    # skills.sh reachability. `npx skills find` swallows network errors and prints "No skills found"
    # (upstream src/find.ts: catch { return [] }), so check the host directly.
    ok, detail = _reachable(os.environ.get("SKILLS_API_URL", "https://skills.sh") + "/api/search?q=react")
    add("skills.sh reachable", ok, detail,
        None if ok else "Allow https://skills.sh in your network policy; until then `npx skills find` reports "
                        "'No skills found' for every query", "find-skills:find-skills")

    # ECC hooks need npm runtime deps (js-yaml, ajv, ...) that plugin installs do not provide
    # (upstream TROUBLESHOOTING.md "MODULE_NOT_FOUND"). Check every installed ECC copy we can find.
    for ecc in _installed_ecc_dirs():
        have = (ecc / "node_modules" / "js-yaml").is_dir()
        add(f"ecc runtime deps ({ecc})", have, "node_modules present" if have else "node_modules missing: ECC "
            "SessionStart hook fails with Cannot find module 'js-yaml'",
            None if have else f"{HERE / 'install-plugin-deps.sh'} {ecc}", "ecc hooks")
    return checks


def _reachable(url):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=8) as r:
            return True, f"{url} -> HTTP {r.status}"
    except urllib.error.HTTPError as exc:  # the host answered, so it is reachable
        return True, f"{url} -> HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return False, f"{url} unreachable ({exc.__class__.__name__}: {str(exc)[:80]})"


def _installed_ecc_dirs():
    """ECC plugin directories: the plugin cache of the active config, and this checkout's plugins/ecc."""
    found = []
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser()
    for manifest in sorted((config / "plugins" / "cache").glob("*/ecc/*/.claude-plugin/plugin.json")):
        found.append(manifest.parent.parent)
    local = HERE.parent.parent / "ecc"
    if (local / ".claude-plugin" / "plugin.json").exists():
        found.append(local)
    return found


# ------------------------------------------------------------------ route
def route(task, limit=12):
    skills = load("skills.json")
    rules = load("routing-rules.json")
    toks = tokens(task)
    tl = task.lower()
    matched_routes = []
    for r in rules["routes"]:
        score = sum(3 for t in r.get("triggers", []) if t in tl)
        score += sum(1 for t in r.get("triggers", []) for w in tokens(t) if w in toks)
        if score:
            matched_routes.append((score, r))
    matched_routes.sort(key=lambda x: -x[0])
    # IDF-weighted keyword match: rare words ("jwt") outweigh common ones ("use", "code").
    import math
    docs = [set(tokens(s["name"].replace("-", " ") + " " + s["description"] + " " + " ".join(s["topics"])))
            for s in skills]
    df = {}
    for d in docs:
        for w in d:
            df[w] = df.get(w, 0) + 1
    n = len(docs)
    route_skills = {x for _sc, r in matched_routes[:3] for x in [r.get("primary")] + [a["skill"] for a in r.get("alternatives", [])]}
    scored = []
    for s, d in zip(skills, docs):
        name_words = set(tokens(s["name"].replace("-", " ")))
        sc = 0.0
        for t in set(toks):
            if t in d:
                idf = math.log((n + 1) / (df[t] + 1)) + 1
                sc += idf * (2.5 if t in name_words else 1.0)
        if s["invocation"] in route_skills:
            sc += 2.0
        if sc:
            scored.append((round(sc, 1), s))
    scored.sort(key=lambda x: (-x[0], x[1]["invocation"]))
    return {"task": task, "routes": [{"score": sc, **r} for sc, r in matched_routes[:3]],
            "skills": [{"score": sc, "invocation": s["invocation"], "plugin": s["plugin"],
                        "description": s["description"][:200], "dependencies": s["dependencies"]}
                       for sc, s in scored[:limit]]}


def check_routes():
    skills = {s["invocation"] for s in load("skills.json")}
    rules = load("routing-rules.json")
    caps = load("capabilities.json")
    commands = {f"{c['plugin']}:/{c['name']}" for c in caps["commands"]}
    problems = []
    for r in rules["routes"]:
        names = [r.get("primary")] + [a["skill"] for a in r.get("alternatives", [])] + r.get("pipeline", []) \
            + r.get("cli_skills", []) + [x for x in r.get("always_with", []) if ":" in x]
        for n in names:
            if not n or n.startswith("(search)") or n.startswith("ecc agents"):
                continue
            if n.split(" --")[0] not in skills and n not in commands:
                problems.append(f"route {r['id']}: '{n}' is not a registered skill or command")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("route"); p.add_argument("task"); p.add_argument("--limit", type=int, default=12); p.add_argument("--json", action="store_true")
    p = sub.add_parser("doctor"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("list"); p.add_argument("--plugin"); p.add_argument("--topic")
    p = sub.add_parser("show"); p.add_argument("name")
    sub.add_parser("check-routes")
    a = ap.parse_args(argv)

    if a.cmd == "route":
        res = route(a.task, a.limit)
        if a.json:
            print(json.dumps(res, indent=1)); return 0
        print(f"Task: {a.task}\n")
        if res["routes"]:
            for r in res["routes"]:
                print(f"Route [{r['id']}]  primary: {r['primary']}")
                for alt in r.get("alternatives", [])[:6]:
                    print(f"    alt: {alt['skill']}  ({alt['when']})")
                if r.get("pipeline"):
                    print("    pipeline: " + " -> ".join(r["pipeline"]))
                if r.get("requires"):
                    print(f"    requires: {', '.join(r['requires'])}")
                print(f"    fallback: {r.get('fallback', '-')}")
                if r.get("skip_when"):
                    print(f"    skip when: {r['skip_when']}")
                print()
        else:
            print("No curated route matched; keyword matches below.\n")
        print("Keyword matches across all registered skills:")
        for s in res["skills"]:
            deps = f"  [needs: {', '.join(s['dependencies'])}]" if s["dependencies"] else ""
            print(f"  {s['score']:>3}  {s['invocation']}{deps}\n       {s['description']}")
        return 0
    if a.cmd == "doctor":
        res = doctor()
        if a.json:
            print(json.dumps(res, indent=1)); return 0
        for c in res:
            mark = "OK  " if c["ok"] else "MISS"
            print(f"[{mark}] {c['check']:<32} {c['detail']}")
            if not c["ok"]:
                print(f"        needed by: {c['needed_by']}\n        fix: {c['fix']}")
        return 0
    if a.cmd == "list":
        for s in load("skills.json"):
            if a.plugin and s["plugin"] != a.plugin:
                continue
            if a.topic and a.topic not in s["topics"]:
                continue
            print(f"{s['invocation']:<55} {s['description'][:90]}")
        return 0
    if a.cmd == "show":
        hits = [s for s in load("skills.json") if a.name in (s["invocation"], s["name"])]
        print(json.dumps(hits, indent=1) if hits else f"no skill named {a.name}")
        return 0 if hits else 1
    if a.cmd == "check-routes":
        probs = check_routes()
        for pr in probs:
            print(pr)
        print(f"{len(probs)} problem(s)")
        return 1 if probs else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
