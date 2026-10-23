"""Tests for the OMEGA-ENGINEERING X10 router and registry.  Run: python3 -m unittest discover -s tests -v"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "plugins" / "omega-core"
sys.path.insert(0, str(CORE / "scripts"))
import omega  # noqa: E402


def load(p):
    return json.loads((ROOT / p).read_text())


class RouteTests(unittest.TestCase):
    CASES = [
        ("take a screenshot of example.com and fill the login form", "browser-automation", "agent-browser:agent-browser"),
        ("grill me on this plan, the requirements are unclear", "requirements-discovery", "mattpocock-skills:grill-me"),
        ("find a skill for writing changelogs", "skill-discovery", None),
        ("what did we do last session on the auth bug, search memory", "session-memory", "claude-mem:mem-search"),
        ("audit my login endpoint for sql injection and xss", "security", "vibesec:vibesec"),
        ("add a password reset flow to our express app", "security", "vibesec:vibesec"),
        ("design a landing page with a calm color palette and good typography", "ui-ux-design", "ui-ux-pro-max:ui-ux-pro-max"),
        ("build a knowledge graph of this codebase architecture", "repository-architecture", "graphify:graphify"),
        ("clone this app: reverse engineer notion", "app-replication", "replica-skill:replica-recon"),
        ("write an implementation plan for a multi-step feature", "planning", "superpowers:writing-plans"),
        ("there is a flaky failing test, debug it", "debugging", "superpowers:systematic-debugging"),
        ("tdd: write tests first for the parser", "tdd", "superpowers:test-driven-development"),
        ("review my PR diff", "code-review", "superpowers:requesting-code-review"),
        ("create a git worktree for this branch", "git-workflow", "superpowers:using-git-worktrees"),
    ]

    def test_curated_routes(self):
        for task, route_id, primary in self.CASES:
            with self.subTest(task=task):
                res = omega.route(task)
                ids = [r["id"] for r in res["routes"]]
                self.assertIn(route_id, ids, f"{task!r} -> {ids}")
                if primary:
                    r = next(r for r in res["routes"] if r["id"] == route_id)
                    self.assertEqual(r["primary"], primary)

    def test_keyword_search_reaches_long_tail(self):
        # skills not named by any curated route must still be reachable through search
        for task, expect in [("django celery background task", "ecc:django-celery"),
                             ("homelab wireguard vpn", "ecc:homelab-wireguard-vpn"),
                             ("shoehorn as assertions in tests", "mattpocock-skills-extras:migrate-to-shoehorn"),
                             ("electron desktop app automation", "agent-browser skills get electron")]:
            with self.subTest(task=task):
                top = [s["invocation"] for s in omega.route(task, limit=5)["skills"]]
                self.assertIn(expect, top)

    def test_check_routes_clean(self):
        self.assertEqual(omega.check_routes(), [])

    def test_doctor_reports_every_check_with_fix(self):
        for c in omega.doctor():
            self.assertIn("ok", c)
            if not c["ok"]:
                self.assertTrue(c["fix"], c)

    def test_cli_exit_codes(self):
        py = sys.executable
        script = str(CORE / "scripts" / "omega.py")
        self.assertEqual(subprocess.run([py, script, "check-routes"], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([py, script, "show", "superpowers:brainstorming"], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([py, script, "show", "no-such-skill"], capture_output=True).returncode, 1)
        out = subprocess.run([py, script, "route", "debug a crash", "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(out.stdout)["task"], "debug a crash")


class DoctorRegressionTests(unittest.TestCase):
    """Regressions for gaps found by live runtime checks (Phase 3)."""

    def test_unreachable_host_is_reported_not_swallowed(self):
        # `npx skills find` turns network errors into "No skills found"; the doctor must not.
        ok, detail = omega._reachable("http://127.0.0.1:9/api/search?q=x")
        self.assertFalse(ok)
        self.assertIn("unreachable", detail)

    def test_doctor_has_skills_sh_check_with_fix(self):
        names = {c["check"]: c for c in omega.doctor()}
        self.assertIn("skills.sh reachable", names)
        c = names["skills.sh reachable"]
        if not c["ok"]:
            self.assertIn("No skills found", c["fix"])

    def test_ecc_missing_runtime_deps_detected(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as cfg:
            plugin = Path(cfg) / "plugins" / "cache" / "omega-engineering-x10" / "ecc" / "2.2.3"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin" / "plugin.json").write_text('{"name": "ecc"}')
            old = os.environ.get("CLAUDE_CONFIG_DIR")
            os.environ["CLAUDE_CONFIG_DIR"] = cfg
            try:
                checks = {c["check"]: c for c in omega.doctor()}
                key = f"ecc runtime deps ({plugin})"
                self.assertIn(key, checks)
                self.assertFalse(checks[key]["ok"])
                self.assertIn("install-plugin-deps.sh", checks[key]["fix"])
                # regression (clean git install): the suggested helper must exist next to omega.py, since
                # an installed omega-core has no repository scripts/ directory
                helper = checks[key]["fix"].split()[0]
                self.assertTrue(Path(helper).is_file(), helper)
                (plugin / "node_modules" / "js-yaml").mkdir(parents=True)
                self.assertTrue({c["check"]: c for c in omega.doctor()}[key]["ok"])
            finally:
                if old is None:
                    os.environ.pop("CLAUDE_CONFIG_DIR")
                else:
                    os.environ["CLAUDE_CONFIG_DIR"] = old


class BuildDeterminismTest(unittest.TestCase):
    """Regression: skill directories used to be ordered from a Python set, so outputs changed with
    PYTHONHASHSEED. A rebuild under another seed must reproduce the registry byte for byte."""

    def test_rebuild_with_different_hash_seed_is_identical(self):
        import hashlib
        import os
        # transforms.json/merge-map.json: regression for --no-copy builds dropping the transform records
        files = ["registry/components.json", "registry/skills.json", "audit/merge-map.json", "audit/file-map.json",
                 "audit/transforms.json"]
        before = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
        env = dict(os.environ, PYTHONHASHSEED="424242")
        r = subprocess.run([sys.executable, str(ROOT / "tools/build.py"), "--no-copy"], capture_output=True, text=True,
                           env=env, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
        self.assertEqual(before, after)
        self.assertEqual(len(json.loads((ROOT / "audit/transforms.json").read_text())), 2)


class SubreaperTests(unittest.TestCase):
    """tools/subreaper.py: reaps orphaned zombies, and returns when the command exits even if a daemon
    it started is still running (regression: it used to wait for every descendant until the timeout)."""

    SCRIPT = str(ROOT / "tools" / "subreaper.py")

    def test_returns_command_status_without_waiting_for_daemons(self):
        import time
        start = time.monotonic()
        # the daemon must not hold our pipes open, or run() would wait for EOF rather than for the subreaper
        r = subprocess.run([sys.executable, self.SCRIPT, "bash", "-c", "sleep 30 >/dev/null 2>&1 </dev/null & exit 3"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        self.assertEqual(r.returncode, 3)
        self.assertLess(time.monotonic() - start, 10)

    def test_killed_orphan_is_reaped(self):
        # Positive check only: whether an orphan would stay a zombie WITHOUT the subreaper depends on the
        # host's process tree (it did under node in this sandbox, see audit/baseline-results.md).
        probe = (
            "import os, signal, subprocess, sys, time\n"
            "pid = int(subprocess.run(['bash', '-c', 'sleep 30 >/dev/null 2>&1 & echo $!'], capture_output=True, text=True).stdout)\n"
            "os.kill(pid, signal.SIGKILL)\n"
            "for _ in range(50):\n"
            "    try: os.kill(pid, 0)\n"
            "    except ProcessLookupError: sys.exit(0)\n"
            "    time.sleep(0.05)\n"
            "sys.exit(1)\n")
        r = subprocess.run([sys.executable, self.SCRIPT, sys.executable, "-c", probe], timeout=30)
        self.assertEqual(r.returncode, 0, "orphan stayed a zombie: subreaper did not reap it")


class RegistryTests(unittest.TestCase):
    def test_core_registry_matches_root_registry(self):
        for n in ("skills.json", "capabilities.json", "routing-rules.json"):
            self.assertEqual((ROOT / "registry" / n).read_bytes(), (CORE / "registry" / n).read_bytes(), n)

    def test_every_component_has_valid_disposition(self):
        valid = {"preserved", "merged-with-traceability", "adapted-with-traceability", "excluded-with-justification",
                 "retained-as-external-runtime", "blocked-uninspected"}
        comps = load("registry/components.json")
        self.assertGreater(len(comps), 3000)
        bad = [c["id"] for c in comps if c["disposition"] not in valid]
        self.assertEqual(bad, [])

    def test_non_preserved_items_carry_a_reason(self):
        for c in load("registry/components.json"):
            if c["disposition"] in ("excluded-with-justification", "retained-as-external-runtime", "merged-with-traceability"):
                with self.subTest(id=c["id"]):
                    self.assertTrue(c.get("reason") or c.get("notes") or c.get("merged_into"), c["id"])

    def test_every_source_skill_is_accounted_for(self):
        comps = load("registry/components.json")
        skill_paths = {(c["source_repository"], c["source_path"]) for c in comps if c["item_type"] == "skill"}
        fmap = load("audit/file-map.json")
        sk_files = {(f["repo"], f["path"]) for f in fmap if not f.get("extra") and (
            f["path"].endswith("/SKILL.md") or f["path"] == "SKILL.md" or re.match(r"graphify/skill(-[a-z]+)?\.md$", f["path"]))}
        self.assertEqual(sk_files - skill_paths, set())

    def test_invocation_namespace_is_plugin_manifest_name(self):
        for s in load("registry/skills.json"):
            if ":" not in s["invocation"]:
                continue
            name = json.loads((ROOT / "plugins" / s["plugin"] / ".claude-plugin/plugin.json").read_text())["name"]
            self.assertEqual(s["invocation"].split(":")[0], name, s["invocation"])

    def test_loaded_skill_counts_match_claude_plugin_details(self):
        # audit/plugin-details/*.txt is the recorded output of `claude plugin details` from the isolated install
        details = ROOT / "audit" / "plugin-details"
        if not details.exists():
            self.skipTest("no recorded plugin details")
        skills = load("registry/skills.json")
        caps = load("registry/capabilities.json")
        for f in details.glob("*.txt"):
            m = re.search(r"^  Skills \((\d+)\)", f.read_text(), re.M)
            if not m:
                continue
            plugin_dir = next((p.name for p in (ROOT / "plugins").iterdir() if json.loads(
                (p / ".claude-plugin/plugin.json").read_text())["name"] == f.stem), None)
            n_sk = sum(1 for s in skills if s["plugin"] == plugin_dir and not s.get("served_by_cli"))
            n_cmd = sum(1 for c in caps["commands"] if c["plugin"] == plugin_dir)
            with self.subTest(plugin=f.stem):
                self.assertEqual(int(m.group(1)), n_sk + n_cmd, f"{f.stem}: claude sees {m.group(1)}, registry {n_sk}+{n_cmd}")


if __name__ == "__main__":
    unittest.main()
