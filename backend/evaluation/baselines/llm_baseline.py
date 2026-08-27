from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
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

Give a short answer.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return {
            "prediction": response.choices[0].message.content,
            "method": "Basic LLM"
        }
    except Exception as e:
        return {
            "prediction": str(e),
            "method": "Basic LLM"
        }
