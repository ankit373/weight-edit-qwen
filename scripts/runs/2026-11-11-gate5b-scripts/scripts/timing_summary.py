"""B1 timing: 2B time per prompt on the gate 1 timing ids vs the 0.8b gate 1 rows for the same ids.

usage: timing_summary.py <2b timing rows.jsonl> <gate1 full_nonthinking.jsonl> <out.json>
speed factor = sum of 2B time_s / sum of 0.8b time_s over the same ids (per prompt and per new token).
the 0.8b times come from the full gate 1 run, not from gate 1's own timing log. stdlib only.
"""
import json
import statistics
import sys

a = {r["id"]: r for r in map(json.loads, open(sys.argv[1]))}
ids = list(a)
b = {}
for line in open(sys.argv[2]):
    r = json.loads(line)
    if r["id"] in a:
        b[r["id"]] = r
t2, t8 = [a[i]["time_s"] for i in ids], [b[i]["time_s"] for i in ids]
n2, n8 = [a[i]["n_new_tokens"] for i in ids], [b[i]["n_new_tokens"] for i in ids]
res = {"n": len(ids), "missing_in_gate1": [i for i in ids if i not in b],
       "s_per_prompt_2b": {"mean": statistics.mean(t2), "median": statistics.median(t2), "max": max(t2)},
       "s_per_prompt_08b": {"mean": statistics.mean(t8), "median": statistics.median(t8), "max": max(t8)},
       "ms_per_new_token_2b": 1000 * sum(t2) / sum(n2), "ms_per_new_token_08b": 1000 * sum(t8) / sum(n8),
       "factor_per_prompt": sum(t2) / sum(t8),
       "factor_per_token": (sum(t2) / sum(n2)) / (sum(t8) / sum(n8)),
       "factor_excluding_first_prompt": sum(t2[1:]) / sum(t8[1:]),
       "rows": [{"id": i, "t_2b": a[i]["time_s"], "t_08b": b[i]["time_s"], "tok_2b": a[i]["n_new_tokens"],
                 "tok_08b": b[i]["n_new_tokens"]} for i in ids]}
json.dump(res, open(sys.argv[3], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
