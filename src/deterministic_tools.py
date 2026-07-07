"""Zero-token solvers for genuinely computable tasks (Rules 6 + 8).

Only pure computation is handled here (arithmetic, bounded counting). Word problems
with multiple named quantities must fall through to Fireworks.
"""

from __future__ import annotations

import ast
import operator
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from .allowed_models import OFFICIAL_TASK_TYPES

DETERMINISTIC_TASK_TYPE = "math_reasoning"

_COMMAND_MARKERS = (
    "what is",
    "calculate",
    "calcule",
    "quanto e",
    "compute",
    "evaluate",
    "solve",
)

# Units / narrative cues that indicate a multi-entity word problem, not pure arithmetic.
_WORD_PROBLEM_UNIT_PATTERNS = (
    r"\bkm/h\b",
    r"\bkm\b",
    r"\bmiles?\b",
    r"\bmi\b",
    r"\bhours?\b",
    r"\bhrs?\b",
    r"\bminutes?\b",
    r"\bmins?\b",
    r"\bseconds?\b",
    r"\bsec\b",
    r"\bpercent\b",
    r"\bprice\b",
    r"\bprices?\b",
    r"\bcost\b",
    r"\bcosts?\b",
    r"\brate\b",
    r"\brates?\b",
    r"\btax\b",
    r"\bdistance\b",
    r"\bspeed\b",
    r"\btime\b",
    r"\btravels?\b",
    r"\btrip\b",
    r"\baverage speed\b",
)

_NARRATIVE_MARKERS = (
    "then",
    "after",
    "before",
    "first",
    "second",
    "whole trip",
    "average speed",
    "travels",
    "travel",
    "per hour",
    "per minute",
    "in total",
    "combined",
)

_QUANTITY_PHRASE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:km/h|km|miles?|mi|hours?|hrs?|minutes?|mins?|seconds?|sec|%)",
    re.IGNORECASE,
)

_PURE_ARITHMETIC_CHARS = re.compile(r"^[\d\s+\-*/().%^]+$")
_PERCENT_OF = re.compile(r"^(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)$", re.IGNORECASE)


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


def is_word_problem_with_named_quantities(task_content: str) -> bool:
    """Detect multi-entity math word problems that must not use regex extraction."""
    normalized = _normalized(task_content)

    quantity_phrases = _QUANTITY_PHRASE.findall(normalized)
    if len(quantity_phrases) >= 2:
        return True

    unit_hits = sum(1 for pattern in _WORD_PROBLEM_UNIT_PATTERNS if re.search(pattern, normalized))
    if unit_hits >= 2:
        return True

    numbers = re.findall(r"\d+(?:\.\d+)?", normalized)
    narrative_hits = sum(1 for marker in _NARRATIVE_MARKERS if marker in normalized)
    if len(numbers) >= 2 and narrative_hits >= 1:
        return True

    return False


def extract_pure_arithmetic_expression(task_content: str) -> Optional[str]:
    """Return a safe arithmetic expression only for reducible pure-math prompts."""
    if is_word_problem_with_named_quantities(task_content):
        return None

    normalized = _normalized(task_content)
    has_command = any(marker in normalized for marker in _COMMAND_MARKERS)

    working = task_content.replace("^", "**").strip()
    for marker in _COMMAND_MARKERS:
        working = re.sub(rf"(?i){re.escape(marker)}\s*", "", working)
    working = working.strip().rstrip("?").strip()
    working = re.sub(r"\([^)]*[a-zA-Z][^)]*\)", "", working).strip()

    if not working:
        return None

    residual = _normalized(working)

    percent_of = _PERCENT_OF.fullmatch(residual)
    if percent_of:
        return f"{percent_of.group(1)} * {percent_of.group(2)} / 100"

    if _PURE_ARITHMETIC_CHARS.fullmatch(residual):
        expression = residual
    elif has_command:
        operator_chunks = re.findall(r"[\d\s+\-*/().%^]+", working)
        operator_chunks = [
            chunk.strip()
            for chunk in operator_chunks
            if re.search(r"\d", chunk) and re.search(r"[+\-*/%]", chunk)
        ]
        if len(operator_chunks) != 1:
            return None
        expression = operator_chunks[0]
    else:
        return None

    expression = expression.replace("%", " / 100 * ").strip()
    expression = re.sub(r"\s+", " ", expression)

    if not expression or len(expression) > 80:
        return None
    if not re.search(r"[+\-*/]", expression):
        return None

    return expression


def is_pure_arithmetic(task_content: str) -> bool:
    """True only when the prompt reduces to a single safe arithmetic expression."""
    return extract_pure_arithmetic_expression(task_content) is not None


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _normalized(text: str) -> str:
    return _compact(_strip_accents(text))


def _try_counting(task_content: str) -> Optional[DeterministicResult]:
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
    expression = extract_pure_arithmetic_expression(task_content)
    if not expression:
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