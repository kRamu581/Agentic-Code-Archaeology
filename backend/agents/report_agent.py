import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_final_report(
    repository_summary,
    intent_analysis,
    scope_analysis,
    recovery_analysis
):
    if os.getenv("USE_GEMINI_ANALYSIS", "false").lower() != "true":
        return (
            "Overall repository condition: Review recommended.\n\n"
            f"Repository summary: {repository_summary}\n\n"
            f"Intent findings: {intent_analysis}\n\n"
            f"Scope findings: {scope_analysis}\n\n"
            f"Recovery findings: {recovery_analysis}\n\n"
            "Next action: add automated tests and configure a valid Gemini key only "
            "when AI-enhanced analysis is required."
        )

    prompt = f"""
You are the Final Decision Agent in an Agentic
Code Archaeology system.

Create one unified repository analysis report using:

Repository Summary:
{repository_summary}

Intent Analysis:
{intent_analysis}

Scope Analysis:
{scope_analysis}

Recovery Analysis:
{recovery_analysis}

Return:

1. Overall repository condition
2. Main findings
3. Important risks
4. Recommended next action
5. Final recommendation

Be evidence-based. Do not invent facts.
If evidence is insufficient, clearly mention it.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
