"""One-call Gemini smoke test. Verifies your API key and model access.

Usage:
    python scripts/test_gemini.py
Reads MODEL_NAME and API_KEY from .env (copy .env.example -> .env first).
"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.1-flash-lite")

if not API_KEY or API_KEY == "your-api-key-here":
    print("ERROR: Set a real API_KEY in .env (copy .env.example to .env first).")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

print(f"Calling model: {MODEL_NAME} ...")
resp = client.models.generate_content(
    model=MODEL_NAME,
    contents="Reply with exactly: OK",
    config=types.GenerateContentConfig(temperature=0),
)
print("Model replied:", repr(resp.text))
print("SUCCESS - your key and model work.")
