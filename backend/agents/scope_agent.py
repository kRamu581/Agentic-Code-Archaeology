import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_scope(task_description, changed_files):
    if os.getenv("USE_GEMINI_ANALYSIS", "false").lower() != "true":
        return (
            "Verdict: INSUFFICIENT_EVIDENCE\n"
            f"Requested task: {task_description}\n"
            f"Changed files: {', '.join(changed_files)}\n"
            "Local analysis cannot determine semantic relevance; enable Gemini for an AI review."
        )

    prompt = f"""
You are a Software Scope Creep Detection AI Agent.

A developer was given this task:

{task_description}

The developer changed these files:

{changed_files}

Analyze whether the changes are related to the requested task.

Return:

1. Verdict: IN_SCOPE / POSSIBLE_SCOPE_CREEP
2. Related changes
3. Unrelated or suspicious changes
4. Short explanation

Do not invent information.
If there is insufficient evidence, say so clearly.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
