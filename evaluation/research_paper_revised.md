# AICAR: An Agentic AI Framework for Code Intent Analysis, Scope Creep Detection, and Software Project Recovery

**Submission candidate - evidence-based draft, 22 October 2026**

**Author(s):** [Insert verified author names and affiliations]

## Abstract

Understanding why code was introduced, whether a change matches an intended task, and whether an inactive project is feasible to resume are related software-maintenance problems. This paper presents AICAR (Agentic Intent, Creep, and Recovery), a prototype that combines Git repository extraction, a React dashboard, a FastAPI service, a LangGraph workflow, optional Gemini calls, and SQLite persistence. Its workflow extracts recent commits, selected diffs and file histories; invokes intent, optional scope, and recovery agents; computes a heuristic health score; and returns a commit-to-file graph and report. These capabilities are not equally mature: offline intent uses commit-message evidence, scope analysis receives changed-file names rather than per-hunk code evidence, and recovery and health estimates are uncalibrated. A separate pinned-revision evaluation pipeline exists, but its current dataset has 50 candidate cases and no human-labelled cases. An archived offline smoke run completed 150 method executions with no scored cases. The current software test rerun passed 47 Python tests and 10 frontend tests; these results establish selected implementation behavior, not research accuracy. The paper therefore reports an implemented prototype and its verification limits, not a validated comparative study.

**Index Terms** - software repository analysis, code intent, scope analysis, project recovery, multi-agent systems, software maintenance.

## I. Introduction

Software repositories preserve commits, diffs, and file histories that can help developers understand how a codebase evolved. These records do not by themselves establish the original rationale for a change, whether every part of a patch was requested, or what work would be needed to resume an inactive project. AICAR explores a single user-facing workflow for these three questions: intent reconstruction, scope review, and project recovery.

The project addresses a practical integration problem rather than a demonstrated research-performance gap. Its prototype accepts GitHub repository URLs, extracts repository evidence, produces agent outputs and heuristic measures, and presents results through a web interface. Optional GitHub OAuth supports private-repository access. Optional Gemini use is controlled by configuration. Without live model use, the implemented agents provide fallbacks that are intentionally limited.

This paper distinguishes executable application behavior from evaluation infrastructure and from research hypotheses. The active evaluation dataset contains candidate cases but no human labels, so there is no basis for reporting predictive accuracy or comparing AICAR with baselines. The paper makes no claim that the prototype outperforms Git tools or a single-prompt model.

The implementation contributions reported here are:

1. An end-to-end prototype linking repository extraction, a conditional multi-agent workflow, SQLite result persistence, and a dashboard.
2. A commit-to-file graph and repository comparison interface backed by transparent, code-defined heuristic measures.
3. A separate evaluation pipeline that can prepare pinned Git evidence, run offline baselines, validate prediction schemas, calculate task metrics when labels exist, and refuse to score missing ground truth.

These are software artifacts and engineering contributions. The current implementation does not establish that the agents reliably infer developer intent, identify scope creep, or rank recovery candidates.

## II. Background and Related Work

Project abandonment is not equivalent to permanent project failure. Avelino et al. studied 1,932 popular GitHub projects and reported that 315 (16%) were abandoned by their core maintainers; 128 of those abandoned projects (41%) survived after new core developers assumed maintenance [1]. This finding motivates treating recovery as a question that needs evidence beyond inactivity alone. It does not validate AICAR's health score or recovery agent.

Commit untangling and collaborative agent work are adjacent research areas. Atomizer studies multi-agent, intent-driven composite-commit untangling [2]. ColaUntangle studies explicit and implicit dependency reasoning for commit untangling [3]. These systems address neighboring repository-comprehension problems; they are not components of AICAR and this paper does not claim to reproduce their methods or results. A related preprint on vulnerability-inducing commit detection is also relevant to multi-stage code-change analysis [4], but its complete bibliographic metadata should be checked against the final arXiv record before publication.

The initial draft also named Barnett et al. (2015), Dias et al. (2015), Dhaouadi et al. (2023), and Fan et al. (2024) without complete bibliographic entries. Those citations are not used here because the supplied details were insufficient to identify and verify the intended works. A systematic literature review is outside the current evaluation.

## III. System Overview

AICAR is a locally runnable web application with a separate research-evaluation subsystem. Its application path and evaluation path must not be conflated:

- **Application path:** a user request enters the React frontend, is proxied to FastAPI during development, retrieves a repository, runs the LangGraph workflow, computes heuristics and graph data, persists a full-analysis result, and returns JSON for display.
- **Evaluation path:** pinned revisions are converted to immutable evidence packs for offline baseline and agent execution. This path supports claim-resolution checks and metrics, but it does not benchmark the dashboard's complete LangGraph request path.

### A. Implemented Application Flow

```text
User
 |
 v
React / TypeScript UI
 |  /api requests (Vite proxy in development)
 v
FastAPI
 |  GitHub URL + optional connected-account token
 v
Temporary Git clone -> GitPython extraction
 |  recent commits, selected diffs, file history, TODO/FIXME scan
 v
LangGraph application workflow
 |-> Intent agent
 |-> Scope agent only when task and changed files exist and history has >= 2 commits
 |-> Recovery agent
 |-> Final report agent
 v
Heuristic score + commit/file graph -> SQLite saved result -> JSON response
 |
 v
Dashboard / History / Compare pages
```

**Fig. 1.** Application request flow reconstructed from the current FastAPI endpoints, repository analyzer, workflow, and React pages. The scope branch operates on changed-file names in the dashboard workflow; it does not classify each diff hunk.

The development proxy is configured in `frontend/vite.config.ts`. It is not a production reverse proxy. The repository analyzer uses GitPython and a temporary clone. In the current implementation it returns at most ten recent commits, gathers file histories for at most five files from the newest commit, and caps each selected file diff at 3,000 characters while considering up to five files for that diff. TODO/FIXME scanning and further size checks occur after cloning. These limits describe the implementation, not a guarantee that clone resource consumption is bounded.

### B. Agent Workflow

The compiled LangGraph begins with the intent node. It routes to scope only when the recent history has at least two commits and both a task description and changed-file list are available. Scope then precedes recovery; otherwise the graph routes directly to recovery. The report node follows recovery. An empty-history intent fallback exists in the graph, although the full-analysis API rejects repositories without commits.

**Algorithm 1: Current full-analysis workflow**

```text
Input: GitHub repository URL, optional task description, optional changed files
1. Clone repository to a temporary directory; extract summary, commits, diffs,
   histories, and TODO/FIXME markers.
2. Reject the request if repository extraction reports no commits or an error.
3. Build the initial LangGraph state and evidence map.
4. Run intent agent on the latest commit, file histories, and evidence map.
5. If at least two commits exist and task and changed files are present:
      run scope agent on task description and changed-file names.
   Otherwise:
      mark scope as skipped or not available in workflow state.
6. Run recovery agent on summary and recent commits.
7. Generate a report from summary and agent outputs.
8. Compute the heuristic health metrics and commit-to-file graph.
9. Persist the result in SQLite and return it to the frontend.
```

The evidence verifier in `backend/services/evidence_verifier.py` is used by the evaluation subsystem. The dashboard workflow does not supply a pinned evidence pack to the agents or automatically verify their claims. Therefore, "evidence-based" in the prototype description means that repository evidence is gathered and supplied to prompts; it does not mean that every live conclusion has machine-verified semantic support.

### C. Modules and Status

| Module | Current implementation | Status and limitation |
|---|---|---|
| Repository extraction | Git clone, recent commits, selected diffs, file histories, TODO/FIXME scan | Implemented; network cloning and private GitHub access were not exercised in this paper audit. |
| Intent agent | Optional Gemini prompt; offline fallback derived from latest commit message and changed files | Partial; fallback is not an independent reconstruction of intent, and live Gemini output was not verified. |
| Scope agent | Optional task-vs-changed-file prompt; offline insufficient-evidence response | Partial; application passes filenames rather than diff hunks. |
| Recovery agent | Optional Gemini prompt; offline summary with generic MEDIUM recommendation | Partial; no calibrated score or demonstrated recovery ranking. |
| Health score | Weighted heuristic from commit count, TODO count, and recovery-output text | Implemented as a heuristic, not validated as project health or recovery probability. |
| Repository graph | Commit nodes linked to modified-file nodes | Implemented; the graph describes recorded commit/file relationships, not a dependency graph. |
| Saved history | SQLite storage of full analysis results and history endpoints | Implemented and API-tested with an isolated database; public-user access control was not part of these tests. |
| GitHub OAuth | Signed state, HTTP-only cookie, encrypted token storage, repository listing | Implemented with mocked exchange tests; real GitHub credentials and live OAuth were not tested. |
| Evaluation pipeline | Pinned evidence, baselines, prediction validation, citation checks and metrics | Implemented as research tooling; currently unscored because ground truth is absent. |

## IV. Heuristic Health Measure

The application computes the following measures from repository summary and recovery-agent text. Let \(C\) be the repository commit count, \(T\) the detected TODO/FIXME count, and \(s\) the lower-cased string form of the recovery output:

\[
A = \min(5C, 100), \qquad K = \max(0, 100 - 5T),
\]
\[
R = \min\left(100,\ 50 + 30\,\mathbf{1}[\text{``continue''}\subset s]
                      + 20\,\mathbf{1}[\text{``high potential''}\subset s]\right),
\]
\[
H = \operatorname{round}(0.40A + 0.35K + 0.25R,\ 2).
\]

Here, \(A\) is called Git activity, \(K\) code completeness, \(R\) recovery potential, and \(H\) the health score in the application. These names should not be read as measured constructs: the code uses simple capped arithmetic and substring checks. It does not estimate calibrated probabilities, execute project tests, or validate that TODO markers correspond to unfinished features. The `intent_analysis` argument accepted by the health-score function is unused. No predictive validity or ranking quality is established.

The repository comparison page analyzes repository URLs and ranks the resulting heuristic scores. A separate recommendation endpoint ranks user-supplied project metrics. Neither ranking has been validated against human recovery judgments.

## V. Evaluation Design and Available Data

### A. Candidate Dataset

The active manifest and case files describe the following candidate data. Intent and scope candidates may share source repositories; these are task-case counts, not independent repository counts.

| Item | Available | Annotation status | Source |
|---|---:|---|---|
| Source repositories | 9 | Not an annotation label | `evaluation/datasets/repositories.json` |
| Intent cases | 23 | 23 pending | `evaluation/datasets/intent_cases.json` |
| Scope task/diff pairs | 18 | 18 pending | `evaluation/datasets/scope_cases.json` |
| Recovery candidates | 9 | 9 pending; unfinished status unconfirmed | `evaluation/datasets/recovery_cases.json` |
| Total task cases | 50 | 0 labelled; 50 pending | Current run manifest and annotation guide |
| Commits reachable at registered revisions | 566 | Extracted Git fact, not a case label | Current evaluation report/manifest |

The annotation guide lists larger design targets of 25 repositories, 40 intent cases, 30 scope pairs, 20 recovery projects, and approximately 1,800 commits. These are targets, not observed sample sizes. Recovery eligibility has not been confirmed by human annotation. No annotator count, inter-rater agreement, adjudication, or participant study is reported because none is documented in the active dataset.

### B. Evaluation Pipeline and Smoke Run

The evaluation package has a pinned-revision evidence path, offline Git and Git-script baselines, an AICAR task-agent method, and a single-prompt LLM method that is skipped when live provider execution is disabled. Its metrics include normalized exact-match intent accuracy, scope precision/recall/F1, recovery nDCG, and an exact-extractive evidence-support measure. The metric definitions do not make them observed results.

The saved run `20261014T152850_5739f230` is explicitly `unscored_smoke`. Its manifest records 50 intent, 18 scope, and 9 recovery candidates, 9 repositories, 566 commits, 0 labelled cases, and 50 pending cases. It records 200 attempts, 150 executions, 150 successful executions, 0 errors, 50 skipped executions, and 0 scored cases. The LLM method did not run because the model was disabled. Every accuracy, precision, recall, F1, evidence-support rate, and nDCG value is unavailable (`null`), not zero. This run demonstrates that configured offline methods can execute on evidence packs; it provides no estimate of task performance.

### C. Software Verification

The following checks were rerun on 22 October 2026. They test software behavior and buildability, not research validity.

| Check | Result | Scope / limitation |
|---|---|---|
| Full Python suite: `python -m pytest -q -p no:cacheprovider --rootdir E:\\Codeforces\\agentic-code-archaeology -c E:\\Codeforces\\agentic-code-archaeology\\pytest.ini <isolated-test-copy>` | 47 passed | Current tests were copied under a disposable project-local test directory, with `PYTHONPATH` set to the project and backend and `DATABASE_URL` pointing to test-only SQLite. Includes API, OAuth, graph, and evaluation-pipeline tests; uses fixtures/mocks and does not test a live provider or remote GitHub repository. |
| OAuth-focused API tests: `python -m pytest -q -p no:cacheprovider -c pytest.ini evaluation\\tests\\test_api.py -k github` | 5 passed | Successful mocked state exchange plus invalid, expired, missing state, denial/configuration scenarios. |
| Frontend: `npm test -- --reporter=dot` | 10 passed in 2 files | Axios is mocked for UI API behavior. |
| Frontend lint: `npm run lint` | Passed | Static lint only. |
| Frontend production build: `npm run build -- --outDir E:\\aicar-paper-audit-build` | Passed | TypeScript build and Vite bundle; output was temporary and removed. |
| Demo smoke check: `python scripts\\smoke_test.py` | 0 of 6 endpoints available during this audit | Backend and frontend servers were not running; all checks failed with connection refused. This is a blocked live-demo check, not a test of analysis quality. |

The Python test run copied the current tests to a temporary workspace and set `DATABASE_URL` to a test-only SQLite file. The repository's production database was not used. The 47/10 software-test results must not be interpreted as 47/47 or 10/10 research predictions.

## VI. Results

No labelled research cases were available, and the live LLM method was disabled in the recorded smoke run. Consequently, this paper reports no measured intent accuracy, scope precision/recall/F1, recovery nDCG, semantic evidence-support rate, runtime improvement, or time savings. Such quantities cannot be inferred from the software test results or from successful execution of unlabelled cases.

The verified result is narrower: the application has working local components and automated tests for selected paths; the current dataset and evaluation pipeline do not yet establish whether the agents' conclusions are correct or better than a baseline.

## VII. Limitations and Threats to Validity

1. **Construct validity:** commit count, TODO count, and substrings in recovery text do not establish health, completion, or recoverability. The score is heuristic and uncalibrated.
2. **Scope evidence:** the dashboard scope agent receives changed-file names rather than per-hunk diffs. A filename alone is insufficient to determine semantic task relevance.
3. **Intent evidence:** the offline intent fallback largely repeats the latest commit message. A commit message may be incomplete, ambiguous, or unrelated to the selected code region.
4. **Citation support:** the evaluation verifier can resolve citations and award credit for exact extractive quotes; it does not automatically establish semantic entailment. It is not integrated into the live dashboard path.
5. **Dataset and labels:** all 50 active candidate cases are pending annotation. Repository selection, task provenance, human gold labels, and recovery eligibility are therefore unverified.
6. **External services:** real Gemini calls, GitHub OAuth, private-repository cloning, provider timeouts, and production deployment were not verified. The OAuth tests use mocked HTTP responses.
7. **Research design:** no participant study, independent annotation study, inter-rater agreement, or measured user-time comparison is available.
8. **Reproducibility:** the recorded smoke run is offline and unscored. Its timing includes shared validation/extraction and is not a controlled model or end-to-end latency comparison.
9. **Security and operations:** the application stores GitHub authorizations and analysis results. Authorization boundaries, clone resource controls, production routing, and database migration strategy require separate review before public deployment.

## VIII. Conclusion and Future Work

AICAR is an implemented prototype that combines repository extraction, a conditional LangGraph workflow, optional Gemini integration, SQLite result storage, a React dashboard, project comparison, and a commit-to-file graph. Automated tests verify selected API, workflow, evaluation, and UI behaviors. The project also contains a separate pinned-evidence evaluation pipeline.

The evidence available for this paper does not demonstrate accurate intent reconstruction, scope-creep detection, or recovery ranking. Scope analysis in the live path is based on filenames rather than individual code hunks; offline agent behavior is deliberately limited; the health score is heuristic; and all active research cases lack human labels. Accordingly, AICAR should be described as a prototype with an evaluation framework, not as a validated framework that outperforms existing methods.

Priority future work is to complete and provenance-check human annotations; verify recovery-project eligibility; run the preregistered offline and live evaluation without changing labels after observing predictions; integrate diff/hunk-level scope evidence and citation checks into the application path; calibrate or rename the health measure; test live GitHub and Gemini integrations; and address production authorization and resource-control concerns. Results should be added only after those tasks produce traceable artifacts.

## References

[1] G. Avelino, E. Constantinou, M. T. Valente, and A. Serebrenik, "On the abandonment and survival of open source projects: An empirical investigation," arXiv:1906.08058, 2019. doi: 10.48550/arXiv.1906.08058. [Online]. Available: https://arxiv.org/abs/1906.08058

[2] K. Zhu, Z. Tian, S. Wang, M. Leng, and X. Mao, "An LLM-based collaborative multi-agent framework for intent-driven commit untangling," arXiv:2601.01233, 2026. [Online]. Available: https://arxiv.org/abs/2601.01233. Bibliographic details were located through indexed arXiv/ACM records; confirm against the publisher's final proceedings record before submission.

[3] B. Hou, X. Tan, K. Zheng, F. Liu, Y. Zhu, and L. Zhang, "LLM-Driven Collaborative Model for Untangling Commits via Explicit and Implicit Dependency Reasoning," ACM Transactions on Software Engineering and Methodology, published online 2026, doi: 10.1145/3822177. The earlier draft's 2024 date is not supported by the publisher record located in this audit.

[4] L. Chen et al., "Detecting Vulnerability-Inducing Commits via Multi-Stage Reasoning with LLM-Based Agents," arXiv:2607.05772, 2026. [Online]. Available: https://arxiv.org/abs/2607.05772. The title and identifier were found in indexed arXiv records; full author list and publication status were not independently confirmed in this audit.

## Numerical Claim Ledger

| Numerical statement in this draft | Traceable source |
|---|---|
| 1,932 projects; 315 (16%) abandoned; 128 (41%) of abandoned projects survived | Primary arXiv record and abstract for [1]. |
| Health-score weights 0.40/0.35/0.25; component multipliers and caps | `backend/services/health_score.py`. |
| Extraction limits: ten recent commits; up to five file histories; up to five diff files; 3,000-character per-file diff cap | `backend/services/repository_analyzer.py`. |
| 9 repositories; 23 intent, 18 scope, 9 recovery cases; 50 total; 0 labelled; 50 pending; 566 commits | `evaluation/results/raw/20261014T152850_5739f230/manifest.json`, active datasets, and `evaluation/reports/evaluation_report.md`. |
| 25/40/30/20/approximately 1,800 research design targets | `evaluation/ANNOTATION_GUIDE.md`; explicitly labelled targets, not observations. |
| 200 attempts; 150 successful executions; 0 errors; 50 skipped; 0 scored cases | Saved smoke-run manifest `evaluation/results/raw/20261014T152850_5739f230/manifest.json`. |
| 47 Python tests; 5 OAuth-focused tests; 10 frontend tests | Rerun outputs from 22 October 2026 in the audit session. |
| Six demo endpoints, 0 available at check time | `scripts/smoke_test.py` check list and rerun output; endpoints were not running. |

No performance or research-accuracy result is asserted in this draft. Section/table/figure numbering is document structure, not empirical evidence.
