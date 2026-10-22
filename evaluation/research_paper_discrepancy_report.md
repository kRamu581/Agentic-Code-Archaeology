# AICAR Paper-to-Implementation Discrepancy Report

**Audit date:** 22 October 2026
**Scope:** Comparison of `evaluation/research_paper_draft.md`, active application code, evaluation data, saved run artifacts, and current test outputs. The original draft was not modified.

## A. Executive Finding

The original paper presents AICAR as a validated agentic framework and reports performance numbers that are not supported by the current evaluation data. The codebase contains a functioning prototype, but several capabilities are partial, the active evaluation set is unlabelled, and the saved research run is explicitly an unscored smoke run. The revised draft therefore describes an implementation and its verification limits, not a validated comparative study.

The original manuscript's numeric result table (60%, 72%, 84%, 64%, 91%) was removed from the revised draft because no traceable labelled dataset, prediction artifact, or scored run substantiates those claims. The claimed sample sizes and annotation protocol were also removed or replaced with current manifest counts.

## B. Discrepancy Matrix

| Original paper statement | Current code/data evidence | Revision disposition |
|---|---|---|
| AICAR produces evidence-linked conclusions and citations | Evidence is collected and passed into ordinary prompts. The evaluation `evidence_verifier.py` can check citation resolution and exact quote support, but is not invoked by the live dashboard workflow. | Reframed as an evidence-gathering prototype; explicitly states machine verification is evaluation-only. |
| Scope creep is detected by comparing tasks with actual code changes | The dashboard workflow passes a task description and changed-file list to `analyze_scope`; it does not pass per-hunk diffs. Offline behavior reports insufficient evidence. | Described as partial task/file review, not validated hunk-level scope detection. |
| Recovery potential and viability are evaluated using structural indicators | Offline recovery emits a generic MEDIUM assessment from summary counts. Health score uses commit count, TODO count, and recovery-text substring checks. No score calibration or human validation exists. | Exposed the exact heuristic and removed claims of demonstrated viability ranking. |
| A three-agent architecture performs analysis | LangGraph workflow has intent, conditional scope, recovery, and report nodes. Scope requires at least two commits and both task and file inputs. Report is a separate node; recommendation is a separate API path. | Diagram and algorithm now match the implemented flow and conditional routing. |
| AICAR is compared against Git and zero-shot LLM baselines | Evaluation tooling contains baselines. The latest saved run disables the LLM and scores no labels. | Replaced superiority claims with an explicit unscored-smoke description. |
| Dataset has 50 intent cases, 60 scope pairs, and 30 recovery repositories; double annotation and Cohen's kappa | Active manifest: 23 intent candidates, 18 scope pairs, 9 recovery candidates, 9 repositories, 566 commits; 0 labelled, 50 pending. No completed multi-annotator records or kappa results were found. | Corrected counts, described targets separately from observations, removed the annotation-agreement claim. |
| Git 60%, LLM 72%, AICAR 84%; evidence support 64%/91%; scope F1 values | Current processed results and manifest have null metrics and zero scored cases. No matching source artifacts were identified for the original numbers. | Removed all unsupported outcome figures. |
| Project recovery is ranked by a recovery agent | Repository comparison ranks application heuristic scores; one recommendation endpoint accepts caller-supplied metrics. Neither has measured alignment with human recovery labels. | Described interfaces as present and ranking quality as unverified. |
| Avelino et al. (2019) found 16% abandonment and 41% survival | Primary arXiv record `1906.08058` confirms 1,932 projects, 315 (16%) abandoned, and 128 (41% of abandoned projects) surviving after new maintainers assumed development. | Retained with exact denominator and verified arXiv reference. |
| Atomizer (Zhu et al., 2026) | Indexed arXiv/ACM results locate the title, author list, and arXiv:2601.01233. Direct arXiv page retrieval did not complete in this audit. | Corrected title and supplied identifier; flagged publisher proceedings record for final cross-check. |
| ColaUntangle (Hou et al., 2024) | Indexed ACM record gives DOI `10.1145/3822177`, title, authors, and 2026 online publication. | Corrected publication year to 2026; the 2024 date is unsupported. |
| VIC-RAGENT (Chen et al., 2026; arXiv:2607.05772) | Indexed arXiv results support the title and identifier, but this audit could not retrieve the primary arXiv page to confirm full author list/publication status. | Retained only with an explicit metadata-verification caveat. |
| Barnett et al. (2015), Dias et al. (2015), Dhaouadi et al. (2023), Fan et al. (2024) | In-text citations lack complete bibliographic records in the original draft; intended works could not be confidently identified. | Removed from the revised paper and listed as needing author-supplied source details. |
| System testing: all features PASS | Original `final_testing.md` and phase checklists are manually stated outcomes, not current test evidence. | Replaced with current test suite outputs and limitations. |

## C. Figure and Table Disposition

| Original / existing item | Disposition |
|---|---|
| Original abstract/introduction claims of demonstrated effectiveness | Rewrite; no empirical effectiveness result exists. |
| Original architecture diagram | Replace with Fig. 1 in the revised paper. The new flow reflects actual proxy/backend/extraction/conditional workflow/SQLite flow and labels the current changed-file limitation. |
| Original results table (60%, 72%, 84%, 64%, 91%) | Remove. No matching traceable scored run exists. |
| Original sample-size and inter-rater claims | Remove and replace with a dataset inventory that separates current candidates from research design targets. |
| Any result plot derived from old result tables | Do not reuse. Regenerate only after the evaluation dataset is labelled and a scored run has been archived. |
| Figures and tables under `evaluation/results/figures/` | No PNG, JPEG, SVG, or PDF figure files were found during the audit. The figure-generation code is not evidence that paper-ready plots exist. |
| Revised paper tables | New module-status, candidate-dataset, and software-verification tables are implementation/audit summaries, not experimental performance tables. |

The workspace inventory contained no PDF under `evaluation/`; the original Markdown paper remains unchanged. If an original PDF exists elsewhere, this audit did not access or alter it.

## D. Work That Remains Beyond This Revision

These items cannot be honestly completed merely by editing the paper, and should not be claimed as finished in a six-hour submission window:

1. Annotate every selected intent and scope case with provenance and rationale; establish whether recovery candidates were truly unfinished.
2. Establish an annotation protocol, independent annotator count, adjudication process, and inter-rater agreement only if those activities are actually performed.
3. Run offline and live evaluations on frozen labels, retain raw evidence/predictions, and report every skipped/failed case.
4. Expand the dataset toward the documented targets only if time and defensible selection criteria permit; the targets are not mandatory validation by themselves.
5. Integrate code/hunk evidence and citation verification into the live scope/intent path, or limit product claims accordingly.
6. Calibrate or rename the health score and validate recovery rankings against human judgments.
7. Test real Gemini, GitHub OAuth, public/private repository cloning, and deployment configuration with safe test accounts and documented consent.
8. Address production authorization, clone resource controls, rate limiting, and database migration strategy before public deployment.
9. Rebuild any figures or benchmark comparison tables from the final scored run; do not copy the obsolete values.
10. Complete a reliable bibliography check and any institution-required literature review, ethics review, formatting, and demonstration evidence.

## E. Numerical Consistency Check

The revised paper was checked against the current code and records. Traceable numbers retained are:

| Number(s) retained | Source / interpretation |
|---|---|
| 1,932 projects; 315 (16%) abandoned; 128 (41%) of abandoned projects survived | Primary arXiv abstract, `https://arxiv.org/abs/1906.08058`. |
| 40%, 35%, 25%; factors 5, 30, and 20 | Formula and implementation constants in `backend/services/health_score.py`; described as a heuristic only. |
| Ten recent commits; up to five file histories; up to five diff files; 3,000-character diff limit | `backend/services/repository_analyzer.py`. |
| 9 repositories; 23 intent; 18 scope; 9 recovery; 50 total; 0 labelled; 50 pending; 566 commits | `evaluation/results/raw/20261014T152850_5739f230/manifest.json`, active datasets, and evaluation report. |
| Targets of 25 repositories, 40 intent, 30 scope, 20 recovery, and approximately 1,800 commits | `evaluation/ANNOTATION_GUIDE.md`; marked as targets, not observed data. |
| 200 attempts; 150 executed and successful; 0 errors; 50 skipped; 0 scored | Saved smoke-run manifest. This is execution status, not predictive performance. |
| 47 Python tests; 5 OAuth-focused tests; 10 frontend tests | Current rerun outputs in the audit session dated 22 October 2026. |
| Six smoke endpoints; zero reachable at current recheck | `scripts/smoke_test.py` and its run output; services were not running. |

The revised paper does not contain the original accuracy, precision, recall, F1, evidence-support, nDCG, speedup, or time-saving claims. The `14`, section numbers, table numbers, figure number, and algorithm numbering in the paper are structural labels rather than empirical results.

## Bibliographic Verification Notes

- **Verified from primary source:** Avelino et al., arXiv:1906.08058. The arXiv record confirms title, authors, submission date, DOI, study design, and reported counts.
- **Located in indexed official records:** Atomizer, arXiv:2601.01233; final conference proceedings metadata should be confirmed.
- **ACM DOI and corrected year located:** ColaUntangle, DOI `10.1145/3822177`, listed as online publication in 2026. Do not cite it as a 2024 publication.
- **Partially verified:** VIC-RAGENT, arXiv:2607.05772. Title and identifier appear in indexed arXiv results; full author list and publication status remain to be checked against the primary record.
- **Unresolved:** Barnett, Dias, Dhaouadi, and Fan citations as given in the initial text. No complete references were supplied; do not restore them without source identifiers.

## Current Verification Record

- Python suite: 47 passed. Exact invocation pattern: `python -m pytest -q -p no:cacheprovider --rootdir E:\\Codeforces\\agentic-code-archaeology -c E:\\Codeforces\\agentic-code-archaeology\\pytest.ini <isolated-test-copy>`, with `PYTHONPATH` set to the project root and backend and `DATABASE_URL` set to a test-only SQLite file. Test files were copied under a disposable project-local directory and removed afterwards.
- OAuth-focused API tests: 5 passed, including successful state exchange and invalid, expired, and missing state handling.
- Frontend tests: 10 passed in 2 files.
- Frontend lint and production build: passed.
- Current live demo smoke check: failed with connection refused for all six checks because neither server was running. This was reported as unavailable, not as application correctness evidence.
- No Gemini API call, real GitHub OAuth exchange, live remote repository analysis, or scored research experiment was performed in this audit.
