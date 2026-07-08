"""Run an arbitrary task batch and print route/token summary."""

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


def main() -> int:
    tasks_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "samples" / "tasks_math_validation.json"

    os.environ.pop("ALLOW_DEV_MOCK", None)
    os.environ.setdefault(
        "ALLOWED_MODELS",
        "accounts/fireworks/models/minimax-m3,accounts/fireworks/models/kimi-k2p7-code",
    )

    input_dir = ROOT / "input"
    output_dir = ROOT / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(tasks_file, input_dir / "tasks.json")
    os.environ["INPUT_PATH"] = str(input_dir / "tasks.json")
    os.environ["OUTPUT_PATH"] = str(output_dir / "results.json")

    log_path = ROOT / "logs" / "runs.jsonl"
    start_len = sum(1 for _ in log_path.open("r", encoding="utf-8")) if log_path.exists() else 0

    from src.submission import main as submission_main
    from scripts.token_report import build_report, load_rows

    code = submission_main()
    if code != 0:
        return code

    rows = load_rows(log_path)
    batch_rows = rows[start_len:]
    report = build_report(batch_rows)
    results = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))

    print()
    print(f"Batch: {tasks_file.name}")
    print(f"{'task_id':<8} {'route':<14} {'tokens':>7}  answer")
    print("-" * 72)
    for row, item in zip(batch_rows, results):
        tokens = row.get("usage", {}).get("tokens", {}).get("remote_total", 0)
        answer = item["answer"].replace("\n", " ")
        if len(answer) > 48:
            answer = answer[:48] + "..."
        print(f"{item['task_id']:<8} {row.get('route',''):<14} {tokens:>7}  {answer}")

    print()
    print(f"Deterministic: {report.deterministic_tasks} | Remote: {report.remote_tasks} | Total tokens: {report.totals.remote_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())