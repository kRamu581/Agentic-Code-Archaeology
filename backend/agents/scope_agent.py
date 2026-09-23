import os

try:
    from backend.services.llm import generate
except ModuleNotFoundError:
    from services.llm import generate


def analyze_scope(task_description, changed_files, *, evidence_pack=None, live=False):
    if evidence_pack is not None:
        if live:
            from backend.services.llm import structured_prediction
            return structured_prediction("scope", evidence_pack, specialized=True)
        return {"hunks": {h["id"]: "unclear" for h in evidence_pack["hunks"]},
                "verdict": "justify", "confidence": "LOW", "claims": [],
                "analysis_mode": "local abstention; semantic scope requires review"}
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

    return generate(prompt)
