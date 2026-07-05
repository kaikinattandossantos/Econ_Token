import os
from typing import Dict, Any
from .config import FIREWORKS_API_KEY, REMOTE_MODEL_NAME

def generate_remote(prompt: str, model: str = REMOTE_MODEL_NAME) -> Dict[str, Any]:
    """Generate response using Fireworks AI or mock if API key is missing."""
    if not FIREWORKS_API_KEY:
        prompt_tokens = int(len(prompt.split()) * 1.3)
        completion_tokens = 80
        total_tokens = prompt_tokens + completion_tokens
        return {
            "text": f"[MOCK REMOTE] This is a high-quality response to: {prompt[:50]}...",
            "tokens_input": prompt_tokens,
            "tokens_output": completion_tokens,
            "tokens_total": total_tokens,
            "tokens_estimated": total_tokens,
            "model": "mock-remote-model",
            "cost_credits": round((total_tokens / 1_000_000) * 0.5, 6),
            "cost_estimated": round((total_tokens / 1_000_000) * 0.5, 6),
        }

    try:
        import requests
    except ImportError as e:
        return {
            "text": f"Error calling remote model: requests is not installed: {str(e)}",
            "tokens_input": 0,
            "tokens_output": 0,
            "tokens_total": 0,
            "tokens_estimated": 0,
            "model": model,
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        cost = (tokens / 1_000_000) * 0.5

        return {
            "text": text,
            "tokens_input": prompt_tokens,
            "tokens_output": completion_tokens,
            "tokens_total": tokens,
            "tokens_estimated": tokens,
            "model": model,
            "cost_credits": round(cost, 6),
            "cost_estimated": round(cost, 6),
        }
    except Exception as e:
        return {
            "text": f"Error calling remote model: {str(e)}",
            "tokens_input": 0,
            "tokens_output": 0,
            "tokens_total": 0,
            "tokens_estimated": 0,
            "model": model,
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }
