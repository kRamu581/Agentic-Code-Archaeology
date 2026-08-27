import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_scope(task_description, changed_files):

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
