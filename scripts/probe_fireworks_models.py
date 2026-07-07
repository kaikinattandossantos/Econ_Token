from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

key = os.environ.get("FIREWORKS_API_KEY", "").strip()
url = os.environ.get("FIREWORKS_BASE_URL", "").strip()
if not key or not url:
    print("Missing FIREWORKS_API_KEY or FIREWORKS_BASE_URL", file=sys.stderr)
    raise SystemExit(1)

models = [
    "accounts/fireworks/models/minimax-m3",
    "accounts/fireworks/models/gemma-4-26b-a4b-it",
    "accounts/fireworks/models/gemma-4-31b-it",
    "accounts/fireworks/models/kimi-k2p7-code",
]

for model in models:
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "What is the capital of France? One word."}],
            "max_tokens": 20,
        },
        timeout=30,
    )
    text = response.text.replace("\n", " ")[:180]
    print(f"{model} -> {response.status_code} {text}")