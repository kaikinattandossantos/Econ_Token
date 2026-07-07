import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model_router import select_remote_model
from src.remote_fireworks import generate_remote
from src.specialist_agents import analyze_task, build_remote_prompt


SMOKE_TASKS = {
    "sentiment": "Classify the sentiment as positive, neutral, or negative: I absolutely loved the AMD workshop.",
    "code": "Debug this Python code and return the fix: def add(a,b): return a-b",
    "math": "Solve briefly: If 3x + 5 = 20, what is x?",
    "factual": "What is the capital of France?",
}


def main():
    parser = argparse.ArgumentParser(description="Smoke test Fireworks Track 1 routing.")
    parser.add_argument("--case", choices=SMOKE_TASKS.keys(), default="sentiment")
    args = parser.parse_args()

    task = SMOKE_TASKS[args.case]
    profile = analyze_task(task)
    decision = select_remote_model(profile)
    prompt = build_remote_prompt(task, profile)

    print(f"case={args.case}")
    print(f"task_type={profile.task_type}")
    print(f"domain={profile.domain}")
    print(f"model={decision.model}")
    print(f"reason={decision.reason}")

    result = generate_remote(
        prompt,
        model=decision.model,
        max_tokens=decision.max_tokens,
        temperature=decision.temperature,
    )
    print(f"tokens={result.get('tokens_total', 0)}")
    print(f"response={result.get('text', '')[:500]}")

    if result.get("text", "").lower().startswith("error calling remote model"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
