"""Zero-token solvers for genuinely computable tasks (Rules 6 + 8).

Only pure computation is handled here (arithmetic, bounded counting). Canned
fact templates and domain-specific hardcoded answers were removed because the
harness uses unseen variants and those patterns violate Rule 6.
"""

from __future__ import annotations

import ast
import operator
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from .allowed_models import OFFICIAL_TASK_TYPES

# Rule 5: deterministic shortcuts only tag official evaluation categories.
DETERMINISTIC_TASK_TYPE = "math_reasoning"


@dataclass
class DeterministicResult:
    text: str
    task_type: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.task_type not in OFFICIAL_TASK_TYPES:
            raise ValueError(f"Invalid deterministic task_type: {self.task_type}")


_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def try_deterministic(task_content: str) -> Optional[DeterministicResult]:
    """Answer high-confidence computable tasks without any LLM call (Rule 8)."""
    counting = _try_counting(task_content)
    if counting:
        return counting

    arithmetic = _try_simple_arithmetic(task_content)
    if arithmetic:
        return arithmetic

    return None


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _normalized(text: str) -> str:
    return _compact(_strip_accents(text))


def _try_counting(task_content: str) -> Optional[DeterministicResult]:
    """Emit a comma-separated integer sequence when bounds are explicit."""
    normalized = _normalized(task_content)
    match = re.search(
        r"\b(?:count|conte|conta)\s+(?:from|de)\s+(-?\d+)\s+(?:to|ate|até|a)\s+(-?\d+)\b",
        normalized,
    )
    if not match:
        return None

    start = int(match.group(1))
    end = int(match.group(2))
    step = 1 if end >= start else -1
    length = abs(end - start) + 1
    if length > 250:
        return None

    numbers = [str(number) for number in range(start, end + step, step)]
    return DeterministicResult(
        text=", ".join(numbers),
        task_type=DETERMINISTIC_TASK_TYPE,
        confidence=1.0,
    )


def _try_simple_arithmetic(task_content: str) -> Optional[DeterministicResult]:
    """Safely evaluate a short arithmetic expression embedded in the prompt."""
    normalized = _normalized(task_content)
    if not any(marker in normalized for marker in ["what is", "calculate", "calcule", "quanto e"]):
        return None

    candidates = re.findall(r"[-+*/().\d\s%^]+", task_content.replace("^", "**"))
    candidates = [item.strip() for item in candidates if re.search(r"\d", item)]
    if not candidates:
        return None

    expression = max(candidates, key=len)
    if not expression or len(expression) > 80:
        return None

    try:
        value = _safe_eval(expression)
    except Exception:
        return None

    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return DeterministicResult(text=str(value), task_type=DETERMINISTIC_TASK_TYPE)


def _safe_eval(expression: str):
    node = ast.parse(expression, mode="eval")
    return _eval_node(node.body)


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return _ALLOWED_UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")