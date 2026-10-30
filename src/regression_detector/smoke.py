import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the ignored local key only when this module is executed.
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

with genai.Client(api_key=api_key) as client:
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Return only the word READY.",
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            max_output_tokens=20,
        ),
    )

text = (response.text or "").strip()
candidates = response.candidates or []
usage = response.usage_metadata
if not candidates or text != "READY":
    raise RuntimeError("Gemini returned an invalid smoke response")
counts = None if usage is None else (
    usage.prompt_token_count, usage.candidates_token_count, usage.total_token_count
)
if counts is None or any(value is None for value in counts):
    raise RuntimeError("Gemini omitted required usage metadata")
print(f"response={text} input={counts[0]} output={counts[1]} total={counts[2]}")