"""Cheap routing specialists — classification only, never final answers (Rule 4).

All task_type values are normalized to the 8 official Track 1 categories (Rule 5).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .allowed_models import normalize_task_type
from .semantic_router import semantic_route


@dataclass
class TaskProfile:
    raw_task: str
    normalized_task: str
    task_type: str = "factual_qa"
    domain: str = "general"
    complexity: float = 0.2
    risk: float = 0.1
    template_fit: float = 0.0
    expected_answer: str = "concise_answer"
    constraints: Dict[str, Any] = field(default_factory=dict)
    signals: List[str] = field(default_factory=list)
    semantic: Dict[str, Any] = field(default_factory=dict)
    route_hint: str = "remote"

    @property
    def score(self) -> float:
        return min(1.0, max(0.0, (self.complexity * 0.55) + (self.risk * 0.45)))

    def finalize_task_type(self) -> None:
        self.task_type = normalize_task_type(self.task_type)


def analyze_task(task: str) -> TaskProfile:
    profile = TaskProfile(raw_task=task, normalized_task=_normalize(task))
    _intent_specialist(profile)
    _entity_specialist(profile)
    _semantic_specialist(profile)
    _risk_specialist(profile)
    _contract_specialist(profile)
    _routing_specialist(profile)
    profile.finalize_task_type()
    return profile


def build_remote_prompt(task: str, profile: TaskProfile) -> str:
    """Compressed Fireworks prompt; final answer must be English (Rule 1)."""
    requirements = _requirements_line(profile)
    return (
        "Respond in English only.\n"
        f"Task: {task}\n"
        f"Category: {profile.task_type}; domain: {profile.domain}; "
        f"expected format: {profile.expected_answer}.\n"
        f"{requirements}\n"
        "Return only the final useful answer. Be concise and accurate."
    )


def _semantic_specialist(profile: TaskProfile) -> None:
    semantic = semantic_route(profile.raw_task)
    if not semantic:
        profile.signals.append("semantic_router_unavailable_or_low_confidence")
        return

    profile.semantic = {
        "label": semantic.label,
        "score": semantic.score,
        "model": semantic.model,
        "matched_description": semantic.matched_description,
    }
    profile.signals.append(f"semantic:{semantic.label}:{semantic.score}")

    if semantic.score >= 0.48:
        profile.task_type = semantic.task_type
        profile.domain = semantic.domain
        profile.expected_answer = semantic.expected_answer
        profile.route_hint = semantic.route_hint
        if semantic.route_hint == "deterministic":
            profile.template_fit = max(profile.template_fit, 0.95)
        else:
            profile.complexity = max(profile.complexity, 0.45)


def _intent_specialist(profile: TaskProfile) -> None:
    text = profile.normalized_task

    if any(marker in text for marker in ["sentiment", "classify the sentiment", "positive", "negative", "neutral"]):
        profile.task_type = "sentiment"
        profile.domain = "language"
        profile.signals.append("track1_sentiment")
        return

    if any(marker in text for marker in ["summarize", "summary", "tl;dr", "resuma", "resumir"]):
        profile.task_type = "summarization"
        profile.domain = "language"
        profile.signals.append("track1_summarization")
        return

    if any(marker in text for marker in ["ner", "named entity", "extract entities", "entidades nomeadas"]):
        profile.task_type = "ner"
        profile.domain = "language"
        profile.signals.append("track1_ner")
        return

    if any(marker in text for marker in ["debug", "bug", "traceback", "stack trace", "fix the error", "corrija o erro"]):
        profile.task_type = "code_debugging"
        profile.domain = "software"
        profile.complexity = max(profile.complexity, 0.65)
        profile.signals.append("track1_code_debugging")
        return

    if any(marker in text for marker in ["write code", "generate code", "implement", "create a function", "crie uma funcao"]):
        profile.task_type = "code_generation"
        profile.domain = "software"
        profile.complexity = max(profile.complexity, 0.65)
        profile.signals.append("track1_code_generation")
        return

    if any(marker in text for marker in ["logic puzzle", "riddle", "deduce", "logica", "logical reasoning"]):
        profile.task_type = "logical_reasoning"
        profile.domain = "reasoning"
        profile.complexity = max(profile.complexity, 0.7)
        profile.signals.append("track1_logical_reasoning")
        return

    if any(marker in text for marker in ["math reasoning", "prove", "step by step", "solve for", "equation"]):
        profile.task_type = "math_reasoning"
        profile.domain = "math"
        profile.complexity = max(profile.complexity, 0.7)
        profile.signals.append("track1_math_reasoning")
        return

    if re.search(r"\b(?:count|conte|conta)\s+(?:from|de)\s+-?\d+\s+(?:to|ate|a)\s+-?\d+\b", text):
        profile.task_type = "math_reasoning"
        profile.domain = "math"
        profile.template_fit = 1.0
        profile.signals.append("counting_range")
        return

    if _looks_like_arithmetic(text):
        profile.task_type = "math_reasoning"
        profile.domain = "math"
        profile.template_fit = 0.95
        profile.signals.append("arithmetic_expression")
        return

    if any(marker in text for marker in ["how many", "what is", "who is", "where is", "when did", "quantos", "quantas"]):
        profile.task_type = "factual_qa"
        profile.domain = "factual"
        profile.signals.append("track1_factual_qa")
        return

    if any(marker in text for marker in ["code", "function", "algorithm", "python", "javascript"]):
        profile.task_type = "code_debugging"
        profile.domain = "software"
        profile.signals.append("track1_code_fallback")


def _entity_specialist(profile: TaskProfile) -> None:
    text = profile.normalized_task
    range_match = re.search(
        r"\b(?:count|conte|conta)\s+(?:from|de)\s+(-?\d+)\s+(?:to|ate|a)\s+(-?\d+)\b",
        text,
    )
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        profile.constraints["range"] = [start, end]
        profile.constraints["range_len"] = abs(end - start) + 1


def _risk_specialist(profile: TaskProfile) -> None:
    text = profile.normalized_task
    risk_terms = {
        "medical": ["medical", "diagnosis", "symptom", "disease"],
        "legal": ["legal", "contract", "lawsuit", "law"],
        "financial": ["financial", "investment", "credit", "loan", "tax"],
    }
    for domain, terms in risk_terms.items():
        if any(term in text for term in terms):
            profile.risk = max(profile.risk, 0.85)
            profile.domain = domain
            profile.signals.append(f"high_risk_{domain}")

    if profile.constraints.get("range_len", 0) > 250:
        profile.complexity = max(profile.complexity, 0.8)


def _contract_specialist(profile: TaskProfile) -> None:
    contracts = {
        "math_reasoning": "number_or_short_reasoned_solution",
        "sentiment": "label_only",
        "summarization": "short_summary",
        "ner": "structured_entities",
        "code_debugging": "bug_fix_or_explanation",
        "code_generation": "working_code",
        "logical_reasoning": "concise_reasoned_answer",
        "factual_qa": "concise_factual_answer",
    }
    profile.expected_answer = contracts.get(profile.task_type, "concise_factual_answer")


def _routing_specialist(profile: TaskProfile) -> None:
    if profile.template_fit >= 0.9:
        profile.route_hint = "deterministic"
    else:
        profile.route_hint = "remote"


def _requirements_line(profile: TaskProfile) -> str:
    bits = []
    mapping = {
        "label_only": "Return only the sentiment label.",
        "short_summary": "Return a compact summary.",
        "structured_entities": "Return entities grouped by type.",
        "working_code": "Return minimal correct code.",
        "bug_fix_or_explanation": "Return the smallest useful fix or explanation.",
        "concise_reasoned_answer": "Use brief reasoning, then the answer.",
        "number_or_short_reasoned_solution": "Return the numeric result or concise solution.",
        "concise_factual_answer": "Return the factual answer only.",
    }
    if profile.expected_answer in mapping:
        bits.append(mapping[profile.expected_answer])
    if profile.constraints:
        bits.append(f"Constraints: {profile.constraints}.")
    return " ".join(bits) if bits else "No extra context."


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.strip().lower())


def _looks_like_arithmetic(text: str) -> bool:
    if not any(marker in text for marker in ["what is", "calculate", "calcule", "quanto e"]):
        return False
    return bool(re.search(r"\d\s*[-+*/]\s*\d", text))