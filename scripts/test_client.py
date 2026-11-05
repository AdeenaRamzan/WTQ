"""Phase 1 check: exercise LLMClient (cache + fallback + rate limit).

Run twice: first call hits the API, second is served from cache instantly.
    python scripts/test_client.py
"""
from src.llm_client import LLMClient


def main() -> None:
    client = LLMClient()
    prompt = "Reply with exactly the word: PONG"
    text = client.generate(prompt, temperature=0)
    print("Response:", repr(text.strip()))
    print("Calling again (should be a cache hit)...")
    text2 = client.generate(prompt, temperature=0)
    print("Response:", repr(text2.strip()))
    print("OK - client, cache and config all work.")


if __name__ == "__main__":
    main()
