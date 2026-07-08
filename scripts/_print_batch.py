import json
from pathlib import Path

IDS = {
    "fact1", "fact2", "fact3", "fact4",
    "sent1", "sent2", "sent3", "sent4",
    "sum1", "sum2", "sum3", "sum4",
    "ner1", "ner2", "ner3", "ner4",
    "dbg1", "dbg2", "dbg3", "dbg4",
    "code1", "code2", "code3", "code4",
    "logic1", "logic2", "logic3", "logic4",
}

rows = [
    json.loads(line)
    for line in Path("logs/runs.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
batch = [r for r in rows if r["task_id"] in IDS]
# keep latest run per task_id
seen = {}
for r in batch:
    seen[r["task_id"]] = r
batch = [seen[k] for k in sorted(seen)]

print(f"tasks: {len(batch)}")
print(f"{'id':<8} {'route':<12} {'type':<18} {'semantic':<16} {'tok':>5}  status")
print("-" * 90)
for r in batch:
    sem = r["specialists"].get("semantic", {}).get("label", "-")
    tok = r.get("remote_tokens", 0)
    ans = r["answer"]
    status = "FAIL" if ans.startswith("Unable to complete") else "OK"
    print(f"{r['task_id']:<8} {r['route']:<12} {r['specialists']['task_type']:<18} {sem:<16} {tok:>5}  {status}")