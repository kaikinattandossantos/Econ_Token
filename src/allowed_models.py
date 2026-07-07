"""Runtime model allow-list for Track 1 (Rule 2 + validation).

ALLOWED_MODELS is injected by the hackathon harness at runtime. Model IDs must
never be hardcoded in routing code; always read and validate against this list.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import List

logger = logging.getLogger(__name__)

# Official Track 1 evaluation categories (Rule 5).
OFFICIAL_TASK_TYPES = frozenset(
    {
        "factual_qa",
        "math_reasoning",
        "sentiment",
        "summarization",
        "ner",
        "code_debugging",
        "logical_reasoning",
        "code_generation",
    }
)

# Legacy / heuristic labels mapped into the official set.
TASK_TYPE_ALIASES = {
    "sequence": "math_reasoning",
    "arithmetic": "math_reasoning",
    "logic_puzzle": "logical_reasoning",
    "coding": "code_debugging",
    "estimation": "factual_qa",
    "open_qa": "factual_qa",
    "translation": "factual_qa",
    "plan_generation": "factual_qa",
    "rewrite": "summarization",
    "high_risk": "factual_qa",
    "reasoning": "logical_reasoning",
}


def normalize_task_type(task_type: str) -> str:
    """Reclassify any non-official label into one of the 8 allowed categories."""
    if task_type in OFFICIAL_TASK_TYPES:
        return task_type
    return TASK_TYPE_ALIASES.get(task_type, "factual_qa")


def get_allowed_models() -> List[str]:
    """Read ALLOWED_MODELS from the environment at call time (Rule 2)."""
    raw = os.environ.get("ALLOWED_MODELS", "").strip()
    if not raw:
        if os.environ.get("ALLOW_DEV_MOCK") == "1":
            return ["mock-remote-model"]
        logger.error("ALLOWED_MODELS is not set; cannot select a remote model.")
        sys.exit(1)

    models = [item.strip() for item in raw.split(",") if item.strip()]
    if not models:
        logger.error("ALLOWED_MODELS is empty after parsing.")
        sys.exit(1)
    return models


def ensure_model_allowed(model: str) -> str:
    """Fail fast if the chosen model is outside ALLOWED_MODELS (Rule 2)."""
    allowed = get_allowed_models()
    if model not in allowed:
        logger.error(
            "Selected model %r is not in ALLOWED_MODELS: %s",
            model,
            allowed,
        )
        sys.exit(1)
    return model