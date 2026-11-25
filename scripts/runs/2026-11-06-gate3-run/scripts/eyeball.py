"""print 20 random answers of one setting for the by-eye guard check (random.Random(20)).
usage: eyeball.py <rows.jsonl> <ids.txt> [n=20] [chars=300]
"""
import json
import random
import sys

rows = {r["id"]: r for r in map(json.loads, open(sys.argv[1]))}
ids = [x.strip() for x in open(sys.argv[2]) if x.strip()]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
chars = int(sys.argv[4]) if len(sys.argv) > 4 else 300
for i, pid in enumerate(random.Random(20).sample(ids, n)):
    c = rows[pid]["completion"]
    print(f"[{i}] {pid} ({rows[pid]['n_new_tokens']} tok): {c[:chars]!r}")
