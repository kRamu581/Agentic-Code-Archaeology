import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_recovery(repository_data):
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

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
