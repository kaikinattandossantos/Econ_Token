import requests
import json
from .config import OLLAMA_BASE_URL, LOCAL_MODEL_NAME

def generate_local(prompt: str, model: str = LOCAL_MODEL_NAME) -> str:
    """Generate response using local Ollama instance."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_BASE_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error calling local model: {str(e)}"
