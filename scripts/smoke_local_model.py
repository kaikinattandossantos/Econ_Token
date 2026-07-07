import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os

from src.config import LOCAL_MODEL_NAME, LOCAL_PROVIDER
from src.local_model import generate_local


def main():
    os.environ.setdefault("ALLOW_LOCAL_DEV", "1")
    prompt = "Answer with only one word: ready"
    result = generate_local(prompt)
    print(f"provider={LOCAL_PROVIDER}")
    print(f"model={result.get('model', LOCAL_MODEL_NAME)}")
    print(f"tokens={result.get('tokens_total', 0)}")
    print(f"response={result.get('text', '')[:500]}")
    if result.get("text", "").lower().startswith("error calling local model"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
