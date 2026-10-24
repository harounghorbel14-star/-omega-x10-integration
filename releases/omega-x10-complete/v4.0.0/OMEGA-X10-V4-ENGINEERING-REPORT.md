# OMEGA X10 v4.0.0 — Engineering Report

## Verdict: READY WITH LIMITATIONS

The two acceptance gates have different outcomes:

| Gate | Result |
|---|---|
| **Multi-step orchestration** | **PASSED**: 57/57 declared scenarios; every criterion at 100% |
| **Routing** (100% exact match on the final blind set) | **NOT PASSED**: 82.1% (716/872, 95% CI 79–84%) |

v4.0.0 is a large, statistically significant improvement over v3.0.0: 82.1% vs 50.3% on the same fresh blind set (paired p < 1e-6). It is safe to install: it runs offline, sends nothing out without consent, and every check below passes. It is not a 100% router, and the remaining defects are listed in §8.

| | |
|---|---|
| Package | `omega-x10-v4.0.0.zip` (byte-identical to `omega-x10-complete.skill`) |
| Release commit | `50a86ce`; router frozen at `bbea294` |
| Router fingerprint | `5db7c2547c297d7608f2dcc2f946e578c9fad0e02d812996e127b9dc73f5e64a` |
| Workflow fingerprint | `4675a25d7e26589e76d522f5ab6d2d5ee0a26e3fc3a8f97b69412287bf6558a3` |
| Release = evaluated build? | Yes. A fresh extraction of the zip has a byte-identical fingerprint file and reproduces 716/872 on blind4b. |

---

## 1. Inputs and baseline

### Inputs
- The v3.0.0 release, the Phase 3 report and the Phase 3 evidence were not re-uploaded for this phase.
- The session-local Phase 3 deliverables were used instead, copied read-only to `v4/inputs/` and identified by hash (`evidence/inputs.sha256`):
  - v3 zip `f4fa5487…`
  - report `dfaed99b…`
  - evidence `dd0788c0…`
- The original release and the installed skill were not modified. All work happened in a git working copy.

### Baseline reproduced on v3.0.0
| Check | Result |
|---|---|
| Unit tests | OK |
| dev | 143/143 |
| validation | 90/100 |
| Phase 3 blind | 85/125 |
| Phase 2 bench | 162/162 |

### Independent data showed the Phase 3 numbers were optimistic
The Phase 3 router had been tuned by the same author who wrote its test data. On new data written by isolated authors, v3 scored:

| Set | n | v3 exact match |
|---|---:|---:|
| dev4 | 400 | 58.2% |
| val4 | 300 | 58.3% |
| blind4a | 896 | 51.6% |
| blind4b | 872 | 50.3% |

---

## 2. What was built

### 2.1 Layered router (all offline, standard library at run time)
1. **Normalisation** (v3, extended): Unicode, Arabic orthography, Arabizi digits, contractions.
2. **Rule layer** (`omega_lang.py`, `lexicon.json`, `intents.json`): clause segmentation, scope analysis, verb–object rules, English phrase signals. Fixes per failure class are listed in §3.
3. **Contextual classifier** (`omega_classify.py`, `registry/classifier.json`, new).
   - One-vs-rest logistic regression with heads for 18 intents plus route / none / clarify.
   - Features: character 3–5-grams, words and bigrams, Arabizi skeletons, lexicon concepts and rule scores.
   - It sees only text that is neither negated nor a discussion question. It runs on the whole request and on each clause.
4. **Multi-intent and dependencies**: clause-level detection, time-clause ordering ("after you fix", "before deploying") and `depends_on` for hard dependencies.
5. **Confidence and clarification**: outcome heads, per-intent thresholds, and a clarify question listing the candidates.
6. **Fusion policy**, recorded in the model file: rule-backed routes, a stricter concrete verb–object override, rule fallback and a discussion veto. Every result reports both layers, the probabilities, the top features and the fusion step.
7. **Capability planning** (v3, unchanged): READY / FALLBACK / LIMITED / BLOCKED from the real session tools and authorisations.
8. **Optional external LLM/embedding adapter** (`omega_adapter.py`):
   - Off by default, and used only with `OMEGA_ADAPTER_CMD` plus `OMEGA_ADAPTER_CONSENT=granted`.
   - Advisory only. Any failure, timeout or invalid output means the offline result stands.
   - Tested with a fake adapter. No external model or service was called anywhere in this work.

### 2.2 Training and model selection (no tuning on blind data)
- Training data was development data only (n = 6,898):
  - dev, dev4, train4–7 (all written by isolated agents from the labelling guide);
  - the retired Phase 3 blind set;
  - the retired round-1 blind set (blind4a).
- val4 and the Phase 3 validation set were used for policy selection, then folded in.
- The trainer (`omega_train.py`, `tests/train_classifier.sh`) is deterministic (lbfgs, fixed folds). numpy and scikit-learn are needed only for retraining.
- Full-pipeline 5-fold cross-validation (`tests/cv_route.py`) on 6,736 labelled prompts: **77.9%**. Three fusion variants explored before C2 (rule additions, a lower multi-intent threshold, verb positions) did not improve it. The clause-level pass added +0.5 pt and was kept.

### 2.3 Orchestration (`omega_workflow.py`, new; `omega.py workflow`)
- **Spec per step**: id, action, capability, argv command, inputs (references to prerequisites' outputs), outputs with validators, prerequisites, retry policy (1–5), timeout, confirmation kind, evidence.
- **Pre-execution validation**: duplicate ids, unknown or self prerequisites, **cycles** (the path is printed), undeclared inputs, path traversal, absolute paths, shell-string commands, unbounded retries, bad timeouts, steps with no outputs or evidence.
- **Execution**:
  - subprocess without a shell, with timeouts and real exit codes;
  - bounded retries;
  - outputs validated (size, content, JSON) and hashed (sha256) in a ledger;
  - dependents of a failed step are SKIPPED while independent branches continue;
  - confirmation is required for destructive, external, financial, publishing and deployment steps;
  - secrets are redacted from the ledger.
- **Recovery**: resume after interruption, re-run of stale artifacts, refusal when the spec changed, and detection of corruption between steps.
- **Statuses**:
  - steps: READY / LIMITED / BLOCKED / RUNNING / COMPLETE / FAILED / SKIPPED;
  - runs: COMPLETE / PARTIAL / FAILED / BLOCKED (exit 0/3/4/5).
  - Exit code 0 alone never makes a step COMPLETE.
- The v3 ledger (`omega.py run …`) is unchanged.

---

## 3. Defect-to-fix matrix (Phase 3 failure classes)

There are 61 permanent regression cases (`tests/test_v4_regressions.py::FailureClasses`), with positive, negative, adversarial and paraphrase forms. All pass.

| Class | Fix | Cases | Spot checks on the release |
|---|---|---:|---|
| **A. Negation** | Descriptive negation is bug evidence. Also handled: 1st-person plural, lexical ("leave … alone", "sans toucher"), post-posed ("mouch lazma", "not needed") and "don't want". Penalties are clause-local. | 18 | "Images don't load" → debugging · "لا تصل الإشعارات" → debugging · "ma tetla3ch el page" → debugging · "el video mouch lazma, a3mel image" → image · "Do not create an image" / "Leave the existing file alone" / "ma ndeployiwech taw" → clarify (nothing is executed) |
| **B. Vocabulary** | Lexicon additions from dev4 error analysis, plus open-vocabulary character n-grams in the classifier | 6 | — |
| **C. Verb–object** | Causative "make X faster" → performance; V_CODE; "find why" → debugging; "find current info" → research | 8 | "make this endpoint faster" → performance · "export the document as PDF" → documents · "implement a search filter" → implementation · "write tests for the cart module" → tdd |
| **D. Multi-step** | Clause-level classification, time-clause ordering, request order with `depends_on`, and the DAG executor | 6 | blind4b multi-step: 72.8%; ordering when the step set is right: 91.9% |
| **E. Arabizi collisions** | Latin matches precede skeletons; short skeletons need a raw-spelling match | 5 | "bouton login ma ye5demch" → debugging · "boutique en ligne" / "tahni2a l omi" → clarify (no false route) · "scraping des prix" → browser-automation, not security |
| **F. Prefix/regex over-match** | `heberge*` and `profil(e)` boundaries; malformed patterns are skipped with a warning (fuzz-tested) | 4 | "liste des hébergeurs gratuits" → no deploy route · **"update my GitHub profile README" → performance (still wrong, see §8)** |
| **G. Discussion vs action** | Evaluative-question frame; discussion masks start at the marker's clause | 8 | "Is this tool worth using?", "Is this feature free?", "C'est vraiment utile ?", "هل هذا مجاني؟", "Explain how browser automation works" → none · "Use browser automation to log in and download the invoices" → browser-automation |
| **H. Clarify only when ambiguous** | Outcome heads plus rule-backed overrides | 6 | blind4b: unwarranted clarify 0.9%, missed clarify 10.0% |

---

## 4. Routing evaluation

### 4.1 Iteration budget and stop condition
The budget was declared as two blind rounds, each on a new set written after the candidate was frozen.

| Round | Candidate | Frozen at | Blind set | Result |
|---|---|---|---|---|
| 1 | C1 | `c696e5e` | blind4a (`006d79d`, n=896) | 77.1% |
| 2 | C2 | `bbea294` | blind4b (`439e0a4`, n=872) | **82.1%** |

- blind4a was retired to development data after round 1, and C2 was built from it.
- **Stop condition**: the budget is exhausted, and cross-validation had plateaued (77.2–77.9% across four fusion variants).
- No code or label changed after the blind4b evaluation.

### 4.2 Final blind result (C2 on blind4b, n = 872)

Full tables, per-intent P/R/F1 and every negation and ambiguity failure are in `OMEGA-X10-V4-NEW-BLIND-RESULTS.md`.

| Metric | v3.0.0 | C1 | **C2 (v4.0.0)** | Gate |
|---|---:|---:|---:|---|
| Exact match | 50.3% | 78.7% | **82.1%** (CI 79–84) | 100%: NOT PASSED |
| Strict (set + order) | 49.8% | 77.6% | 80.7% | — |
| Critical negation subset (n=112) | 50.0% | 87.5% | 89.3% | 100%: NOT PASSED |
| Ambiguity subset (n=46) | 50.0% | 89.1% | 87.0% | 100%: NOT PASSED |
| Unsupported-tool selections | 0 | 0 | **0** | 0: PASSED |
| Macro F1 | — | — | 0.908 | — |
| Multi-step category | — | — | 72.8% | — |
| False security / unwarranted clarify | — | — | 0.6% / 0.9% | — |

By language (C2):

| Language | Exact match |
|---|---:|
| Arabic | 78% |
| English | 79% |
| French | 79% |
| mixed | 90% |
| Tunisian Arabizi | 84% |

Paired tests: C2 vs C1 47 gained / 17 lost (p = 0.0002).

### 4.3 Evaluator audit (against false scores) — PASSED
`tests/eval_audit.py` checks:
- the denominator (872 frozen = 872 evaluated, no skips or duplicates);
- an independent re-judge (716 = 716, 0 disagreements);
- that gold labels and prompts are unchanged;
- that no blind prompt or id appears in the router sources or registry;
- that no blind prompt appears in the training files;
- that the labels are well-formed and all 8 categories are present;
- that there are zero unsupported-tool selections;
- that the router files match the fingerprint recorded at evaluation.

Also:
- A manual review of 40 sampled failures found about 3 debatable gold labels. None were changed.
- Hygiene removed 128 of 1,000 authored items as near-duplicates of development data before freezing.
- Single-run evaluation; nothing was retried.

---

## 5. Multi-step acceptance gate — PASSED

The gate is `tests/workflow_gate.py`, a declared matrix of 57 scenarios using deterministic fake tools. No deploys, publishing, credits or external accounts were used.

**Scenarios covered:**
- diagnose → fix → unit → integration → report;
- research → compare → synthesise → document;
- image → validate → video → inspect;
- implement → tests → run (flaky) → fix → rebuild;
- build → typecheck → lint (fail) → unit → E2E → package;
- analyse → identify → fix → rescan;
- independent artifacts → aggregate, including an aggregate with a failed branch;
- 2-, 3- and 10-step chains;
- missing optional and missing required tools;
- a failed first step, and a failed step next to an independent branch;
- timeout, exhausted retries, corrupted JSON, exit 0 without output, empty output, crash (137);
- deploy needing confirmation and deploy confirmed;
- publish/financial/destructive gates, limited fallback, secret redaction, missing final deliverable;
- 16 invalid specs (cycles, self-dependency, unknown prerequisite, duplicate id, path traversal, shell strings, unbounded retry …);
- 4 recovery cases;
- 10 routed multilingual workflows, including prohibited actions ("fix the bug but do not deploy", "a3melli logo w ba3d 7awlou video, ma tpublishich").

| Criterion | Result |
|---|---|
| Step extraction/ordering (routed workflows) | 10/10 |
| Prerequisite enforcement | 27/27 |
| Dependent prevention after failure | 27/27 |
| Cycle/invalid-dependency detection | 16/16 |
| Status reporting | 27/27 |
| Artifact integrity | 27/27 |
| No false COMPLETE | 27/27 |
| Happy-path end-to-end success | 10/10 |
| Recovery | 4/4 |

100% applies to this declared matrix only. Routing-side step extraction on free text is measured separately: 72.8% on the blind multi-step category.

---

## 6. Regression, security, performance, environments

### Regression
| Check | Result |
|---|---|
| Unit tests | 138, OK (from a fresh extraction of the zip) |
| Phase 2 bench | 162/162 |
| Workflow gate | 57/57 |
| `doctor --offline` | 0 fatal (the 5 optional items are external tools not present here) |
| skill-creator `quick_validate` | valid |
| Archive | exactly 1 SKILL.md, 0 nested archives, 0 unsafe paths, 108 entries |
| Capability inventory | every v3 file is still present (0 removed, 32 added); 23 intents; 20 routing rules; 426 catalogue skills; 333 AI-Engineer index entries; 13 Replica references; lexicon 64 concepts / 55 rules / 26 tools (v3: 63/54); v3 CLI (`route`, `run`, `doctor`, `list`, `show`, `check-routes`) unchanged |

### Security
| Scanner | Status | Result |
|---|---|---|
| bandit (skill scripts) | **PASS** | 0 high, 0 medium, 7 low (subprocess use with argv lists and timeouts) |
| semgrep, local rule set (12 rules: subprocess timeouts, shell, unsafe extraction, deserialisation, temp files, urlopen) | **PASS** (no high) | 2 warnings: `urlopen` in `doctor` with a fixed URL and timeout |
| semgrep registry rulesets | **NOT RUN** | semgrep.dev blocked by the network policy (proxy 403) |
| detect-secrets | **PASS** | 0 findings (corpora and hash manifests excluded) |
| pip-audit (trainer deps numpy/scipy/scikit-learn) | **PASS** | 0 known vulnerabilities; the run-time skill has no third-party deps |
| npm audit (task app regression) | **PASS** | 0 vulnerabilities |

Manual review:
- subprocess is argv-only with timeouts, and there is no `shell=True`;
- workflow paths must be relative and inside the workdir;
- extraction checks paths;
- no pickle or yaml.load;
- the ledger redacts secrets.

No high or critical findings needed fixing in C2.

### Performance (`tests/perf_bench.py`, Python 3.13, under tracemalloc)
| Measure | Result |
|---|---|
| Cold start | 1.9 s (loads the 6 MB model) |
| Per-request latency | p50 77 ms, p95 118 ms, max 156 ms |
| Peak traced memory | 82 MB |
| Pathological inputs | all finish; worst case 4.0 s for a 15,000-token "ma ma ma …" input; no catastrophic regex backtracking |

### Environments
| Environment | Status | Notes |
|---|---|---|
| Python 3.11, 3.12, 3.13 | **PASS** (138 tests each) | 3.11/3.12 first failed 3 tests because Pillow/Playwright were missing for those interpreters, so the fallback was correctly BLOCKED. After installing them, all passed (both logs kept). |
| Python 3.10, 3.14 | **NOT RUN** | not installed |
| Node | 22 only | |
| Task-app E2E | **PASS** (Chromium 4/4) | |
| Task-app checks | **PASS** | npm test 87/87, typecheck and lint clean |
| Firefox / WebKit E2E | **NOT RUN** | browsers not installed |

---

## 7. Files changed (v3.0.0 → v4.0.0; corpora excluded)

34 files, +3,285 / −111.

| Kind | Files |
|---|---|
| New code | `scripts/omega_classify.py`, `omega_train.py`, `omega_workflow.py`, `omega_adapter.py`, `registry/classifier.json` |
| Changed code | `scripts/omega.py`, `omega_lang.py`, `registry/intents.json`, `lexicon.json` |
| New tests | `test_v4_regressions.py`, `test_workflow.py`, `workflow_gate.py`, `cv_route.py`, `eval_audit.py`, `perf_bench.py`, `corpus_hygiene.py`, `train_classifier.sh`, `fixtures/fake_tool.py`, `fixtures/fake_adapter.py` |
| Changed tests | `routing_eval.py`, `test_multilingual.py`, `test_orchestrate.py` |
| Docs | `docs/ARCHITECTURE.md`, `INSTALL.md`, `INTENTS.md`, `MIGRATION.md`, `OPTIONAL-MODELS.md`, `TROUBLESHOOTING.md`, `WORKFLOWS.md`; `SKILL.md`, `CHANGELOG.md`, `MERGE-MANIFEST.json`, `FILE-SHA256.json` |
| New corpora (`tests/corpus/v4/`) | dev4, val4, train4–7, blind4a, blind4b, LABELING-GUIDE.md |

---

## 8. Limitations and remaining defects
1. **The routing gate is not passed.** About 1 in 5 requests is still routed imperfectly. On blind4b the 156 misses are:
   - 48 extra intents;
   - 45 missing intents (usually a later step);
   - 31 wrong intents;
   - 20 abstentions on a real request;
   - 9 routes where nothing was requested;
   - 3 confusions between clarify and none.
2. **Multi-step free text** is the weakest category (72.8%). Hard items reach only 57%.
3. **Negation is not perfect.** There are 12 strict failures in the negation subset, for example "Don't deploy. Just review the diff…" still adds deployment.
4. **Class F residue**: "update my GitHub profile README" routes to performance, because the verb sense of "profile" fires. It was found after the freeze, so it is not fixed in this release.
5. The `omega.py --help` text still describes the v3 two-layer router. The docs and SKILL.md are current. The help text is inside the fingerprinted file and was left unchanged after the freeze.
6. Long inputs (over about 10k tokens) can take seconds to route.
7. All corpora were written by language-model agents from one guide. Real user traffic may differ.
8. The 100% multi-step result covers the declared 57-scenario matrix, not every possible workflow.
9. This phase was interrupted twice by usage limits. Work resumed from the committed repository state, and every number above is backed by an evidence file produced by an actual run.

**Next remediation step:** more labelled multi-step and negation data, plus a dedicated step-extraction model, then a fresh blind round 3 on a new frozen candidate.

---

## 9. Install
```bash
unzip omega-x10-v4.0.0.zip -d <your-skills-dir>/       # or install the .zip / .skill in your skills UI
cd <your-skills-dir>/omega-x10-complete
python3 components/omega-engineering-x10/scripts/omega.py doctor --offline     # expect 0 fatal
python3 components/omega-engineering-x10/scripts/omega.py fingerprint          # expect router 5db7c254…
python3 components/omega-engineering-x10/scripts/omega.py route "fix the login crash then add tests"
```
Upgrade notes are in `OMEGA-X10-V4-MIGRATION.md`. Evidence for every claim is in `OMEGA-X10-V4-TEST-EVIDENCE.zip`.
