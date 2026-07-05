import os
import requests
from typing import Dict, Any
from .config import FIREWORKS_API_KEY, REMOTE_MODEL_NAME

def generate_remote(prompt: str, model: str = REMOTE_MODEL_NAME) -> Dict[str, Any]:
    """Generate response using Fireworks AI or mock if API key is missing."""
    if not FIREWORKS_API_KEY:
        # Mock implementation for development
        return {
            "text": f"[MOCK REMOTE] This is a high-quality response to: {prompt[:50]}...",
            "tokens_estimated": len(prompt.split()) * 1.5,
            "model": "mock-remote-model",
            "cost_estimated": 0.0
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
        tokens = usage.get("total_tokens", 0)
        
        return {
            "text": text,
            "tokens_estimated": tokens,
            "model": model,
            "cost_estimated": (tokens / 1000000) * 0.5  # Rough estimation
        }
    except Exception as e:
        return {
            "text": f"Error calling remote model: {str(e)}",
            "tokens_estimated": 0,
            "model": model,
            "cost_estimated": 0.0
        }
