import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Load .env from root of monorepo or local .env
root_env = Path(__file__).parents[4] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


async def generate_response(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"
