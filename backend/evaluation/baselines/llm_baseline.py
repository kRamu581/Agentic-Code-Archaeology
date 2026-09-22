from google import genai
import os

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def llm_baseline(commit):

    prompt = f"""
Based only on the following Git commit information,
answer the question:

Why was this code change introduced?

Commit message:
{commit.get("message")}

Changed files:
{commit.get("changed_files")}

Actual code diff:
{commit.get("diff", [])}

Give a short answer.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return {
            "prediction": response.text,
            "method": "Basic LLM"
        }
    except Exception as e:
        return {
            "prediction": str(e),
            "method": "Basic LLM"
        }
