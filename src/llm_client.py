"""Gemini client wrapper: rate limiting, retry with backoff, model fallback,
and on-disk caching of every response.

Design notes
------------
* Cache key is derived from the *logical request* (prompt + image bytes +
  schema + temperature), NOT the model name. So a re-run is free even if we
  had to fall back to the secondary model last time, and both Level 1 and
  Level 2 re-runs cost zero API calls once populated.
* Only real API calls pass through the rate limiter; cache hits are instant.
* Retries cover 429 (quota) and 5xx; after exhausting retries on the primary
  model we transparently try the fallback model.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import deque
from typing import Any, Optional

from google import genai
from google.genai import errors, types
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from . import config

log = config.get_logger("llm")


# ---------------------------------------------------------------------------
# Rate limiter: sliding 60s window, thread-safe.
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, max_per_min: int):
        self.max_per_min = max_per_min
        self._times: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                while self._times and now - self._times[0] >= 60:
                    self._times.popleft()
                if len(self._times) < self.max_per_min:
                    self._times.append(now)
                    return
                sleep_for = 60 - (now - self._times[0]) + 0.1
            log.info("Rate limit reached; sleeping %.1fs", sleep_for)
            time.sleep(max(sleep_for, 0.1))


# ---------------------------------------------------------------------------
# Retry predicate
# ---------------------------------------------------------------------------
def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, errors.ServerError):  # 5xx
        return True
    if isinstance(exc, errors.ClientError):  # 4xx; retry only on 429
        return getattr(exc, "code", None) == 429
    # transient network issues
    return isinstance(exc, (TimeoutError, ConnectionError))


class LLMClient:
    def __init__(self) -> None:
        config.validate()
        self._client = genai.Client(api_key=config.API_KEY)
        self._limiter = RateLimiter(config.MAX_REQUESTS_PER_MIN)
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------- caching helpers ----------------
    @staticmethod
    def _schema_repr(schema: Any) -> str:
        if schema is None:
            return ""
        try:
            # pydantic model class
            return json.dumps(schema.model_json_schema(), sort_keys=True)
        except Exception:
            return repr(schema)

    def _cache_key(
        self,
        prompt: str,
        image: Optional[tuple[bytes, str]],
        json_mode: bool,
        schema: Any,
        system_instruction: Optional[str],
        temperature: float,
        extra: str,
    ) -> str:
        img_sig = hashlib.sha256(image[0]).hexdigest() if image else ""
        material = json.dumps(
            {
                "prompt": prompt,
                "sys": system_instruction or "",
                "json": json_mode,
                "schema": self._schema_repr(schema),
                "temp": temperature,
                "img": img_sig,
                "extra": extra,
            },
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    # ---------------- low-level model call (retried) ----------------
    def _call(self, model_name: str, contents: list, gen_config: types.GenerateContentConfig) -> str:
        @retry(
            retry=retry_if_exception(_is_retryable),
            wait=wait_exponential(
                multiplier=config.RETRY_BASE_SECONDS, max=config.RETRY_MAX_SECONDS
            ),
            stop=stop_after_attempt(config.MAX_RETRIES),
            reraise=True,
        )
        def _do() -> str:
            self._limiter.acquire()
            resp = self._client.models.generate_content(
                model=model_name, contents=contents, config=gen_config
            )
            text = resp.text
            if not text or not text.strip():
                raise errors.ServerError(500, {"error": {"message": "empty response"}})
            return text

        return _do()

    # ---------------- public API ----------------
    def generate(
        self,
        prompt: str,
        image: Optional[tuple[bytes, str]] = None,
        *,
        json_mode: bool = False,
        response_schema: Any = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        cache_key_extra: str = "",
    ) -> str:
        """Return model text. `image` is (bytes, mime_type).

        Tries primary model then fallback; caches successful responses.
        """
        key = self._cache_key(
            prompt, image, json_mode, response_schema,
            system_instruction, temperature, cache_key_extra,
        )
        cache_file = config.CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            try:
                rec = json.loads(cache_file.read_text(encoding="utf-8"))
                log.info("cache hit (%s) model=%s", key[:8], rec.get("model"))
                return rec["text"]
            except Exception:
                log.warning("corrupt cache file %s; ignoring", cache_file.name)

        contents: list = []
        if image is not None:
            contents.append(types.Part.from_bytes(data=image[0], mime_type=image[1]))
        contents.append(prompt)

        gen_config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json" if json_mode else None,
            response_schema=response_schema,
            http_options=types.HttpOptions(timeout=config.REQUEST_TIMEOUT_SECONDS * 1000),
        )

        last_err: Optional[Exception] = None
        for i, model_name in enumerate(config.MODEL_CHAIN):
            try:
                log.info("calling %s (%s) key=%s", model_name,
                         "fallback" if i else "primary", key[:8])
                text = self._call(model_name, contents, gen_config)
                cache_file.write_text(
                    json.dumps({"model": model_name, "text": text}, ensure_ascii=False),
                    encoding="utf-8",
                )
                return text
            except Exception as exc:  # noqa: BLE001 - we record and try fallback
                last_err = exc
                log.warning("model %s failed: %s", model_name, exc)
                continue

        raise RuntimeError(f"all models failed for request {key[:8]}") from last_err
