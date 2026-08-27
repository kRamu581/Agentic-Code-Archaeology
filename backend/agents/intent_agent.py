import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_intent(commit, file_histories, evidence_map):

    prompt = f"""
You are an Evidence-Based Software Code Archaeology AI Agent.

Your goal is to reconstruct WHY a code change exists.

COMMIT HASH:
{commit["hash"]}

COMMIT MESSAGE:
{commit["message"]}

CHANGED FILES:
{commit["changed_files"]}

ACTUAL CODE DIFF:
{commit.get("diff", [])}

FILE HISTORY:
{file_histories}

EVIDENCE MAP:
{evidence_map}

Return ONLY valid JSON in this format:

{{
    "likely_intent": "...",
    "code_change_summary": "...",
    "historical_context": "...",
    "confidence": "HIGH | MEDIUM | LOW",
    "evidence": [
        {{
            "type": "commit | file | diff | history",
            "reference": "...",
            "reason": "Why this evidence supports the conclusion"
        }}
    ]
}}

Rules:
- Every important conclusion must be supported by evidence.
- Do not invent developer intentions.
- Distinguish facts from inference.
- If evidence is weak, use LOW confidence.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(
        response.choices[0].message.content
    )
