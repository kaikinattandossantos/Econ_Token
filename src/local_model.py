from typing import Dict, Any
from .config import OLLAMA_BASE_URL, LOCAL_MODEL_NAME


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.3))


def generate_local(prompt: str, model: str = LOCAL_MODEL_NAME) -> Dict[str, Any]:
    """Generate response using local Ollama instance."""
    try:
        import requests
    except ImportError as e:
        return _error_response(prompt, model, f"requests is not installed: {str(e)}")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_BASE_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "")
        prompt_tokens = data.get("prompt_eval_count") or _estimate_tokens(prompt)
        completion_tokens = data.get("eval_count") or _estimate_tokens(text)
        return {
            "text": text,
            "tokens_input": prompt_tokens,
            "tokens_output": completion_tokens,
            "tokens_total": prompt_tokens + completion_tokens,
            "model": model,
            "cost_credits": 0.0,
        }
    except Exception as e:
        return _error_response(prompt, model, str(e))


def _error_response(prompt: str, model: str, error: str) -> Dict[str, Any]:
    prompt_tokens = _estimate_tokens(prompt)
    return {
        "text": f"Error calling local model: {error}",
        "tokens_input": prompt_tokens,
        "tokens_output": 0,
        "tokens_total": prompt_tokens,
        "model": model,
        "cost_credits": 0.0,
    }
