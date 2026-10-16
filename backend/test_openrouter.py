
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

if not api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing from backend/.env"
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: Company Brain LLM connected",
        }
    ],
)

print("Model:", response.model)
print("Response:", response.choices[0].message.content)
