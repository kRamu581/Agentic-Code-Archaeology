# Reproducible evaluation

Start with [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md). The active dataset is
`datasets/`, not the legacy illustrative `dataset/` directory.

```powershell
python -m pip install -r evaluation/requirements.txt
python -m pytest -q
python evaluation/runners/run_all.py --smoke
```

The default runner (without `--smoke`) fails on missing human labels. Smoke mode
runs real Git evidence without scoring accuracy. `--live` explicitly enables
Gemini with GEMINI_API_KEY and GEMINI_MODEL in the process environment.

Methods reuse `backend/evaluation/baselines/` and the existing application agents.
Outputs contain immutable per-run raw evidence/predictions, timing CSV, processed
metrics, final JSON/CSV and a Markdown report. Figures are drawn only for measured
values; absent metrics receive a reason in the figures manifest, never a zero bar.

`research_paper_draft.md` and `fyp_report_draft.md` are unchanged. Their numbers,
`dataset/*_examples.json`, `results/final_metrics.json`, manual PASS checklists and
`results/phase3_test_results.json` are **legacy unverified material**, excluded
from every experiment. The previous `results/final_results.json` is preserved at
`results/legacy_unverified/final_results.json`. Only schema-versioned new run
artifacts represent execution of this evaluator.
