"""Summarize Fireworks token usage from logs/runs.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional


@dataclass
class Bucket:
    tasks: int = 0
    remote_input: int = 0
    remote_output: int = 0
    remote_total: int = 0
    credits: float = 0.0

    def add(self, row: Dict[str, Any]) -> None:
        usage = row.get("usage", {})
        tokens = usage.get("tokens", {})
        credits = usage.get("credits", {})

        self.tasks += 1
        self.remote_input += int(tokens.get("remote_input", 0))
        self.remote_output += int(tokens.get("remote_output", 0))
        self.remote_total += int(tokens.get("remote_total", row.get("remote_tokens", 0)))
        self.credits += float(credits.get("total_spent", 0.0))


@dataclass
class Report:
    rows: List[Dict[str, Any]] = field(default_factory=list)
    by_category: DefaultDict[str, Bucket] = field(default_factory=lambda: defaultdict(Bucket))
    by_model: DefaultDict[str, Bucket] = field(default_factory=lambda: defaultdict(Bucket))
    by_route: DefaultDict[str, Bucket] = field(default_factory=lambda: defaultdict(Bucket))
    totals: Bucket = field(default_factory=Bucket)

    @property
    def deterministic_tasks(self) -> int:
        return self.by_route.get("deterministic", Bucket()).tasks

    @property
    def remote_tasks(self) -> int:
        return sum(bucket.tasks for route, bucket in self.by_route.items() if route != "deterministic")


def load_rows(path: Path, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if last_n is not None and last_n > 0:
        rows = rows[-last_n:]
    return rows


def build_report(rows: List[Dict[str, Any]]) -> Report:
    report = Report(rows=rows)

    for row in rows:
        specialists = row.get("specialists", {})
        category = specialists.get("task_type", "unknown")
        model = row.get("remote_model") or "(none)"
        route = row.get("route", "unknown")

        report.by_category[category].add(row)
        report.by_model[model].add(row)
        report.by_route[route].add(row)
        report.totals.add(row)

    return report


def _pct(part: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(part / total) * 100:.1f}%"


def _short_model(model: str, width: int = 42) -> str:
    if len(model) <= width:
        return model
    return model[: width - 3] + "..."


def format_text(report: Report, log_path: Path) -> str:
    lines: List[str] = []
    lines.append("Token Usage Report")
    lines.append(f"Source: {log_path}")
    lines.append(f"Tasks analyzed: {report.totals.tasks}")
    lines.append("")

    lines.append("Totals (scored = Fireworks remote only)")
    lines.append(f"  Remote input tokens : {report.totals.remote_input:,}")
    lines.append(f"  Remote output tokens: {report.totals.remote_output:,}")
    lines.append(f"  Remote total tokens : {report.totals.remote_total:,}")
    lines.append(f"  Credits spent       : {report.totals.credits:.6f}")
    lines.append(f"  Deterministic tasks : {report.deterministic_tasks} (0 tokens each)")
    lines.append(f"  Remote LLM tasks    : {report.remote_tasks}")
    lines.append("")

    lines.append("By category")
    lines.append(f"  {'category':<22} {'tasks':>5} {'in':>8} {'out':>8} {'total':>8} {'share':>7}")
    for category in sorted(report.by_category, key=lambda key: report.by_category[key].remote_total, reverse=True):
        bucket = report.by_category[category]
        lines.append(
            f"  {category:<22} {bucket.tasks:>5} {bucket.remote_input:>8,} "
            f"{bucket.remote_output:>8,} {bucket.remote_total:>8,} "
            f"{_pct(bucket.remote_total, report.totals.remote_total):>7}"
        )
    lines.append("")

    lines.append("By remote model")
    lines.append(f"  {'model':<44} {'tasks':>5} {'in':>8} {'out':>8} {'total':>8} {'share':>7}")
    for model in sorted(report.by_model, key=lambda key: report.by_model[key].remote_total, reverse=True):
        bucket = report.by_model[model]
        lines.append(
            f"  {_short_model(model):<44} {bucket.tasks:>5} {bucket.remote_input:>8,} "
            f"{bucket.remote_output:>8,} {bucket.remote_total:>8,} "
            f"{_pct(bucket.remote_total, report.totals.remote_total):>7}"
        )
    lines.append("")

    lines.append("By route")
    for route in sorted(report.by_route, key=lambda key: report.by_route[key].remote_total, reverse=True):
        bucket = report.by_route[route]
        lines.append(
            f"  {route:<14} tasks={bucket.tasks:<4} remote_total={bucket.remote_total:,}"
        )
    lines.append("")

    lines.append("Per task")
    lines.append(f"  {'task_id':<16} {'route':<14} {'category':<18} {'tokens':>8}  model")
    for row in report.rows:
        specialists = row.get("specialists", {})
        category = specialists.get("task_type", "unknown")
        tokens = row.get("usage", {}).get("tokens", {}).get("remote_total", row.get("remote_tokens", 0))
        model = row.get("remote_model") or "-"
        lines.append(
            f"  {str(row.get('task_id', '')):<16} {str(row.get('route', '')):<14} "
            f"{category:<18} {int(tokens):>8,}  {_short_model(model, 36)}"
        )

    lines.append("")
    lines.append("Note: Hugging Face semantic-router embeddings are local and not included here.")
    return "\n".join(lines)


def report_to_json(report: Report, log_path: Path) -> Dict[str, Any]:
    def bucket_dict(bucket: Bucket) -> Dict[str, Any]:
        return {
            "tasks": bucket.tasks,
            "remote_input": bucket.remote_input,
            "remote_output": bucket.remote_output,
            "remote_total": bucket.remote_total,
            "credits": round(bucket.credits, 6),
        }

    return {
        "source": str(log_path),
        "totals": bucket_dict(report.totals),
        "deterministic_tasks": report.deterministic_tasks,
        "remote_tasks": report.remote_tasks,
        "by_category": {key: bucket_dict(value) for key, value in report.by_category.items()},
        "by_model": {key: bucket_dict(value) for key, value in report.by_model.items()},
        "by_route": {key: bucket_dict(value) for key, value in report.by_route.items()},
        "tasks": [
            {
                "task_id": row.get("task_id"),
                "route": row.get("route"),
                "category": row.get("specialists", {}).get("task_type"),
                "remote_model": row.get("remote_model"),
                "remote_tokens": row.get("usage", {}).get("tokens", {}).get(
                    "remote_total", row.get("remote_tokens", 0)
                ),
                "timestamp": row.get("timestamp"),
            }
            for row in report.rows
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize token usage from logs/runs.jsonl")
    parser.add_argument(
        "--log",
        default="logs/runs.jsonl",
        help="Path to the JSONL log file (default: logs/runs.jsonl)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        help="Only analyze the last N log entries",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text table",
    )
    args = parser.parse_args()

    log_path = Path(args.log)
    try:
        rows = load_rows(log_path, last_n=args.last)
        report = build_report(rows)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in log file: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print(f"No entries found in {log_path}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report_to_json(report, log_path), indent=2))
    else:
        print(format_text(report, log_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())