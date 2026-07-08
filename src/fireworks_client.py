"""Production Fireworks inference client for Track 1 (Rule 3).

All scored LLM inference must go through FIREWORKS_BASE_URL with
FIREWORKS_API_KEY. Both are read from os.environ only — no .env loading and no
default URLs/keys in this module.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from .allowed_models import ensure_model_allowed, get_allowed_models

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS_PER_MODEL = 2


class FireworksConfigError(RuntimeError):
    """Raised when required Fireworks environment variables are missing."""


class FireworksCompletionError(RuntimeError):
    """Raised when Fireworks returns no usable completion text after retries."""


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise FireworksConfigError(f"{name} must be set by the hackathon harness.")
    return value


def _chat_completions_url(base_url: str) -> str:
    """Accept either the harness base URL or a full chat/completions URL.

    Some docs show `$FIREWORKS_BASE_URL/chat/completions`, while local dev often
    uses the complete `.../chat/completions` endpoint. Supporting both keeps all
    scored inference on the harness-provided URL without baking in credentials.
    """
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def _dev_mock_enabled() -> bool:
    return os.environ.get("ALLOW_DEV_MOCK") == "1"


def _extract_choice_text(choice: Dict[str, Any]) -> str:
    """Normalize OpenAI-compatible choice payloads into plain completion text."""
    message = choice.get("message")
    if not isinstance(message, dict):
        return ""

    for key in ("content", "text"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    content = message.get("content")
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, str) and part.strip():
                parts.append(part.strip())
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        joined = "\n".join(parts).strip()
        if joined:
            return joined

    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        return refusal.strip()

    return ""


def _extract_completion_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise FireworksCompletionError("Fireworks response missing choices.")

    for choice in choices:
        if not isinstance(choice, dict):
            continue
        text = _extract_choice_text(choice)
        if text:
            return text

    finish_reasons = [
        str(choice.get("finish_reason", ""))
        for choice in choices
        if isinstance(choice, dict)
    ]
    raise FireworksCompletionError(
        "Fireworks returned an empty completion "
        f"(finish_reason={finish_reasons or 'unknown'})."
    )


def _models_to_try(primary_model: str) -> List[str]:
    models = [primary_model]
    for candidate in get_allowed_models():
        if candidate not in models:
            models.append(candidate)
    return models


def _post_chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
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

    response = requests.post(base_url, json=payload, headers=headers, timeout=25)
    response.raise_for_status()
    data = response.json()

    text = _extract_completion_text(data)
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
    base_url = _chat_completions_url(_require_env("FIREWORKS_BASE_URL"))

    errors: List[Exception] = []
    for candidate_model in _models_to_try(model):
        attempt_max_tokens = max_tokens
        for attempt in range(_MAX_ATTEMPTS_PER_MODEL):
            try:
                result = _post_chat_completion(
                    api_key=api_key,
                    base_url=base_url,
                    model=candidate_model,
                    prompt=prompt,
                    max_tokens=attempt_max_tokens,
                    temperature=temperature,
                )
                if attempt > 0 or candidate_model != model:
                    logger.info(
                        "Fireworks completion recovered with model=%r attempt=%d",
                        candidate_model,
                        attempt + 1,
                    )
                return result
            except Exception as exc:
                errors.append(exc)
                if isinstance(exc, FireworksCompletionError) and "'length'" in str(exc):
                    attempt_max_tokens = min(max(attempt_max_tokens * 2, max_tokens + 200), 1400)
                logger.warning(
                    "Fireworks completion failed for model=%r attempt=%d: %s",
                    candidate_model,
                    attempt + 1,
                    exc,
                )

    detail = errors[-1] if errors else "unknown error"
    logger.error("Fireworks exhausted retries/fallbacks for initial model %r", model)
    if isinstance(detail, Exception):
        raise FireworksCompletionError(
            f"Fireworks returned no usable completion after retries: {detail}"
        ) from detail
    raise FireworksCompletionError(
        f"Fireworks returned no usable completion after retries: {detail}"
    )