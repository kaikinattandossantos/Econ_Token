"""Run a harder Fireworks batch and print a token usage report."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

DEFAULT_ALLOWED = (
    "accounts/fireworks/models/minimax-m3,"
    "accounts/fireworks/models/kimi-k2p7-code"
)


def main() -> int:
    os.environ.pop("ALLOW_DEV_MOCK", None)
    os.environ.setdefault("ALLOWED_MODELS", DEFAULT_ALLOWED)

    input_dir = ROOT / "input"
    output_dir = ROOT / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks_src = ROOT / "samples" / "tasks_hard.json"
    tasks_dst = input_dir / "tasks.json"
    shutil.copyfile(tasks_src, tasks_dst)

    os.environ["INPUT_PATH"] = str(tasks_dst)
    os.environ["OUTPUT_PATH"] = str(output_dir / "results.json")

    if not os.getenv("FIREWORKS_API_KEY", "").strip():
        print("ERROR: FIREWORKS_API_KEY missing in .env", file=sys.stderr)
        return 1

    from src.submission import main as submission_main
    from scripts.token_report import build_report, format_text, load_rows

    start_len = 0
    log_path = ROOT / "logs" / "runs.jsonl"
    if log_path.exists():
        start_len = sum(1 for _ in log_path.open("r", encoding="utf-8"))

    code = submission_main()
    if code != 0:
        return code

    rows = load_rows(log_path)
    batch_rows = rows[start_len:] if start_len else rows[-8:]
    report = build_report(batch_rows)

    print()
    print(format_text(report, log_path))
    print("Answers written:")
    results = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    for item in results:
        answer = item["answer"].replace("\n", " ")
        if len(answer) > 140:
            answer = answer[:140] + "..."
        print(f"  - {item['task_id']}: {answer}".encode("ascii", "replace").decode("ascii"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())