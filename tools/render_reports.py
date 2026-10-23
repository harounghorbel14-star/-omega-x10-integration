#!/usr/bin/env python3
"""Render audit/baseline-results.md and audit/validation-report.md from recorded results.

Inputs (all produced by real runs):
  audit/baseline-results.jsonl      tools/run-baselines.sh
  audit/structural-validation.json  tools/validate.py --syntax
  audit/functional-tests.json       functional checks, with evidence
  audit/plugin-details/*.txt        `claude plugin details` per plugin
  audit/unittest.txt                python3 -m unittest discover -s tests -v
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "audit"

# Analysis of each non-zero baseline result (investigated by hand; see notes).
BASELINE_NOTES = {
    "superpowers-version-bump": ("environment (confirmed: passes with mikefarah yq v4)", "Needs mikefarah yq v4 (`strenv`); this machine's /usr/bin/yq is the jq wrapper. With yq v4.44.3 (release binary, SHA-256 verified) first on PATH the test passes ('Version-bump tests passed'). Script under test "
                                 "(scripts/bump-version.sh) is release tooling, not a skill."),
    "mattpocock-validate": ("environment/tool-version", "`--strict` turns two warnings into errors: root CLAUDE.md not loaded, and "
                            "missing plugin icon (a newer validator rule). No errors without --strict; the OMEGA copy validates."),
    "ecc-npm-test": ("2/8879 fail: both environmental (confirmed)", "8877/8879 tests passed across 428 files. "
                     "(1) hooks/hooks.test.js 'observe.sh falls back to legacy output fields': with this harness's CLAUDE_*/AI_AGENT "
                     "env vars unset the file passes 258/258 (observe.sh skips non-CLI entrypoints by design). "
                     "(2) scripts/install-sh.test.js 'leader exit cannot hide an owned descendant retaining captured pipes' "
                     "('owned fixture process survived cleanup'): the descendant IS killed (State Z, zombie, 500 ms after SIGKILL) "
                     "but this sandbox's PID 1 (`process_api`) never reaps orphans, and the test's kill(pid, 0) succeeds on a "
                     "zombie. Under a reaping subreaper (tools/subreaper.py, equivalent to tini / docker --init) the file passes "
                     "19/19. ECC's cleanup safeguards were not changed. Requirement elsewhere: an init that reaps zombies."),
    "claude-mem-bun-test": ("71/10120 fail: 67 environmental + 4 upstream build skew (all confirmed)", "9753 pass, 71 fail, 296 skip "
                            "across 977 files. 61: tree-sitter CLI binary missing because install scripts were skipped "
                            "(--ignore-scripts); fixed by upstream's trustedDependencies install. Remaining 10, each reproduced: "
                            "4 launcher tests (ensure-launcher x3, launcher --version) expect LAUNCHER_PROTOCOL 2 from src/ but the "
                            "committed plugin/scripts artifacts were last rebuilt 2026-10-20, before the bump in 8eb3dabc "
                            "(2026-10-22); after upstream `npm run build`: 96/96 launcher tests pass. Upstream main == pinned commit, "
                            "and published npm 15.0.1 ships an ensure-launcher.cjs byte-identical to the integrated copy, so shipped "
                            "artifacts are self-consistent. 1 plugin-distribution test needs the git-ignored dist/ build output "
                            "(passes after build). 2 observation semantic-row-filter tests take 7.1 s and 7.9 s on this 4-core machine, "
                            "over bun's 5 s default (pass with --timeout 60000). 1 Chroma connection-failure test and 1 Codex "
                            "PreToolUse transport test fail only under full-suite load (pass alone at the default timeout). "
                            "1 processesStillUsingArm test: the container locale is POSIX, so pgrep cannot match the emoji in its "
                            "regex (passes with LC_ALL=C.UTF-8)."),
    "graphify-pytest": ("25/8471 fail: all environmental (confirmed)", "8246 passed, 25 failed, 200 skipped. All three groups confirmed: "
                        "test_security.py (7) needs DNS for example.com, blocked by this environment's network policy; "
                        "test_skillgen.py (11) reads the v8 baseline from git history, absent from the shallow clone; after "
                        "`git fetch --unshallow` it passes 71/71; test_ext_tagged_id_clash.py (7) needs the optional `sql` "
                        "extra (tree-sitter-sql); with `uv run --extra sql` it passes 14/14."),
    "vercel-skills-vitest": ("4/978 fail: all environmental (confirmed)", "3 detect-agent tests read AI_AGENT/CLAUDE_CODE_* env "
                             "vars set by this harness. 1 Notion test: @clack/prompts isUnicodeSupported() returns false when "
                             "TERM=linux (this container's TERM), so it draws '|' instead of the box character the test strips. "
                             "With the env vars unset and TERM=xterm-256color: 978/978 pass."),
}


def baseline_md():
    p = A / "baseline-results.jsonl"
    rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []
    out = ["# Baseline results (upstream test suites)", "",
           "Each source's own tests, run by `tools/run-baselines.sh` on a disposable copy of the sources "
           "(dependency installs with `--ignore-scripts`). These establish what already passes or fails upstream, "
           "so integration regressions can be told apart from baseline problems. Logs: `audit/baseline-logs/` "
           "(not committed; regenerate with the script).", "",
           "| Suite | Repository dir | Command | Exit | Seconds | Classification |", "|---|---|---|---|---|---|"]
    for r in rows:
        cls = "pass" if r["exit"] == 0 else ("timeout" if r.get("timed_out") else BASELINE_NOTES.get(r["name"], ("FAIL (see tail)", ""))[0])
        out.append(f"| {r['name']} | {r['cwd']} | `{r['command'][:90]}` | {r['exit']} | {r['seconds']} | {cls} |")
    passed = sum(1 for r in rows if r["exit"] == 0)
    out += ["", f"**{passed}/{len(rows)} suites exit 0.**", ""]
    for r in rows:
        if r["exit"] != 0:
            note = BASELINE_NOTES.get(r["name"], ("", "Not yet analysed."))[1]
            out += [f"## {r['name']} (exit {r['exit']})", "", note, "", "```", *[t[:200] for t in r["tail"][-10:]], "```", ""]
    cp = A / "corrected" / "baseline-results.jsonl"
    crow = [json.loads(line) for line in cp.read_text().splitlines() if line.strip()] if cp.exists() else []
    if crow:
        out += ["## Corrected-environment run", "",
                "`CORRECTED_ENV=1 tools/run-baselines.sh <fresh copy> audit/corrected/baseline-results.jsonl` applies only the "
                "requirements confirmed above: agent env vars unset, TERM=xterm-256color, LC_ALL=C.UTF-8, a reaping subreaper, "
                "claude-mem trusted install scripts + upstream `npm run build` + `--timeout 30000`, Graphify full git history + "
                "`--extra sql`. Network policy, yq and --strict validator rules are unchanged.", "",
                "| Suite | Exit (default run) | Exit (corrected) | Tail |", "|---|---|---|---|"]
        dflt = {r["name"]: r["exit"] for r in rows}
        for r in crow:
            import re as _re
            clean = [_re.sub(r"\x1b\[[0-9;]*m", "", t).strip() for t in r["tail"][-3:]]
            tail = " / ".join(t[:90] for t in clean if t)
            out.append(f"| {r['name']} | {dflt.get(r['name'], '-')} | {r['exit']} | {tail.replace('|', '/')} |")
        out += ["", f"**Corrected run: {sum(1 for r in crow if r['exit'] == 0)}/{len(crow)} suites exit 0.**", ""]
    out += ["## Not run, with reason", "",
            "- superpowers `tests/claude-code`, `tests/explicit-skill-requests`, `tests/opencode`, `tests/kimi`, "
            "`tests/antigravity`, `tests/devin`, `tests/hermes`, `tests/pi`: drive live model sessions or other harnesses "
            "(paid, non-deterministic, or not installed).",
            "- superpowers `tests/brainstorm-server`: needs its own npm install and a browser; the brainstorming skill's "
            "optional visual server is not used by OMEGA routing.",
            "- ECC `test:plugin-setup-platform` (docker), `test:python` (needs ECC's Python test deps).",
            "- agent-browser Rust tests (`cargo test`): the CLI is consumed as a published binary; its launcher test ran.",
            "- claude-mem evals and docker e2e; Graphify benchmarks.",
            "- VibeSec: no tests upstream (single Markdown skill).", ""]
    (A / "baseline-results.md").write_text("\n".join(out) + "\n")
    return rows


def validation_md(baseline_rows):
    sv = json.loads((A / "structural-validation.json").read_text())
    ft = json.loads((A / "functional-tests.json").read_text())
    ut = (A / "unittest.txt").read_text() if (A / "unittest.txt").exists() else ""
    rec = (A / "reconciliation.md").read_text()
    out = ["# Validation report", "",
           "Everything below was executed in this environment; nothing is inferred. Commands are given so each "
           "result can be reproduced.", "",
           "## 1. Structural validation", "", "Command: `python3 tools/validate.py --syntax`", "",
           "| Check | Status | Detail |", "|---|---|---|"]
    for r in sv:
        out.append(f"| {r['check']} | {r['status']} | {r['detail']} |")
    notes = [r for r in sv if r["examples"] and r["status"] == "PASS"]
    if notes:
        out += ["", "Notes on passing checks with examples:", ""]
        for r in notes:
            out.append(f"- **{r['check']}**: " + "; ".join(r["examples"][:6]))
    out += ["", "References already unresolved upstream (placeholders such as `0001-use-nextjs.md`, or files a skill "
            "writes into the user's project such as `assets/design-tokens.json`) are listed in "
            "`audit/upstream-unresolved-references.txt`.", "",
            "## 2. Claude Code plugin validation", "",
            "Command: `claude plugin validate plugins/<p>` (Claude Code 2.1.309) and `claude plugin validate .`", "",
            "- 13 listed plugins: pass (ecc, mattpocock-skills, ui-ux-pro-max pass with upstream warnings: root CLAUDE.md "
            "not loaded / unknown field `id`; all plugins lack an icon, a directory-listing warning). Recorded output: "
            "`audit/claude-plugin-validate.txt`.",
            "- Marketplace: pass after removing claude-mem and claude-mem-cowork, which fail because names starting with "
            "`claude-` are reserved. The upstream claude-mem repository fails the same check (baseline, not a regression).",
            "", "## 3. Isolated install and functional tests", "",
            "Throwaway `CLAUDE_CONFIG_DIR`, scratch npm/uv prefixes and a scratch `HOME` for claude-mem.", "",
            "| Test | Result | Evidence |", "|---|---|---|"]
    for t in ft:
        out.append(f"| {t['test']} | {t['result']} | {t['evidence']} |")
    out += ["", "## 4. Loaded components (from `claude plugin details`)", "", "| Plugin | Inventory | Always-on tokens |", "|---|---|---|"]
    for f in sorted((A / "plugin-details").glob("*.txt")):
        txt = f.read_text()
        inv = " ".join(l.strip().split("  ")[0] for l in txt.splitlines() if l.startswith(("  Skills", "  Agents", "  Hooks", "  MCP")))
        tok = next((l.split("~")[1].split(" ")[0] for l in txt.splitlines() if "Always-on:" in l), "?")
        out.append(f"| {f.stem} | {inv} | ~{tok} |")
    out += ["", "## 5. Unit tests", "", "Command: `python3 -m unittest discover -s tests -v`", "", "```", *ut.strip().splitlines()[-25:], "```", "",
            "## 6. Baseline comparison", "",
            f"Default run: {sum(1 for r in baseline_rows if r['exit'] == 0)}/{len(baseline_rows)} upstream suites exit 0. Every "
            "failing test was reproduced individually and its cause confirmed (see `audit/baseline-results.md`, including the "
            "corrected-environment run). No failure involves a file changed by the integration: apart from two recorded "
            "transforms (VibeSec frontmatter name, anti-pattern-czar command path), every copied file is byte-identical to "
            "the pinned source, so upstream outcomes carry over to the integrated copies.", "",
            "## 7. Disposition reconciliation", "", rec.split("\n", 2)[2] if rec.count("\n") > 2 else rec, "",
            "## 8. Open items", "", "Rendered from `audit/open-items.json`; the same list is in `audit/unresolved-items.md`.", ""]
    oi = json.loads((A / "open-items.json").read_text())
    fx = oi.get("fixed_in_release_gate", [])
    if fx:
        out += [f"**Fixed in the release gate ({len(fx)})**", "", "| Id | Issue | Fix | Regression test |", "|---|---|---|---|"]
        out += [f"| {f['id']} | {f['item']} | {f['fix']} | {f['regression_test']} |" for f in fx]
        out.append("")
    for key, title in (("implementation_blockers", "Implementation blockers"), ("environment_restricted", "Environment-restricted"),
                       ("upstream_limitations", "Upstream limitations"), ("not_verified", "Not verified")):
        items = oi.get(key, [])
        out.append(f"**{title} ({len(items)})**" + (": none." if not items else ""))
        for it in items:
            out.append(f"- {it['id']}: {it['item']}")
        out.append("")
    out += ["Routing is keyword/curated and is a recommendation aid; final skill choice stays with the model, as shown in "
            "the live routing tests.", ""]
    (A / "validation-report.md").write_text("\n".join(out) + "\n")


def completeness_md(baseline_rows):
    from collections import Counter
    comps = json.loads((ROOT / "registry/components.json").read_text())
    man = json.loads((A / "source-manifest.json").read_text())
    cp = A / "corrected" / "baseline-results.jsonl"
    corr = {}
    if cp.exists():
        for line in cp.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                corr[r["name"]] = r["exit"]
    suite_repo = {r["cwd"]: [] for r in baseline_rows}
    for r in baseline_rows:
        d = "pass" if r["exit"] == 0 else f"exit {r['exit']}"
        c = corr.get(r["name"])
        c = "" if c is None else (" / corrected pass" if c == 0 else f" / corrected exit {c}")
        suite_repo[r["cwd"]].append(f"{r['name']}={d}{c}")
    out = ["# Final completeness audit", "",
           "Computed from `registry/components.json` (every component of every source) and the recorded test runs.", "",
           "| Repository | Inspected | Commit | Skills found | Other components | Preserved | Merged | Adapted | Excluded | External runtime | Blocked/unresolved | Upstream tests |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    tot = Counter()
    for m in man:
        cs = [c for c in comps if c["source_repository"] == m["repo"]]
        d = Counter(c["disposition"] for c in cs)
        sk = sum(1 for c in cs if c["item_type"] == "skill")
        tests = "; ".join(suite_repo.get(m["dir"], [])) or "none upstream"
        out.append(f"| {m['repo']} | {m['status']} | `{m['commit'][:12]}` | {sk} | {len(cs) - sk} | {d['preserved']} | "
                   f"{d['merged-with-traceability']} | {d['adapted-with-traceability']} | {d['excluded-with-justification']} | "
                   f"{d['retained-as-external-runtime']} | {d['blocked-uninspected'] + d['unclassified']} | {tests} |")
        tot.update(d); tot["skills"] += sk; tot["all"] += len(cs)
    out.append(f"| **Total** | 10/10 | | {tot['skills']} | {tot['all'] - tot['skills']} | {tot['preserved']} | "
               f"{tot['merged-with-traceability']} | {tot['adapted-with-traceability']} | {tot['excluded-with-justification']} | "
               f"{tot['retained-as-external-runtime']} | {tot['blocked-uninspected'] + tot['unclassified']} | |")
    loaded = sum(1 for c in comps if c.get("loaded_by_claude_code"))
    out += ["", f"Skills loadable in Claude Code: **{loaded}** (+9 agent-browser skills served by its CLI, +1 omega-core router). "
            "386 come from the 11 source plugins in the OMEGA marketplace; 30 are claude-mem / claude-mem-cowork skills, "
            "loadable once claude-mem is installed from its upstream marketplace (identical files are kept in plugins/). "
            "The remaining skill files are harness mirrors, translations or per-platform variants, each mapped to its "
            "canonical loaded skill or excluded with a reason (`audit/exclusions.md`).", "",
            "## Specific checks", "",
            "| Check | Result | How verified |", "|---|---|---|",
            "| Missing nested skills | none | every `SKILL.md` (and graphify `skill*.md`) in `git ls-files` is a registry component (`tests/test_omega.py::test_every_source_skill_is_accounted_for`) |",
            "| Unexamined directories | none | every tracked file matched a rule; build fails otherwise (`validate.py` classified) |",
            "| Uncopied resources/data | only by recorded rule | `audit/file-map.json` gives each file a destination or reason |",
            "| Lost unique behaviours | none found | unique mirror-only skills reviewed individually (ecc-council, ecc-conventions, project-guidelines-example x2, 3 claude-mem harness installers) |",
            "| Broken paths | 0 introduced | `validate.py` references check, comparing against source |",
            "| Silent truncation | none | byte-for-byte integrity of 3,828 files against a fresh fetch of the pinned commits |",
            "| Unavailable integrations | recorded | claude-mem/cowork unlisted (name reservation); skills.sh blocked here; see validation-report section 8 |",
            "| Incorrect install/execution claims | guarded | every claim in docs/INSTALL.md was run in the isolated config; unrun items are marked NOT RUN |",
            "| Duplicate capabilities introduced | none | no skill was duplicated into a second plugin; overlaps across sources are upstream overlaps, listed in `audit/merge-map.json` overlap_groups with routing precedence |",
            "| Dependencies made mandatory | none | each runtime is needed only by its plugin; plugins install independently; MCP servers of the design stack moved to optional/ |",
            ""]
    (A / "completeness-audit.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    rows = baseline_md()
    validation_md(rows)
    completeness_md(rows)
    print("wrote audit/baseline-results.md and audit/validation-report.md")
