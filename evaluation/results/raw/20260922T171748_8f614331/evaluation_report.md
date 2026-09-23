# AICAR reproducible evaluation

## Experimental setup

Run `20260922T171748_8f614331`: **unscored_smoke**. Pinned Git objects; shared evidence per case. Python 3.13.9. Model: disabled. All measurements below come from this run.

## Dataset size

{
  "intent": 3,
  "scope": 3,
  "recovery": 1,
  "repositories": 1,
  "commits": 4,
  "labelled": 0,
  "pending": 7
}

## Dataset composition

Source paths, origins and immutable revisions: evaluation/datasets/repositories.json. Code-case candidates are commits changing source; recovery eligibility is unconfirmed until annotated. Targets (25 repositories, 40 intent, 30 scope, 20 recovery, approximately 1,800 commits) are not achieved dataset counts.

## Ground-truth methodology

Human annotation is mandatory; see evaluation/ANNOTATION_GUIDE.md. No labels are copied from the paper, legacy examples, commit messages, or model predictions. Intent uses preregistered normalized exact accepted answers; this is a strict textual metric, not a semantic correctness claim. Human semantic review is exported separately and not automatically scored.

## Baselines

Git: commit message extraction; scope abstention; no recovery rank. Git log/blame script: single-origin line-blame message plus history summary; ambiguous provenance abstains. Single-prompt Gemini: one common evidence pack per task, no specialized agent or verifier. Offline runs skip Gemini. No manual human analysis time is claimed.

## AICAR architecture

Existing repository analyzer's pinned-snapshot path, existing intent/scope/recovery agents with structured evaluation outputs, and evidence verifier. Dashboard's LangGraph/report route is not timed. Offline AICAR retains intent message fallback and abstains on semantic scope/recovery. Live outputs use specialized task instructions. This is a task-agent evaluation, not a measured end-to-end dashboard benchmark.

## Intent results

Git baseline: {'accuracy': None, 'cases': 0, 'correct': 0, 'incorrect': 0, 'introducing_commit_accuracy': None}
Git log/blame script: {'accuracy': None, 'cases': 0, 'correct': 0, 'incorrect': 0, 'introducing_commit_accuracy': None}
Single-prompt LLM: {'accuracy': None, 'cases': 0, 'correct': 0, 'incorrect': 0, 'introducing_commit_accuracy': None}
Proposed AICAR: {'accuracy': None, 'cases': 0, 'correct': 0, 'incorrect': 0, 'introducing_commit_accuracy': None}

## Evidence-support results

Git baseline: {'supported': 0, 'total_verifiable': 0, 'rate': None}
Git log/blame script: {'supported': 0, 'total_verifiable': 0, 'rate': None}
Single-prompt LLM: {'supported': 0, 'total_verifiable': 0, 'rate': None}
Proposed AICAR: {'supported': 0, 'total_verifiable': 0, 'rate': None}
Only exact extractive claims receive automatic support credit. Resolvable citations alone do not prove semantic support. Interpretations are flagged for human review; this conservative measure is not a semantic entailment score. Smoke audits are retained but not promoted to research metrics.

## Scope precision/recall/F1

Git baseline: {'tp': 0, 'fp': 0, 'fn': 0, 'precision': None, 'recall': None, 'f1': None, 'gold_unclear_excluded': 0, 'predicted_unclear': 0, 'decision_accuracy': None, 'cases': 0}
Git log/blame script: {'tp': 0, 'fp': 0, 'fn': 0, 'precision': None, 'recall': None, 'f1': None, 'gold_unclear_excluded': 0, 'predicted_unclear': 0, 'decision_accuracy': None, 'cases': 0}
Single-prompt LLM: {'tp': 0, 'fp': 0, 'fn': 0, 'precision': None, 'recall': None, 'f1': None, 'gold_unclear_excluded': 0, 'predicted_unclear': 0, 'decision_accuracy': None, 'cases': 0}
Proposed AICAR: {'tp': 0, 'fp': 0, 'fn': 0, 'precision': None, 'recall': None, 'f1': None, 'gold_unclear_excluded': 0, 'predicted_unclear': 0, 'decision_accuracy': None, 'cases': 0}
Out-of-scope is the positive class. Gold unclear hunks are excluded from binary metrics and counted separately. Predicted unclear on a positive is a false negative. Zero denominators yield null, not invented scores.

## Recovery nDCG

Git baseline: {'ndcg': None, 'repositories': 0, 'predicted_ranking': [], 'ground_truth_ranking': []}
Git log/blame script: {'ndcg': None, 'repositories': 0, 'predicted_ranking': [], 'ground_truth_ranking': []}
Single-prompt LLM: {'ndcg': None, 'repositories': 0, 'predicted_ranking': [], 'ground_truth_ranking': []}
Proposed AICAR: {'ndcg': None, 'repositories': 0, 'predicted_ranking': [], 'ground_truth_ranking': []}
Full-cohort nDCG uses gain 2^grade-1 and log2(position+1) discounts, grades 0..3; deterministic case-ID tie break. At least two distinct human-labelled repositories are required. Any missing score makes the cohort metric unavailable.

## Analysis time

Measured pipeline seconds: 27.512967; shared validation/extraction: 27.262724. Executed: 21; successful: 21; errors: 0; skipped: 7. See timings.csv for timestamps and actual input counts. validation/extraction plus method execution; shared extraction is measured separately, report/plot generation excluded. No scaling trend or speedup is inferred from a single smoke run.

## Comparison table

Method | Intent Accuracy | Evidence Support | Scope F1 | Recovery nDCG
--- | --- | --- | --- | ---
Git baseline | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth
Git log/blame script | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth
Single-prompt LLM | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth
Proposed AICAR | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth | N/A — insufficient ground truth

## Limitations

N/A in an unlabelled run means insufficient ground truth. In scored runs, consult task_status for missing methods or failures; recovery abstention and zero-denominator metrics also remain unavailable. No live model result exists in offline mode. One self-repository is not a representative benchmark; candidate regions need human selection. Entry points, dependencies, deployment and feature completeness are not executed/verified. Large/binary blobs are excluded from text feature counts and listed in evidence. Merge diffs use the first parent. No dashboard or provider integration success is implied. Legacy results and paper claims are excluded; paper files are unchanged.

## Reproducibility instructions

From repository root: `python -m pytest -q` then `python evaluation/runners/run_all.py --smoke`. After human annotation: `python evaluation/runners/run_all.py` for offline methods; add `--live` with GEMINI_API_KEY and GEMINI_MODEL set for live comparison. Run `python evaluation/figures.py` to regenerate figures. Immutable raw manifests contain code/dataset hashes, environment versions and complete input packs. Timing and live provider responses may vary.
