import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def recommend_project(projects):
    if os.getenv("USE_GEMINI_ANALYSIS", "false").lower() != "true":
        if not projects:
            return "No projects were provided."
        return (
            "Local recommendation: prioritize the highest-ranked project from "
            "the calculated health scores. Enable Gemini for narrative reasoning."
        )
    prompt = f"""
You are a Software Project Recovery Agent.

Analyze these unfinished projects:

{projects}

Recommend which ONE project should be finished first.

Consider:
- completion level
- remaining work
- TODOs
- recent activity
- technical risk

Return:

1. Recommended project
2. Why it should be completed
3. Main remaining work
4. Risks
5. Ranking of all projects

Important:
Base conclusions only on the provided evidence.
Do not invent missing project details.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
