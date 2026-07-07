import json
from pathlib import Path

import pytest

from src.submission import load_tasks, run_batch, write_results


@pytest.fixture(autouse=True)
def dev_env(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_MOCK", "1")
    monkeypatch.setenv("ALLOWED_MODELS", "mock-remote-model")


def test_load_tasks_accepts_prompt_and_legacy_fields(tmp_path: Path):
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(
        json.dumps(
            [
                {"task_id": "t1", "prompt": "What is 2+2?"},
                {"id": "t2", "task": "Classify the sentiment: great"},
            ]
        ),
        encoding="utf-8",
    )

    tasks = load_tasks(tasks_file)
    assert tasks[0] == {"task_id": "t1", "prompt": "What is 2+2?"}
    assert tasks[1] == {"task_id": "t2", "prompt": "Classify the sentiment: great"}


def test_run_batch_writes_answers(tmp_path: Path):
    results = run_batch(
        [
            {"task_id": "count1", "prompt": "count from 0 to 3"},
            {"task_id": "remote1", "prompt": "What is the capital of Spain?"},
        ]
    )

    assert results[0]["task_id"] == "count1"
    assert results[0]["answer"] == "0, 1, 2, 3"
    assert results[1]["task_id"] == "remote1"
    assert "[MOCK REMOTE]" in results[1]["answer"]


def test_write_results_atomic_contract(tmp_path: Path):
    output_path = tmp_path / "results.json"
    write_results(
        output_path,
        [
            {"task_id": "a", "answer": "one"},
            {"task_id": "b", "answer": "two"},
        ],
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data == [
        {"task_id": "a", "answer": "one"},
        {"task_id": "b", "answer": "two"},
    ]