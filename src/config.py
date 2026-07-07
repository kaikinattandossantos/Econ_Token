"""Non-production defaults for local development only.

Track 1 submission credentials (FIREWORKS_API_KEY, FIREWORKS_BASE_URL,
ALLOWED_MODELS) must be injected by the harness at runtime. Production inference
reads them directly from os.environ inside fireworks_client.py and allowed_models.py.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

# dotenv is for local dev convenience only — not used on the scored submission path.
load_dotenv()

# --- DEV-ONLY local model settings (Rule 4) ---
LOCAL_PROVIDER = os.getenv("LOCAL_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:0.5b")
LOCAL_OPENAI_BASE_URL = os.getenv("LOCAL_OPENAI_BASE_URL", "http://127.0.0.1:8001/v1/chat/completions")
LOCAL_OPENAI_API_KEY = os.getenv("LOCAL_OPENAI_API_KEY", "local-not-needed")
LOCAL_MAX_TOKENS = int(os.getenv("LOCAL_MAX_TOKENS", "512"))
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", "0.0"))

# Semantic router (local embeddings — not scored LLM inference)
ENABLE_SEMANTIC_ROUTER = os.getenv("ENABLE_SEMANTIC_ROUTER", "true").lower() == "true"
SEMANTIC_ROUTER_MODEL = os.getenv(
    "SEMANTIC_ROUTER_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
SEMANTIC_ROUTER_FALLBACK_MODEL = os.getenv(
    "SEMANTIC_ROUTER_FALLBACK_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
SEMANTIC_ROUTER_THRESHOLD = float(os.getenv("SEMANTIC_ROUTER_THRESHOLD", "0.42"))

# Logging
LOG_FILE = "logs/runs.jsonl"