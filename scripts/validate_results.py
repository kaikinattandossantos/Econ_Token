"""Validate Track 1 output contract for local/docker smoke tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(tasks_path: Path, results_path: Path) -> List[str]:
    errors: List[str] = []

    tasks = _load_json(tasks_path)
    results = _load_json(results_path)

    if not isinstance(tasks, list):
        errors.append("tasks.json must be a JSON array.")
        return errors
    if not isinstance(results, list):
        errors.append("results.json must be a JSON array.")
        return errors

    expected_ids: Set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{index}] must be an object.")
            continue
        task_id = task.get("task_id") or task.get("id")
        if not task_id:
            errors.append(f"tasks[{index}] is missing task_id.")
            continue
        expected_ids.add(str(task_id))

    seen_ids: Set[str] = set()
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            errors.append(f"results[{index}] must be an object.")
            continue
        if "task_id" not in result or "answer" not in result:
            errors.append(f"results[{index}] must contain task_id and answer.")
            continue
        task_id = str(result["task_id"])
        answer = result.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            errors.append(f"results[{index}] has an empty answer.")
        if task_id in seen_ids:
            errors.append(f"Duplicate task_id in results: {task_id}")
        seen_ids.add(task_id)

    missing = expected_ids - seen_ids
    extra = seen_ids - expected_ids
    if missing:
        errors.append(f"Missing task_id values in results: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected task_id values in results: {sorted(extra)}")

    return errors


def main() -> int:
    tasks_path = Path(sys.argv[1] if len(sys.argv) > 1 else "input/tasks.json")
    results_path = Path(sys.argv[2] if len(sys.argv) > 2 else "output/results.json")

    if not tasks_path.exists():
        print(f"Missing tasks file: {tasks_path}", file=sys.stderr)
        return 1
    if not results_path.exists():
        print(f"Missing results file: {results_path}", file=sys.stderr)
        return 1

    errors = validate(tasks_path, results_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {results_path} matches {tasks_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())