"""End-to-end Docker harness for AMD Track 1 submissions.

This script intentionally tests the built container as an external black box:
it builds a linux/amd64 image, generates fresh randomized tasks, runs the image
with real Fireworks environment variables, validates /input -> /output, and
prints a PASS/FAIL report.

No Fireworks calls are mocked here. The caller must provide:
  FIREWORKS_API_KEY, FIREWORKS_BASE_URL, ALLOWED_MODELS
in the host environment before running this script.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = ("FIREWORKS_API_KEY", "FIREWORKS_BASE_URL", "ALLOWED_MODELS")
OFFICIAL_CATEGORIES = (
    "factual_qa",
    "math_reasoning",
    "sentiment",
    "summarization",
    "ner",
    "code_debugging",
    "code_generation",
    "logical_reasoning",
)
ERROR_PREFIXES = ("traceback", "error:", "exception", "unable to complete task")
MAX_STARTUP_SECONDS = 60.0
MAX_RUNTIME_SECONDS = 600.0
MAX_IMAGE_BYTES = 10 * 1024**3


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class RunResult:
    name: str
    tasks: list[dict[str, Any]]
    results: list[dict[str, Any]] = field(default_factory=list)
    exit_code: int | None = None
    total_seconds: float = 0.0
    startup_seconds: float | None = None
    logs: str = ""
    output_path: Path | None = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and test the Track 1 Docker image end to end.")
    parser.add_argument("--image", default="router-agent-track1:e2e", help="Local image tag to build/run.")
    parser.add_argument("--platform", default="linux/amd64", help="Docker build platform.")
    parser.add_argument("--skip-build", action="store_true", help="Run an existing image instead of building.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep generated input/output folders.")
    parser.add_argument("--seed", type=int, default=None, help="Optional deterministic random seed.")
    args = parser.parse_args()

    rng = random.Random(args.seed or time.time_ns())
    checks: list[Check] = []

    checks.extend(check_prerequisites())
    if any(not check.ok for check in checks):
        print_report(checks)
        return 1

    if not args.skip_build:
        build_ok, build_detail = build_image(args.image, args.platform)
        checks.append(Check("build linux/amd64 image", build_ok, build_detail))
        if not build_ok:
            print_report(checks)
            return 1
    else:
        checks.append(Check("build linux/amd64 image", True, "skipped by --skip-build"))

    image_ok, image_detail = check_image_size(args.image)
    checks.append(Check("image size <= 10GB", image_ok, image_detail))
    if not image_ok:
        print_report(checks)
        return 1

    run_results: list[RunResult] = []
    temp_root = Path(tempfile.mkdtemp(prefix="track1-e2e-"))
    try:
        for idx in range(2):
            tasks = generate_task_suite(rng, suite_index=idx)
            run_result = run_container(args.image, tasks, temp_root / f"run_{idx + 1}")
            run_results.append(run_result)
            checks.extend(validate_run(run_result))

        checks.extend(validate_cross_run_variability(run_results[0], run_results[1]))
    finally:
        if args.keep_temp:
            print(f"\nKept temp directory: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)

    print_report(checks)
    print_push_hint(args.image, args.platform)
    return 0 if all(check.ok for check in checks) else 1


def check_prerequisites() -> list[Check]:
    checks: list[Check] = []
    missing_env = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    checks.append(
        Check(
            "required runtime env vars present",
            not missing_env,
            "missing: " + ", ".join(missing_env) if missing_env else "FIREWORKS_API_KEY/FIREWORKS_BASE_URL/ALLOWED_MODELS set",
        )
    )

    docker = shutil.which("docker")
    checks.append(Check("docker executable available", docker is not None, docker or "docker not found in PATH"))
    if docker:
        result = subprocess.run(["docker", "buildx", "version"], cwd=ROOT, capture_output=True, text=True)
        checks.append(Check("docker buildx available", result.returncode == 0, (result.stdout or result.stderr).strip()))
    return checks


def build_image(image: str, platform: str) -> tuple[bool, str]:
    started = time.perf_counter()
    cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        platform,
        "--load",
        "--tag",
        image,
        ".",
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    detail = f"{elapsed:.1f}s"
    if result.returncode != 0:
        detail += "\n" + tail(result.stdout + result.stderr)
    return result.returncode == 0, detail


def check_image_size(image: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{.Size}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, tail(result.stdout + result.stderr)
    size_bytes = int(result.stdout.strip())
    return size_bytes <= MAX_IMAGE_BYTES, f"{format_bytes(size_bytes)} (docker image inspect .Size)"


def run_container(image: str, tasks: list[dict[str, Any]], run_dir: Path) -> RunResult:
    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    harness_input = [{"task_id": task["task_id"], "prompt": task["prompt"]} for task in tasks]
    (input_dir / "tasks.json").write_text(json.dumps(harness_input, ensure_ascii=False, indent=2), encoding="utf-8")

    env_args = []
    for name in REQUIRED_ENV:
        env_args.extend(["-e", name])

    cmd = [
        "docker",
        "run",
        "--rm",
        *env_args,
        "-v",
        f"{input_dir.resolve()}:/input:ro",
        "-v",
        f"{output_dir.resolve()}:/output",
        image,
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    log_queue: queue.Queue[tuple[float, str]] = queue.Queue()
    reader = threading.Thread(target=read_process_output, args=(proc, log_queue), daemon=True)
    started = time.perf_counter()
    reader.start()

    logs: list[str] = []
    first_log_at: float | None = None
    timed_out = False
    while True:
        try:
            while True:
                timestamp, line = log_queue.get_nowait()
                if first_log_at is None and line.strip():
                    first_log_at = timestamp
                logs.append(line)
        except queue.Empty:
            pass

        if proc.poll() is not None:
            break
        if time.perf_counter() - started > MAX_RUNTIME_SECONDS:
            timed_out = True
            proc.kill()
            break
        time.sleep(0.05)

    reader.join(timeout=2)
    try:
        while True:
            timestamp, line = log_queue.get_nowait()
            if first_log_at is None and line.strip():
                first_log_at = timestamp
            logs.append(line)
    except queue.Empty:
        pass

    total = time.perf_counter() - started
    exit_code = proc.returncode
    if timed_out:
        exit_code = -9
        logs.append("\nHARNESS: container killed after 10 minute timeout.\n")

    output_path = output_dir / "results.json"
    results: list[dict[str, Any]] = []
    if output_path.exists():
        try:
            results = json.loads(output_path.read_text(encoding="utf-8-sig"))
        except Exception:
            results = []

    return RunResult(
        name=run_dir.name,
        tasks=tasks,
        results=results,
        exit_code=exit_code,
        total_seconds=total,
        startup_seconds=(first_log_at - started) if first_log_at else None,
        logs="".join(logs),
        output_path=output_path,
    )


def read_process_output(proc: subprocess.Popen[str], log_queue: queue.Queue[tuple[float, str]]) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        log_queue.put((time.perf_counter(), line))


def validate_run(run: RunResult) -> list[Check]:
    checks: list[Check] = []
    startup = run.startup_seconds
    checks.append(
        Check(
            f"{run.name}: startup/readiness <= 60s",
            startup is not None and startup <= MAX_STARTUP_SECONDS,
            f"{startup:.2f}s to first log/output" if startup is not None else "no container output observed",
        )
    )
    checks.append(Check(f"{run.name}: total runtime <= 10min", run.total_seconds <= MAX_RUNTIME_SECONDS, f"{run.total_seconds:.2f}s"))
    checks.append(Check(f"{run.name}: exit code 0", run.exit_code == 0, f"exit={run.exit_code}\n{tail(run.logs)}" if run.exit_code != 0 else "exit=0"))
    checks.append(Check(f"{run.name}: results.json exists", run.output_path is not None and run.output_path.exists(), str(run.output_path)))

    input_ids = [task["task_id"] for task in run.tasks]
    result_ids = [row.get("task_id") for row in run.results if isinstance(row, dict)]
    checks.append(
        Check(
            f"{run.name}: one result per input task_id",
            sorted(input_ids) == sorted(result_ids) and len(result_ids) == len(set(result_ids)),
            f"input={len(input_ids)} result={len(result_ids)} missing={sorted(set(input_ids)-set(result_ids))} extra={sorted(set(result_ids)-set(input_ids))}",
        )
    )

    bad_answers = []
    for row in run.results:
        answer = str(row.get("answer", "")).strip() if isinstance(row, dict) else ""
        lowered = answer.lower()
        if not answer or any(lowered.startswith(prefix) for prefix in ERROR_PREFIXES) or "[mock remote]" in lowered:
            bad_answers.append(row.get("task_id", "<unknown>") if isinstance(row, dict) else "<invalid-row>")
    checks.append(Check(f"{run.name}: no empty/error/mock answers", not bad_answers, "bad task_ids=" + ", ".join(bad_answers) if bad_answers else "ok"))

    checks.append(
        Check(
            f"{run.name}: 16 generated tasks",
            len(run.tasks) == 16,
            f"{len(run.tasks)} tasks across {len(set(task['category'] for task in run.tasks))} categories",
        )
    )
    return checks


def validate_cross_run_variability(first: RunResult, second: RunResult) -> list[Check]:
    checks: list[Check] = []
    first_math = get_task_answer_by_prefix(first, "math_reasoning")
    second_math = get_task_answer_by_prefix(second, "math_reasoning")
    if not first_math or not second_math:
        checks.append(Check("cross-run variability: math task present", False, "missing math task or answer"))
        return checks

    first_task, first_answer = first_math
    second_task, second_answer = second_math
    first_expected = str(first_task["expected"])
    second_expected = str(second_task["expected"])
    math_ok = first_expected != second_expected and answer_contains_number(first_answer, first_expected) and answer_contains_number(second_answer, second_expected)
    checks.append(
        Check(
            "cross-run anti-hardcoding: changed math prompt changes numeric answer",
            math_ok,
            f"run1 expected={first_expected} answer={first_answer[:120]!r}; run2 expected={second_expected} answer={second_answer[:120]!r}",
        )
    )

    changed_prompts = {task["category"]: task["prompt"] for task in first.tasks} != {
        task["category"]: task["prompt"] for task in second.tasks
    }
    checks.append(Check("cross-run generated prompts differ", changed_prompts, "randomized task suites differ" if changed_prompts else "task suites identical"))
    return checks


def get_task_answer_by_prefix(run: RunResult, category: str) -> tuple[dict[str, Any], str] | None:
    answers = {row.get("task_id"): str(row.get("answer", "")) for row in run.results if isinstance(row, dict)}
    for task in run.tasks:
        if task["category"] == category and "expected" in task:
            return task, answers.get(task["task_id"], "")
    return None


def generate_task_suite(rng: random.Random, suite_index: int) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for category in OFFICIAL_CATEGORIES:
        for variant in range(2):
            task = make_task(category, rng)
            task_id = f"{category}_{suite_index + 1}_{variant + 1}_{random_suffix(rng)}"
            tasks.append({"task_id": task_id, "prompt": task["prompt"], "category": category, **task.get("meta", {})})
    rng.shuffle(tasks)
    return tasks


def make_task(category: str, rng: random.Random) -> dict[str, Any]:
    if category == "math_reasoning":
        a = rng.randint(4, 19)
        b = rng.randint(3, 15)
        c = rng.randint(2, 9)
        expected = a * b + c
        prompt = f"Calculate exactly: ({a} * {b}) + {c}. Return only the final number."
        return {"prompt": prompt, "meta": {"expected": expected}}

    if category == "factual_qa":
        facts = [
            ("Japan", "Tokyo"),
            ("Canada", "Ottawa"),
            ("Brazil", "Brasilia"),
            ("Australia", "Canberra"),
            ("Kenya", "Nairobi"),
        ]
        country, _capital = rng.choice(facts)
        return {"prompt": f"What is the capital city of {country}? Answer with only the city name."}

    if category == "sentiment":
        positive = [
            "The deployment was smooth and the response quality improved.",
            "I loved how quickly the agent handled the request.",
            "The new routing logic feels reliable and fast.",
        ]
        negative = [
            "The result was confusing and the tool failed twice.",
            "I am disappointed with the slow and inaccurate answer.",
            "The update made the workflow worse than before.",
        ]
        sentence = rng.choice(positive + negative)
        return {"prompt": f"Classify the sentiment as positive, negative, or neutral: {sentence}"}

    if category == "summarization":
        product = rng.choice(["router", "dashboard", "notebook service", "evaluation harness"])
        metric = rng.choice(["latency", "token use", "error rate", "startup time"])
        paragraph = (
            f"The team tested the {product} after several configuration changes. "
            f"The main improvement was lower {metric}, but two edge cases still need review. "
            "The engineers decided to keep the current version for the demo and collect more logs overnight."
        )
        return {"prompt": f"Summarize this in one sentence: {paragraph}"}

    if category == "ner":
        person = rng.choice(["Maya Chen", "Rafael Costa", "Nora Patel", "Lucas Meyer"])
        org = rng.choice(["AMD", "Fireworks AI", "OpenAI", "Lablab"])
        city = rng.choice(["Austin", "Recife", "Toronto", "Berlin"])
        date = rng.choice(["July 12, 2026", "August 3, 2026", "September 18, 2026"])
        text = f"{person} from {org} will present a routing demo in {city} on {date}."
        return {"prompt": f"Extract named entities grouped by type from this text: {text}"}

    if category == "code_debugging":
        x = rng.choice(["total", "count", "score"])
        prompt = (
            "Debug this Python function and provide the corrected code only:\n"
            f"def add_bonus({x}, bonus):\n"
            f"    return {x} - bonus\n"
        )
        return {"prompt": prompt}

    if category == "code_generation":
        name = rng.choice(["clamp", "is_even", "safe_divide", "reverse_words"])
        if name == "clamp":
            prompt = "Write a Python function clamp(value, low, high) that returns value limited to the inclusive range [low, high]."
        elif name == "is_even":
            prompt = "Write a Python function is_even(n) that returns True if n is even and False otherwise."
        elif name == "safe_divide":
            prompt = "Write a Python function safe_divide(a, b) that returns None when b is zero, otherwise a / b."
        else:
            prompt = "Write a Python function reverse_words(text) that reverses the order of words in a string."
        return {"prompt": prompt}

    if category == "logical_reasoning":
        names = rng.sample(["Ava", "Ben", "Cleo", "Dina", "Eli"], 3)
        prompt = (
            f"Logic puzzle: {names[0]} is taller than {names[1]}. "
            f"{names[1]} is taller than {names[2]}. Who is the shortest? Explain briefly."
        )
        return {"prompt": prompt}

    raise ValueError(f"Unsupported category: {category}")


def answer_contains_number(answer: str, expected: str) -> bool:
    return expected in re.findall(r"-?\d+(?:\.\d+)?", answer.replace(",", ""))


def random_suffix(rng: random.Random) -> str:
    return "".join(rng.choice(string.ascii_lowercase + string.digits) for _ in range(5))


def print_report(checks: list[Check]) -> None:
    print("\n=== E2E DOCKER HARNESS REPORT ===")
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}")
        if check.detail:
            print(f"       {check.detail}")
    print("=================================\n")


def print_push_hint(image: str, platform: str) -> None:
    print("For registry submission, build/push with:")
    print(f"docker buildx build --platform {platform} --tag YOUR_REGISTRY/{image.split(':')[0]}:latest --push .")


def tail(text: str, max_chars: int = 3000) -> str:
    return text[-max_chars:] if len(text) > max_chars else text


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


if __name__ == "__main__":
    raise SystemExit(main())
