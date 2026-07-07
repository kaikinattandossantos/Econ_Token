"""Embedding-based task classifier — routing signal only (Rule 4).

Prototypes use only the 8 official Track 1 categories (Rule 5). This module
never produces final answers for results.json.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional

from .config import (
    ENABLE_SEMANTIC_ROUTER,
    SEMANTIC_ROUTER_FALLBACK_MODEL,
    SEMANTIC_ROUTER_MODEL,
    SEMANTIC_ROUTER_THRESHOLD,
)


@dataclass
class SemanticRoute:
    label: str
    route_hint: str
    task_type: str
    domain: str
    expected_answer: str
    score: float
    model: str
    matched_description: str


_ROUTE_PROTOTYPES: Dict[str, Dict[str, str]] = {
    "math_reasoning": {
        "description": "math arithmetic counting numbers solve equation step by step calculation",
        "route_hint": "deterministic",
        "task_type": "math_reasoning",
        "domain": "math",
        "expected_answer": "number_or_short_reasoned_solution",
    },
    "factual_qa": {
        "description": "factual question answer who what where when how many world knowledge",
        "route_hint": "remote",
        "task_type": "factual_qa",
        "domain": "factual",
        "expected_answer": "concise_factual_answer",
    },
    "sentiment": {
        "description": "classify sentiment positive negative neutral opinion analysis",
        "route_hint": "remote",
        "task_type": "sentiment",
        "domain": "language",
        "expected_answer": "label_only",
    },
    "summarization": {
        "description": "summarize long text short summary main points tl dr",
        "route_hint": "remote",
        "task_type": "summarization",
        "domain": "language",
        "expected_answer": "short_summary",
    },
    "ner": {
        "description": "named entity recognition extract people places organizations dates",
        "route_hint": "remote",
        "task_type": "ner",
        "domain": "language",
        "expected_answer": "structured_entities",
    },
    "code_debugging": {
        "description": "debug code error traceback bug fix programming issue",
        "route_hint": "remote",
        "task_type": "code_debugging",
        "domain": "software",
        "expected_answer": "bug_fix_or_explanation",
    },
    "code_generation": {
        "description": "generate code implement function write class algorithm program",
        "route_hint": "remote",
        "task_type": "code_generation",
        "domain": "software",
        "expected_answer": "working_code",
    },
    "logical_reasoning": {
        "description": "logic puzzle riddle deduction constraints reasoning problem",
        "route_hint": "remote",
        "task_type": "logical_reasoning",
        "domain": "reasoning",
        "expected_answer": "concise_reasoned_answer",
    },
}


def semantic_route(task: str) -> Optional[SemanticRoute]:
    if not ENABLE_SEMANTIC_ROUTER:
        return None

    router = _load_router()
    if router is None:
        return None
    return router.route(task)


class _SemanticRouter:
    def __init__(self, model_name: str, model):
        self.model_name = model_name
        self.model = model
        self.labels = list(_ROUTE_PROTOTYPES.keys())
        self.descriptions = [_ROUTE_PROTOTYPES[label]["description"] for label in self.labels]
        self.prototype_embeddings = self.model.encode(
            self.descriptions,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

    def route(self, task: str) -> Optional[SemanticRoute]:
        try:
            import torch
        except ImportError:
            torch = None

        task_embedding = self.model.encode(
            task,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
        scores = self.prototype_embeddings @ task_embedding
        if torch is not None:
            best_idx = int(torch.argmax(scores).item())
            best_score = float(scores[best_idx].item())
        else:
            values = scores.tolist()
            best_idx = max(range(len(values)), key=lambda idx: values[idx])
            best_score = float(values[best_idx])

        if best_score < SEMANTIC_ROUTER_THRESHOLD:
            return None

        label = self.labels[best_idx]
        meta = _ROUTE_PROTOTYPES[label]
        return SemanticRoute(
            label=label,
            route_hint=meta["route_hint"],
            task_type=meta["task_type"],
            domain=meta["domain"],
            expected_answer=meta["expected_answer"],
            score=round(best_score, 4),
            model=self.model_name,
            matched_description=meta["description"],
        )


def _hub_offline_mode() -> bool:
    flag = os.environ.get("HF_HUB_OFFLINE", "0").strip().lower()
    return flag in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def _load_router() -> Optional[_SemanticRouter]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    local_only = _hub_offline_mode()
    errors: List[Exception] = []
    for model_name in [SEMANTIC_ROUTER_MODEL, SEMANTIC_ROUTER_FALLBACK_MODEL]:
        try:
            return _SemanticRouter(
                model_name,
                SentenceTransformer(model_name, local_files_only=local_only),
            )
        except Exception as exc:
            errors.append(exc)
            continue
    return None