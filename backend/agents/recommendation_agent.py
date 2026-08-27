import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def recommend_project(projects):
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

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
