import argparse
import json
import sys
from .router import HybridRouter

def main():
    parser = argparse.ArgumentParser(description="Hybrid Token-Efficient Routing Agent")
    parser.add_argument("--task", type=str, help="Task description")
    parser.add_argument("--file", type=str, help="JSONL file with tasks")
    
    args = parser.parse_args()
    
    router = HybridRouter()
    
    if args.task:
        result = router.run(args.task)
        print_result(result)
    elif args.file:
        try:
            with open(args.file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    task_data = json.loads(line)
                    task_content = task_data.get("task", task_data.get("content", ""))
                    task_id = task_data.get("id", "batch")
                    result = router.run(task_content, task_id)
                    print_result(result)
                    print("-" * 40)
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        parser.print_help()

def print_result(res):
    usage = res.get("usage", {})
    tokens = usage.get("tokens", {})
    credits = usage.get("credits", {})
    print(f"\n[ROUTE]: {res['route'].upper()}")
    print(f"[CONFIDENCE]: {res['local_confidence']:.2f}")
    print(f"[TOTAL TOKENS]: {tokens.get('total', res.get('remote_tokens', 0))}")
    print(f"[LOCAL TOKENS]: {tokens.get('local_total', 0)}")
    print(f"[REMOTE TOKENS]: {tokens.get('remote_total', res.get('remote_tokens', 0))}")
    print(f"[CREDITS SPENT]: {credits.get('total_spent', 0.0)}")
    print(f"[ANSWER]:\n{res['answer']}\n")

if __name__ == "__main__":
    main()
