import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

# Local Model (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:0.5b")

# Remote Model (Fireworks AI)
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
REMOTE_MODEL_NAME = os.getenv("REMOTE_MODEL_NAME", "accounts/fireworks/models/llama-v3p1-70b-instruct")

# Strategy Settings
ENABLE_LOCAL_COMPETITION = os.getenv("ENABLE_LOCAL_COMPETITION", "false").lower() == "true"
ROUTING_THRESHOLD = float(os.getenv("ROUTING_THRESHOLD", "0.7"))

# Logging
LOG_FILE = "logs/runs.jsonl"
