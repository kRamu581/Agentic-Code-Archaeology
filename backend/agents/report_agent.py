import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def generate_final_report(
    repository_summary,
    intent_analysis,
    scope_analysis,
    recovery_analysis
):

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
