"""Production Fireworks inference client for Track 1 (Rule 3).

All scored LLM inference must go through FIREWORKS_BASE_URL with
FIREWORKS_API_KEY. Both are read from os.environ only — no .env loading and no
default URLs/keys in this module.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from .allowed_models import ensure_model_allowed

logger = logging.getLogger(__name__)


class FireworksConfigError(RuntimeError):
    """Raised when required Fireworks environment variables are missing."""


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise FireworksConfigError(f"{name} must be set by the hackathon harness.")
    return value


def _dev_mock_enabled() -> bool:
    return os.environ.get("ALLOW_DEV_MOCK") == "1"


def generate_completion(
    prompt: str,
    model: str,
    max_tokens: int = 700,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Call Fireworks chat completions; validate model against ALLOWED_MODELS."""
    model = ensure_model_allowed(model)

    if _dev_mock_enabled() and model == "mock-remote-model":
        prompt_tokens = int(len(prompt.split()) * 1.3)
        completion_tokens = min(max_tokens, 80)
        total_tokens = prompt_tokens + completion_tokens
        return {
            "text": f"[MOCK REMOTE] Response for: {prompt[:80]}...",
            "tokens_input": prompt_tokens,
            "tokens_output": completion_tokens,
            "tokens_total": total_tokens,
            "tokens_estimated": total_tokens,
            "model": model,
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }

    api_key = _require_env("FIREWORKS_API_KEY")
    base_url = _require_env("FIREWORKS_BASE_URL")

    try:
        import requests
    except ImportError as exc:
        logger.error("requests is required for Fireworks inference: %s", exc)
        raise

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers, timeout=25)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error("Fireworks request failed for model %r: %s", model, exc)
        raise

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
    cost = (total_tokens / 1_000_000) * 0.5

    return {
        "text": text,
        "tokens_input": prompt_tokens,
        "tokens_output": completion_tokens,
        "tokens_total": total_tokens,
        "tokens_estimated": total_tokens,
        "model": model,
        "cost_credits": round(cost, 6),
        "cost_estimated": round(cost, 6),
    }