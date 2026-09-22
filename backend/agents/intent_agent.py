import os
import json
from google import genai
from google.genai import types

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_intent(commit, file_histories, evidence_map):
    if os.getenv("USE_GEMINI_ANALYSIS", "false").lower() != "true":
        changed_files = commit.get("changed_files", [])
        return {
            "likely_intent": commit.get("message", "No commit message available."),
            "code_change_summary": (
                f"The commit changes {len(changed_files)} file(s): "
                + ", ".join(changed_files[:5])
            ),
            "historical_context": (
                f"{len(file_histories)} changed file(s) have available history."
            ),
            "confidence": "LOW",
            "evidence": [
                {
                    "type": "commit",
                    "reference": commit.get("hash", "unknown"),
                    "reason": "Derived from the commit message and changed-file list."
                }
            ],
            "analysis_mode": "local fallback (set USE_GEMINI_ANALYSIS=true to enable Gemini)"
        }

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

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)
