import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_recovery(repository_data):

    prompt = f"""
You are a Software Project Recovery AI Agent.

Analyze this repository information:

{repository_data}

Your task is to estimate:

1. Possible cause of abandonment
2. Current project completion status
3. Remaining work
4. Recovery potential: HIGH / MEDIUM / LOW
5. Recommendation: CONTINUE / REVIEW / NOT_RECOMMENDED

Important:
- Use only the available evidence.
- Do not claim certainty when evidence is weak.
- Clearly mention assumptions.
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
