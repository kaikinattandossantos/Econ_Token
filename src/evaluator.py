import re
from .task_types import Task

_COMPLEX_KEYWORDS = [
    "prove",
    "calculate",
    "calcule",
    "debug",
    "depure",
    "optimize",
    "otimize",
    "legal",
    "medical",
    "medico",
    "médico",
    "financial",
    "financeiro",
    "step by step",
    "passo a passo",
    "diagnosis",
    "diagnostico",
    "diagnóstico",
    "architecture",
    "arquitetura",
]

_ESTIMATION_MARKERS = [
    "quantos",
    "how many",
    "estimativa",
    "estime",
    "provavelmente",
    "aproximadamente",
]

_TRANSLATION_MARKERS = ["traduz", "translate", "traduza"]


def estimate_task_difficulty(task_content: str) -> float:
    """Estimate task difficulty from 0.0 to 1.0."""
    lowered = task_content.lower()
    score = 0.0

    matched_complex_keywords = sum(1 for word in _COMPLEX_KEYWORDS if word in lowered)
    if matched_complex_keywords:
        score += min(0.8, 0.25 * matched_complex_keywords)

    if any(word in lowered for word in _ESTIMATION_MARKERS):
        score += 0.35

    if any(word in lowered for word in ["code", "codigo", "código", "function", "bug", "traceback"]):
        score += 0.25

    if len(task_content.split()) > 50:
        score += 0.2

    if re.search(r"```[a-z]*\n", task_content):
        score += 0.3

    if "?" in task_content and task_content.count("?") > 2:
        score += 0.2

    if _is_simple_translation_task(task_content):
        score = min(score, 0.15)

    return min(score, 1.0)

def estimate_local_confidence(task_content: str, answer: str) -> float:
    """Estimate confidence in the local answer."""
    lowered_task = task_content.lower()
    lowered_answer = answer.lower() if answer else ""

    if not answer or len(answer.strip()) < 5:
        return 0.0

    if "error calling local model" in lowered_answer:
        return 0.0

    confidence = 0.8

    if _is_translation_task(task_content) and len(answer.split()) > 8:
        confidence -= 0.55

    if _is_numeric_or_estimation_task(task_content) and not _contains_number(answer):
        confidence -= 0.55

    if _looks_uncertain_or_refusal(answer):
        confidence -= 0.3

    if _looks_off_topic(task_content, answer):
        confidence -= 0.35

    if len(task_content) > 100 and len(answer) < 20:
        confidence -= 0.3

    return max(0.0, min(confidence, 1.0))

def should_escalate(task: Task, local_answer: str, confidence: float, threshold: float = 0.7) -> bool:
    """Decide if the task should be escalated to remote."""
    if confidence < 0.3:
        return True

    if confidence < threshold:
        return True

    return False


def get_escalation_reason(task_content: str, local_answer: str, confidence: float, threshold: float = 0.7) -> str:
    """Return a short reason for logging and UI debugging."""
    if not local_answer or not local_answer.strip():
        return "empty_local_answer"
    if "error calling local model" in local_answer.lower():
        return "local_model_error"
    if _is_numeric_or_estimation_task(task_content) and not _contains_number(local_answer):
        return "numeric_task_without_number"
    if _is_translation_task(task_content) and len(local_answer.split()) > 8:
        return "simple_translation_answer_too_long"
    if _looks_off_topic(task_content, local_answer):
        return "possible_off_topic_answer"
    if confidence < threshold:
        return "low_local_confidence"
    return "none"


def _is_translation_task(task_content: str) -> bool:
    lowered = task_content.lower()
    return any(marker in lowered for marker in _TRANSLATION_MARKERS)


def _is_simple_translation_task(task_content: str) -> bool:
    lowered = task_content.lower()
    return _is_translation_task(task_content) and len(task_content.split()) <= 12


def _is_numeric_or_estimation_task(task_content: str) -> bool:
    lowered = task_content.lower()
    return (
        any(marker in lowered for marker in _ESTIMATION_MARKERS)
        or any(marker in lowered for marker in ["calcule", "calculate", "quanto", "what is"])
    )


def _contains_number(text: str) -> bool:
    return bool(re.search(r"\d|10\^|million|billion|milhao|milhão|bilhao|bilhão", text.lower()))


def _looks_uncertain_or_refusal(answer: str) -> bool:
    lowered = answer.lower()
    markers = [
        "i cannot",
        "não posso",
        "nao posso",
        "as an ai",
        "não tenho certeza",
        "nao tenho certeza",
        "desculpe",
    ]
    return any(marker in lowered for marker in markers)


def _looks_off_topic(task_content: str, answer: str) -> bool:
    task_words = _content_words(task_content)
    answer_words = _content_words(answer)
    if len(task_words) < 2 or len(answer_words) < 4:
        return False

    overlap = task_words.intersection(answer_words)
    return len(overlap) == 0 and len(answer.split()) > 20


def _content_words(text: str) -> set[str]:
    stopwords = {
        "a",
        "o",
        "e",
        "de",
        "da",
        "do",
        "em",
        "para",
        "por",
        "com",
        "the",
        "is",
        "to",
        "of",
        "in",
        "and",
        "what",
        "how",
        "que",
        "um",
        "uma",
        "no",
        "na",
    }
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in stopwords}
