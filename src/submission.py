"""Track 1 submission entrypoint for the hackathon harness.

Contract:
  - Read  /input/tasks.json   -> [{"task_id": "...", "prompt": "..."}, ...]
  - Write /output/results.json -> [{"task_id": "...", "answer": "..."}, ...]

Pipeline per task:
  prompt -> semantic classification -> try_deterministic -> Fireworks (ALLOWED_MODELS)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

from .router import HybridRouter

logger = logging.getLogger(__name__)

DEFAULT_INPUT_PATH = "/input/tasks.json"
DEFAULT_OUTPUT_PATH = "/output/results.json"


def _parse_task(item: Dict[str, Any], index: int) -> Dict[str, str]:
    if not isinstance(item, dict):
        raise ValueError(f"Task at index {index} must be a JSON object.")

    task_id = item.get("task_id") or item.get("id")
    prompt = item.get("prompt") or item.get("task") or item.get("content")

    if task_id is None:
        task_id = f"task_{index}"
    if not prompt or not str(prompt).strip():
        raise ValueError(f"Task {task_id!r} is missing a prompt.")

    return {"task_id": str(task_id), "prompt": str(prompt).strip()}


def load_tasks(path: Path) -> List[Dict[str, str]]:
    # utf-8-sig tolerates local Windows-generated JSON with a BOM while still
    # reading normal UTF-8 harness files.
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array of tasks.")

    if not data:
        raise ValueError(f"{path} must contain at least one task.")

    return [_parse_task(item, index) for index, item in enumerate(data)]


def write_results(path: Path, results: List[Dict[str, str]]) -> None:
    """Atomically write results so the harness never reads a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = [{"task_id": row["task_id"], "answer": row["answer"]} for row in results]

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    tmp_path.replace(path)


def run_batch(tasks: List[Dict[str, str]], router: HybridRouter | None = None) -> List[Dict[str, str]]:
    agent = router or HybridRouter()
    results: List[Dict[str, str]] = []

    for task in tasks:
        task_id = task["task_id"]
        prompt = task["prompt"]
        try:
            outcome = agent.run(prompt, task_id=task_id)
            answer = str(outcome.get("answer", "")).strip()
            if not answer:
                raise ValueError("Router returned an empty answer.")
            results.append({"task_id": task_id, "answer": answer})
        except Exception as exc:
            logger.exception("Task %s failed", task_id)
            results.append(
                {
                    "task_id": task_id,
                    "answer": f"Unable to complete task: {exc}",
                }
            )

    return results


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    input_path = Path(os.environ.get("INPUT_PATH", DEFAULT_INPUT_PATH))
    output_path = Path(os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH))

    try:
        tasks = load_tasks(input_path)
        logger.info("Loaded %d task(s) from %s", len(tasks), input_path)

        results = run_batch(tasks)
        write_results(output_path, results)

        logger.info("Wrote %d result(s) to %s", len(results), output_path)
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
