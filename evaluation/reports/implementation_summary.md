# Implementation and verification

Extended the existing backend and evaluation modules; no frontend rewrite. The pre-existing frontend/package-lock.json change was preserved. Paper/FYP draft files are unchanged (`git diff --exit-code` passed).

## Files created or modified

- `.env.example`
- `.gitignore`
- `README.md`
- `backend/agents/intent_agent.py`
- `backend/agents/recommendation_agent.py`
- `backend/agents/recovery_agent.py`
- `backend/agents/report_agent.py`
- `backend/agents/scope_agent.py`
- `backend/evaluation/baselines/agentic_system.py`
- `backend/evaluation/baselines/git_baseline.py`
- `backend/evaluation/baselines/git_script_baseline.py`
- `backend/evaluation/baselines/llm_baseline.py`
- `backend/evaluation/generate_report.py`
- `backend/evaluation/metrics.py`
- `backend/evaluation/run_evaluation.py`
- `backend/services/evidence_verifier.py`
- `backend/services/git_evidence.py`
- `backend/services/llm.py`
- `backend/services/repository_analyzer.py`
- `evaluation/ANNOTATION_GUIDE.md`
- `evaluation/README.md`
- `evaluation/__init__.py`
- `evaluation/dataset.py`
- `evaluation/datasets/evidence/aicar_intent_07b121617c2a.json`
- `evaluation/datasets/evidence/aicar_intent_1e253587774c.json`
- `evaluation/datasets/evidence/aicar_intent_df3ad517cd35.json`
- `evaluation/datasets/evidence/aicar_recovery.json`
- `evaluation/datasets/evidence/aicar_scope_07b121617c2a.json`
- `evaluation/datasets/evidence/aicar_scope_1e253587774c.json`
- `evaluation/datasets/evidence/aicar_scope_df3ad517cd35.json`
- `evaluation/datasets/intent_cases.json`
- `evaluation/datasets/recovery_cases.json`
- `evaluation/datasets/repositories.json`
- `evaluation/datasets/repositories/.gitkeep`
- `evaluation/datasets/scope_cases.json`
- `evaluation/figures.py`
- `evaluation/metrics.py`
- `evaluation/pipeline.py`
- `evaluation/prepare_dataset.py`
- `evaluation/reporting.py`
- `evaluation/reports/evaluation_report.md`
- `evaluation/reports/inspection_report.md`
- `evaluation/requirements.txt`
- `evaluation/runners/run_all.py`
- `evaluation/runners/run_intent_eval.py`
- `evaluation/runners/run_recovery_eval.py`
- `evaluation/runners/run_scope_eval.py`
- `evaluation/tests/.gitignore`
- `evaluation/tests/conftest.py`
- `evaluation/tests/test_evaluation.py`
- `pytest.ini`

## Generated artifacts

- `evaluation/results/final_results.json` and `.csv`
- `evaluation/reports/evaluation_report.md`
- `evaluation/results/raw/<run_id>/`: predictions, full evidence packs, manifest, review template, timing CSV and report
- `evaluation/results/processed/<run_id>.json`
- `evaluation/results/figures/<run_id>/`: measured timing PNG/PDF and omission reasons for unmeasured accuracy charts
- `evaluation/results/test_results.xml`: automated test results
- `evaluation/results/legacy_unverified/final_results.json`: exact preservation of previous unverified results

## Actual latest smoke run

Run `20260922T172449_3f6dec5e`: 21 offline method executions, 21 successes, 0 errors, 7 skipped LLM calls. Zero ground-truth-scored cases. Pipeline wall time 24.196333 seconds, including 23.962019 seconds of shared validation/extraction. Report and figure generation are outside this timed interval.

Earlier development smoke runs are retained separately; they are repeated executions on the same source, not additional repositories or independent labelled experiments.

## Verification

- Complete Python test suite: see test_results.xml (33 tests in the final suite).
- Frontend `npm run lint`: passed.
- Frontend `npm run build`: passed after rerunning outside the sandbox that blocked a Vite child process.
- Strict runner: rejected missing ground truth without replacing results.
- 42 Python source files compiled; fixture working trees excluded.
- `git diff --check`: passed.
- Coverage: not measured; pytest-cov is unavailable.

## Remaining research work

Human annotation and representative source-repository expansion are mandatory. See ANNOTATION_GUIDE.md. No live provider or dashboard API integration run was performed (Gemini SDK, FastAPI and LangGraph are not installed in this environment). Offline baselines abstain on recoverability rather than inventing rankings. Intent exact-match and extractive evidence support have explicitly documented semantic limitations. Human semantic review templates are exported but not automatically scored. No paper claims were validated or revised.
