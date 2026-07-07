"""Thin wrapper around the production Fireworks client (Rule 3).

Scored inference must flow through fireworks_client.generate_completion so tokens
are recorded by the harness proxy. Do not add alternate HTTP endpoints here.
"""

from __future__ import annotations

from typing import Any, Dict

from .fireworks_client import generate_completion


def generate_remote(
    prompt: str,
    model: str,
    max_tokens: int = 700,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Run remote inference via FIREWORKS_BASE_URL (model is required, no default)."""
    return generate_completion(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )