import os
import json

try:
    from backend.services.llm import generate
except ModuleNotFoundError:
    from services.llm import generate


def analyze_intent(commit, file_histories, evidence_map, *, evidence_pack=None, live=False):
    if evidence_pack is not None:
        if live:
            from backend.services.llm import structured_prediction
            return structured_prediction("intent", evidence_pack, specialized=True)
        message = commit.get("message", "")
        return {"intent": message, "introducing_commit": None, "confidence": "LOW",
                "analysis_mode": "local fallback; introducing region not inferred",
                "claims": [{"text": message, "quote": message, "kind": "quote",
                            "commit": commit["hash"], "file": None, "hunk": None}]}
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

    return generate(prompt, structured=True)
