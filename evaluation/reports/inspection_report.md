# Inspection before implementation

Inspected the original repository at `07b121617c2a064e5e16c43db73a4ee852de864c`.
The only pre-existing working-tree change was `frontend/package-lock.json`.

1. **Architecture:** React/TypeScript/Vite dashboard, history and comparison pages;
   Axios through the Vite API proxy; FastAPI endpoints in `backend/main.py`;
   LangGraph workflow in `backend/graph/workflow.py`; SQLite/SQLAlchemy storage in
   `backend/database.py` and `backend/models/analysis.py`.
2. **Existing functionality:** repository cloning and Git extraction, recent
   commit/file histories, TODO scanning, intent/scope/recovery analysis, narrative
   report/recommendation agents, health heuristics, persisted analysis history,
   repository comparison and commit/file graph visualization.
3. **Actually implemented:** GitPython extraction capped at ten recent commits,
   five file diffs and truncated patches; evidence-map construction but no evidence
   verification; scope by filenames rather than hunks; recovery and comparison
   heuristics, not a validated ranking model. Repository-list endpoint returns
   mock entries. README's OpenAI description does not match the Gemini code.
4. **Missing research infrastructure:** pinned real dataset, human labels,
   provenance, valid evidence support checks, hunk classification, recovery nDCG,
   baseline parity, raw timing, reproducibility, uncertainty/missing-data handling.
   Legacy examples contain placeholder SHAs; existing saved results have no
   corresponding traceable experiment outputs and must not be treated as measured.
5. **Tests:** manual Markdown checklists and saved PASS examples, no executable
   automated tests. Frontend provides build/lint scripts. README refers to a
   missing backend requirements file and incorrect evaluation entry point.
6. **LLM/fallback:** Gemini SDK, model hardcoded in each agent, clients initialized
   at import time. `USE_GEMINI_ANALYSIS` defaults false, intent copies the commit
   message, scope reports insufficient evidence, recovery emits generic medium
   potential. `.env.example` originally names only `OPENAI_API_KEY`.
7. **Implementation files:** extend `backend/services/repository_analyzer.py`;
   add `git_evidence.py`, `llm.py`, `evidence_verifier.py`; extend existing agents
   with lazy provider access and structured task evaluation; replace legacy
   backend evaluation entry points/metrics/baselines with a common audited runner;
   add `evaluation/dataset.py`, `prepare_dataset.py`, `pipeline.py`, `metrics.py`,
   `reporting.py`, `figures.py`, task runners, datasets, annotation guide and tests.

The paper and FYP draft are intentionally unchanged. Existing dashboard endpoint
shapes and frontend implementation are preserved.
