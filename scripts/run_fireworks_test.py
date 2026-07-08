"""Run a real Fireworks submission test using .env credentials."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv(ROOT / ".env")

# Override with ALLOWED_MODELS env if needed. Gemma IDs may 404 until deployed on your account.
DEFAULT_ALLOWED = (
    "accounts/fireworks/models/minimax-m3,"
    "accounts/fireworks/models/kimi-k2p7-code"
)


def main() -> int:
    os.environ.pop("ALLOW_DEV_MOCK", None)
    os.environ.setdefault("ALLOWED_MODELS", DEFAULT_ALLOWED)
    os.environ.setdefault("INPUT_PATH", str(ROOT / "input" / "tasks.json"))
    os.environ.setdefault("OUTPUT_PATH", str(ROOT / "output" / "results.json"))

    api_key = os.getenv("FIREWORKS_API_KEY", "").strip()
    base_url = os.getenv("FIREWORKS_BASE_URL", "").strip()
    if not api_key:
        print("ERROR: FIREWORKS_API_KEY is missing. Set it in .env", file=sys.stderr)
        return 1
    if not base_url:
        print("ERROR: FIREWORKS_BASE_URL is missing. Set it in .env", file=sys.stderr)
        return 1

    print(f"FIREWORKS_BASE_URL={base_url}")
    print(f"ALLOWED_MODELS={os.environ['ALLOWED_MODELS']}")
    print(f"INPUT_PATH={os.environ['INPUT_PATH']}")
    print(f"OUTPUT_PATH={os.environ['OUTPUT_PATH']}")

    from src.submission import main as submission_main

    return submission_main()


if __name__ == "__main__":
    raise SystemExit(main())