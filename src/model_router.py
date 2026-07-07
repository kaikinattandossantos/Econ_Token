"""Dynamic remote model selection from ALLOWED_MODELS (Rule 2).

No model IDs are imported from config constants. Preferences are expressed as
name-pattern tiers per official category; the cheapest matching allowed model wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .allowed_models import ensure_model_allowed, get_allowed_models, normalize_task_type
from .specialist_agents import TaskProfile

# Pattern tiers: earlier patterns are preferred (cheaper / sufficient first).
# Patterns match substrings of the runtime model id — not hardcoded full IDs.
_CATEGORY_PATTERN_TIERS: Dict[str, List[str]] = {
    "sentiment": ["minimax", "26b", "31b", "kimi", "gemma"],
    "ner": ["minimax", "26b", "31b", "kimi", "gemma"],
    "summarization": ["26b", "minimax", "31b", "kimi", "gemma"],
    "factual_qa": ["26b", "minimax", "31b", "kimi", "gemma"],
    "math_reasoning": ["31b", "26b", "kimi", "minimax", "gemma"],
    "logical_reasoning": ["31b", "26b", "kimi", "minimax", "gemma"],
    "code_debugging": ["kimi", "31b", "26b", "minimax", "gemma"],
    "code_generation": ["kimi", "31b", "26b", "minimax", "gemma"],
}

# Token budgets tuned for the 30s/task harness limit (Rule 7).
_CATEGORY_MAX_TOKENS: Dict[str, int] = {
    "sentiment": 64,
    "ner": 256,
    "summarization": 384,
    "factual_qa": 384,
    "math_reasoning": 512,
    "logical_reasoning": 512,
    "code_debugging": 768,
    "code_generation": 768,
}


@dataclass
class ModelDecision:
    model: str
    reason: str
    max_tokens: int
    temperature: float = 0.0


def _pattern_rank(model_id: str, patterns: Sequence[str]) -> Tuple[int, int]:
    lowered = model_id.lower()
    for index, pattern in enumerate(patterns):
        if pattern in lowered:
            return index, len(model_id)
    return len(patterns), len(model_id)


def _rank_models_for_category(category: str, allowed: Sequence[str]) -> List[str]:
    patterns = _CATEGORY_PATTERN_TIERS.get(category, _CATEGORY_PATTERN_TIERS["factual_qa"])
    return sorted(allowed, key=lambda model_id: _pattern_rank(model_id, patterns))


def select_remote_model(profile: TaskProfile) -> ModelDecision:
    """Pick the cheapest allowed model likely to pass accuracy for the category."""
    category = normalize_task_type(profile.task_type)
    allowed = get_allowed_models()
    ranked = _rank_models_for_category(category, allowed)
    chosen = ensure_model_allowed(ranked[0])

    max_tokens = _CATEGORY_MAX_TOKENS.get(category, 384)
    if profile.complexity >= 0.75:
        max_tokens = min(max_tokens + 128, 768)
    if profile.risk >= 0.8:
        max_tokens = min(max_tokens + 128, 768)

    return ModelDecision(
        model=chosen,
        reason=f"allowed_models_ranked_for_{category}",
        max_tokens=max_tokens,
        temperature=0.0,
    )