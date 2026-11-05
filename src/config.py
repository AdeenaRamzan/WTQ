"""Central configuration. Reads .env, exposes paths, model names and limits.

Never prints or logs the API key.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CACHE_DIR = PROJECT_ROOT / "cache"       # on-disk LLM response cache
OUTPUT_DIR = PROJECT_ROOT / "output"     # generated CSVs
LOG_DIR = PROJECT_ROOT / "logs"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"

for _d in (CACHE_DIR, OUTPUT_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Model / provider configuration (from .env)
# ---------------------------------------------------------------------------
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "google")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.1-flash-lite")
FALLBACK_MODEL_NAME = os.getenv("FALLBACK_MODEL_NAME", "gemini-3.5-flash-lite")
API_KEY = os.getenv("API_KEY")

# Ordered list of models to try: primary first, then fallback (deduped).
MODEL_CHAIN = [m for m in dict.fromkeys([MODEL_NAME, FALLBACK_MODEL_NAME]) if m]

# ---------------------------------------------------------------------------
# Rate limiting / retry (free tier: 15 req/min, 250K tok/min, 500 req/day)
# We stay comfortably under the per-minute cap.
# ---------------------------------------------------------------------------
MAX_REQUESTS_PER_MIN = int(os.getenv("MAX_REQUESTS_PER_MIN", "12"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_BASE_SECONDS = float(os.getenv("RETRY_BASE_SECONDS", "2"))
RETRY_MAX_SECONDS = float(os.getenv("RETRY_MAX_SECONDS", "60"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))

# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------
# Upscale smaller images so the model can read fine print; cap the long edge
# so we don't blow the token budget.
MIN_LONG_EDGE_PX = int(os.getenv("MIN_LONG_EDGE_PX", "1600"))
MAX_LONG_EDGE_PX = int(os.getenv("MAX_LONG_EDGE_PX", "2600"))


def validate() -> None:
    """Fail fast with a clear message if the key is missing."""
    if not API_KEY or API_KEY == "your-api-key-here":
        raise SystemExit(
            "API_KEY is not set. Copy .env.example to .env and put your real "
            "Google AI Studio key in API_KEY."
        )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger (console + logs/run.log)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s",
                            datefmt="%H:%M:%S")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(LOG_DIR / "run.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.propagate = False
    return logger
