import json
from pathlib import Path

from scripts.token_report import build_report, load_rows


def test_build_report_aggregates_by_category_and_model(tmp_path: Path):
    log_file = tmp_path / "runs.jsonl"
    rows = [
        {
            "task_id": "t1",
            "route": "deterministic",
            "remote_model": "",
            "remote_tokens": 0,
            "specialists": {"task_type": "math_reasoning"},
            "usage": {"tokens": {"remote_input": 0, "remote_output": 0, "remote_total": 0}, "credits": {"total_spent": 0.0}},
        },
        {
            "task_id": "t2",
            "route": "remote",
            "remote_model": "mock-remote-model",
            "remote_tokens": 120,
            "specialists": {"task_type": "sentiment"},
            "usage": {"tokens": {"remote_input": 50, "remote_output": 70, "remote_total": 120}, "credits": {"total_spent": 0.00006}},
        },
    ]
    log_file.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    loaded = load_rows(log_file)
    report = build_report(loaded)

    assert report.totals.tasks == 2
    assert report.totals.remote_total == 120
    assert report.by_category["math_reasoning"].tasks == 1
    assert report.by_category["math_reasoning"].remote_total == 0
    assert report.by_category["sentiment"].remote_total == 120
    assert report.by_model["mock-remote-model"].remote_total == 120
    assert report.deterministic_tasks == 1
    assert report.remote_tasks == 1


def test_load_rows_last_n(tmp_path: Path):
    log_file = tmp_path / "runs.jsonl"
    log_file.write_text(
        "\n".join(json.dumps({"task_id": f"t{i}"}) for i in range(5)) + "\n",
        encoding="utf-8",
    )

    rows = load_rows(log_file, last_n=2)
    assert len(rows) == 2
    assert rows[0]["task_id"] == "t3"
    assert rows[1]["task_id"] == "t4"