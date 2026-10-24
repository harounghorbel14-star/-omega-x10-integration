# omega-x10-complete v4.0.0: independent verification

The files in this folder are the release as supplied: `omega-x10-v4.0.0.zip` (the skill),
`OMEGA-X10-V4-ENGINEERING-REPORT.md` and `OMEGA-X10-V4-TEST-EVIDENCE.zip`. They were checked on
2026-10-24 in a separate environment (Linux, Python 3.13.17, Node 22). Everything ran in scratch
copies of a fresh extraction, and the release files were not modified. Checksums are in `SHA256SUMS`.

## Upload readiness

`python3 tools/package_skill.py --verify omega-x10-v4.0.0.zip`: **OK**

- One top-level folder, `omega-x10-complete/`, with 108 entries.
- No symbolic links, no nested archives, no unsafe paths, and no excluded or secret-like content.
- `SKILL.md` frontmatter has `name: omega-x10-complete`, which matches the folder, and a description within the 1024-character limit.
- All 107 files listed in `FILE-SHA256.json` match their recorded hashes, and every file in the folder is listed.

## Report claims re-run

| Claim (engineering report) | Command | Result |
|---|---|---|
| Router fingerprint `5db7c254…`, workflow fingerprint `4675a25d…` | `omega.py fingerprint` | Identical |
| `doctor --offline`: 0 fatal | `omega.py doctor --offline` | 0 fatal; 6 optional items missing (external tools; the report lists 5) |
| Routes consistent | `omega.py check-routes` | 0 problems |
| blind4b 716/872 = 82.1% (CI 79–84) | `tests/routing_eval.py --set blind4b` | 716/872 = 82.1% (CI 79–84). Also identical: negation 100/112, ambiguity 40/46, macro F1 0.908, 0 unsupported-tool selections |
| Evaluator audit passed | `tests/eval_audit.py` (blind4b, fingerprint, 6 training files) | PASSED, 8/8 checks; independent re-judge 716/872 with 0 disagreements |
| Workflow gate 57/57 | `tests/workflow_gate.py` | 57/57; every criterion full |
| 138 unit tests OK | `python3 -m unittest discover -s tests -p "test_*.py"` | 138 OK **only with the Python `playwright` package installed** (see below) |
| Known defect: "update my GitHub profile README" routes wrong | `omega.py route` | Still reproduces (§8.4 of the report) |

## Finding: unit tests need the Python `playwright` package

Without the Python `playwright` package, the first run gave 2 failures and 1 error:

- `test_multilingual.ToolAvailability.test_named_tool_absent_is_limited_not_ready`
- `test_multilingual.ToolAvailability.test_present_but_unauthorised_connector_is_not_used`
- `test_orchestrate.Ledger.test_cli_end_to_end_partial_exit_code`

All three expect the image fallback to be LIMITED, but they got BLOCKED. Pillow was installed. The
cause is in `doctor`: it marks the image, video, 3D and browser fallbacks available only if
`playwright` can be imported (`omega.py`, around line 920), and the Node `playwright` CLI does not count.

After `pip install playwright` in a throwaway virtual environment, which installs no browsers, all 138 tests pass.

The report attributes the same symptom to Python 3.11/3.12 only (§6). It actually applies to any
interpreter without the package. The router's behaviour is correct, since BLOCKED is the honest
status. The report and install docs should list `playwright` as a test prerequisite.

## Content scan

- No credentials found in the skill or the evidence archive.
- The only email addresses are test fixtures (`*@example.test`).
- The only local paths are generic sandbox paths (`/home/claude`, `/home/me`, `/root/.bun`, `/root/.local`).
- The skill scripts contain no `shell=True`, `pickle`, `yaml.load`, `eval` or `exec`.
- The only URLs in the skill scripts are documentation links, plus the reachability check of `https://skills.sh` in `doctor`.

This was a pattern scan, not a full code review.

## Not verified

- Python 3.10/3.11/3.12/3.14, the task-app E2E/npm checks, the bandit/semgrep/pip-audit runs and the performance benchmark were not re-run. Their outputs are in the evidence archive.
- The report cites `OMEGA-X10-V4-NEW-BLIND-RESULTS.md` and `OMEGA-X10-V4-MIGRATION.md`, which are not part of this release folder.
- No upload to claude.ai was performed from this environment.

## Status

The routing gate (100% exact match) is **not passed**: 82.1%, as the report states. The multi-step
gate passes on its declared 57-scenario matrix. The skill ZIP is upload-ready.
