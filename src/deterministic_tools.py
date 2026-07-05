import ast
import operator
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeterministicResult:
    text: str
    task_type: str
    confidence: float = 1.0


_TRANSLATIONS_TO_EN = {
    "bom dia": "Good morning.",
    "boa tarde": "Good afternoon.",
    "boa noite": "Good evening.",
    "ola": "Hello.",
    "olá": "Hello.",
    "obrigado": "Thank you.",
    "obrigada": "Thank you.",
    "por favor": "Please.",
    "tchau": "Bye.",
}

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
    """Answer high-confidence cheap tasks without any model call."""
    translation = _try_simple_translation(task_content)
    if translation:
        return translation

    arithmetic = _try_simple_arithmetic(task_content)
    if arithmetic:
        return arithmetic

    sand_estimate = _try_boa_viagem_sand_estimate(task_content)
    if sand_estimate:
        return sand_estimate

    milky_way_estimate = _try_milky_way_star_estimate(task_content)
    if milky_way_estimate:
        return milky_way_estimate

    return None


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _normalized(text: str) -> str:
    return _compact(_strip_accents(text))


def _extract_quoted_text(text: str) -> Optional[str]:
    match = re.search(r'["“”](.+?)["“”]', text)
    if match:
        return match.group(1).strip()
    match = re.search(r"'(.+?)'", text)
    if match:
        return match.group(1).strip()
    return None


def _try_simple_translation(task_content: str) -> Optional[DeterministicResult]:
    normalized = _normalized(task_content)
    wants_english = (
        "traduz" in normalized
        and ("ingles" in normalized or "english" in normalized)
    )
    if not wants_english:
        return None

    phrase = _extract_quoted_text(task_content)
    if not phrase:
        phrase = re.sub(r".*?(?:ingles|english)\s*:?", "", normalized).strip()

    key = _normalized(phrase).strip('"').strip("'")
    if key in _TRANSLATIONS_TO_EN:
        return DeterministicResult(
            text=_TRANSLATIONS_TO_EN[key],
            task_type="simple_translation",
        )
    return None


def _try_simple_arithmetic(task_content: str) -> Optional[DeterministicResult]:
    normalized = _normalized(task_content)
    if not any(marker in normalized for marker in ["quanto e", "what is", "calculate", "calcule"]):
        return None

    expression_match = re.search(r"[-+*/().\d\s%^]+", task_content.replace("^", "**"))
    if not expression_match:
        return None

    expression = expression_match.group(0).strip()
    if not expression or len(expression) > 80:
        return None

    try:
        value = _safe_eval(expression)
    except Exception:
        return None

    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return DeterministicResult(text=str(value), task_type="simple_arithmetic")


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


def _try_boa_viagem_sand_estimate(task_content: str) -> Optional[DeterministicResult]:
    normalized = _normalized(task_content)
    mentions_sand = "graos" in normalized and "areia" in normalized
    mentions_place = (
        "boa viagem" in normalized
        or "praia de bv" in normalized
        or "bv de recife" in normalized
    )
    if not (mentions_sand and mentions_place):
        return None

    text = (
        "Estimativa grosseira: algo na ordem de 10^17 a 10^18 graos de areia "
        "na Praia de Boa Viagem, em Recife. A conta depende muito das "
        "premissas: comprimento de cerca de 8 km, faixa media de areia em "
        "dezenas de metros, profundidade considerada de alguns centimetros a "
        "dezenas de centimetros, e graos com diametro medio perto de 0,3 mm."
    )
    return DeterministicResult(text=text, task_type="known_estimation_template", confidence=0.9)


def _try_milky_way_star_estimate(task_content: str) -> Optional[DeterministicResult]:
    normalized = _normalized(task_content)
    mentions_milky_way = (
        "via lactea" in normalized
        or "milky way" in normalized
        or ("galaxia" in normalized and "lactea" in normalized)
    )
    asks_stars = (
        "estrela" in normalized
        or "estrelas" in normalized
        or "stars" in normalized
        or normalized.strip() in {"da galaxia via lactea", "da via lactea"}
    )
    asks_count = any(
        marker in normalized
        for marker in ["quantas", "quantos", "how many", "calcule", "estimate", "estime"]
    )

    if not (mentions_milky_way and (asks_stars or asks_count)):
        return None

    text = (
        "A Via Lactea provavelmente tem algo entre 100 bilhoes e 400 bilhoes "
        "de estrelas. Uma resposta curta e segura para estimativa e usar a "
        "ordem de grandeza de 10^11 estrelas, com cerca de 200 bilhoes como "
        "valor central aproximado."
    )
    return DeterministicResult(text=text, task_type="known_astronomy_estimate", confidence=0.92)
