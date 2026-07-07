"""DEV/TEST ONLY — never use for Track 1 final answers (Rule 4).

generate_local may help during local development or as an optional routing
classifier experiment, but HybridRouter does NOT call it for submission output.
Final answers must come from try_deterministic (zero tokens) or Fireworks remote.

Set ALLOW_LOCAL_DEV=1 to use this module from scripts/smoke_local_model.py.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from .config import (
    LOCAL_MAX_TOKENS,
    LOCAL_MODEL_NAME,
    LOCAL_OPENAI_API_KEY,
    LOCAL_OPENAI_BASE_URL,
    LOCAL_PROVIDER,
    LOCAL_TEMPERATURE,
    OLLAMA_BASE_URL,
)

def _local_dev_allowed() -> bool:
    return os.environ.get("ALLOW_LOCAL_DEV", "0") == "1"


def _require_local_dev() -> None:
    if not _local_dev_allowed():
        raise RuntimeError(
            "generate_local is dev-only. Set ALLOW_LOCAL_DEV=1 for local experiments. "
            "Submission answers must use Fireworks (Rule 4)."
        )


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.3))


def generate_local(prompt: str, model: str = LOCAL_MODEL_NAME) -> Dict[str, Any]:
    """DEV ONLY: local Ollama/vLLM/mock inference — not scored by the harness."""
    _require_local_dev()

    if LOCAL_PROVIDER == "mock":
        text = f"[MOCK LOCAL] {prompt[:120]}"
        return _success_response(prompt, text, model)
    if LOCAL_PROVIDER in {"openai", "openai_compatible", "vllm"}:
        return _generate_openai_compatible(prompt, model)
    return _generate_ollama(prompt, model)


def _generate_ollama(prompt: str, model: str) -> Dict[str, Any]:
    try:
        import requests
    except ImportError as exc:
        return _error_response(prompt, model, f"requests is not installed: {exc}")

    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_BASE_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "")
        prompt_tokens = data.get("prompt_eval_count") or _estimate_tokens(prompt)
        completion_tokens = data.get("eval_count") or _estimate_tokens(text)
        return _success_response(prompt, text, model, prompt_tokens, completion_tokens)
    except Exception as exc:
        return _error_response(prompt, model, str(exc))


def _generate_openai_compatible(prompt: str, model: str) -> Dict[str, Any]:
    try:
        import requests
    except ImportError as exc:
        return _error_response(prompt, model, f"requests is not installed: {exc}")

    headers = {
        "Authorization": f"Bearer {LOCAL_OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": LOCAL_MAX_TOKENS,
        "temperature": LOCAL_TEMPERATURE,
    }
    try:
        response = requests.post(LOCAL_OPENAI_BASE_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens") or _estimate_tokens(prompt)
        completion_tokens = usage.get("completion_tokens") or _estimate_tokens(text)
        return _success_response(prompt, text, model, prompt_tokens, completion_tokens)
    except Exception as exc:
        return _error_response(prompt, model, str(exc))


def _success_response(
    prompt: str,
    text: str,
    model: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> Dict[str, Any]:
    prompt_tokens = prompt_tokens if prompt_tokens is not None else _estimate_tokens(prompt)
    completion_tokens = completion_tokens if completion_tokens is not None else _estimate_tokens(text)
    return {
        "text": text,
        "tokens_input": prompt_tokens,
        "tokens_output": completion_tokens,
        "tokens_total": prompt_tokens + completion_tokens,
        "model": model,
        "provider": LOCAL_PROVIDER,
        "cost_credits": 0.0,
        "dev_only": True,
    }


def _error_response(prompt: str, model: str, error: str) -> Dict[str, Any]:
    prompt_tokens = _estimate_tokens(prompt)
    return {
        "text": f"Error calling local model: {error}",
        "tokens_input": prompt_tokens,
        "tokens_output": 0,
        "tokens_total": prompt_tokens,
        "model": model,
        "provider": LOCAL_PROVIDER,
        "cost_credits": 0.0,
        "dev_only": True,
    }