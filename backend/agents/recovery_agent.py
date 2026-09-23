import os

try:
    from backend.services.llm import generate
except ModuleNotFoundError:
    from services.llm import generate


def analyze_recovery(repository_data, *, evidence_pack=None, live=False):
    if evidence_pack is not None:
        if live:
            from backend.services.llm import structured_prediction
            return structured_prediction("recovery", evidence_pack, specialized=True)
        return {"score": None, "confidence": "LOW", "claims": [],
                "analysis_mode": "local abstention; current recovery agent has no calibrated numeric ranking"}
    if os.getenv("USE_GEMINI_ANALYSIS", "false").lower() != "true":
        summary = repository_data.get("repository_summary", repository_data)
        commits = summary.get("total_commits", summary.get("commit_count", 0))
        todos = summary.get("todo_count", len(summary.get("todos", [])))
        return (
            "Local recovery assessment:\n"
            f"- Observed commits: {commits}\n"
            f"- Observed TODO/FIXME markers: {todos}\n"
            "- Recovery potential: MEDIUM\n"
            "- Recommendation: REVIEW — add tests and confirm deployment configuration."
        )

    prompt = f"""
You are a Software Project Recovery AI Agent.

Analyze this repository information:

{repository_data}

Your task is to estimate:

1. Possible cause of abandonment
2. Current project completion status
3. Remaining work
4. Recovery potential: HIGH / MEDIUM / LOW
5. Recommendation: CONTINUE / REVIEW / NOT_RECOMMENDED

Important:
- Use only the available evidence.
- Do not claim certainty when evidence is weak.
- Clearly mention assumptions.
"""

    return generate(prompt)
