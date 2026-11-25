"""IFEval scoring with the stdlib port (ifeval_checks.py). run in envs/score (fastText for 3 ids).

usage: ifeval_score.py <rows.jsonl> <prompts.jsonl> <out_prefix>
only `scored_instruction_ids` are checked (length_constraints:* left out, PROTOCOL.md section 3).
the response is the row's `completion`. writes <out_prefix>.rows.jsonl (per prompt: strict and loose
result per scored instruction) and <out_prefix>.json: prompt-level strict (primary) and loose over
prompts with at least one scored instruction, instruction-level strict and loose, cap-hit share,
and instruction-level accuracy per instruction id.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ifeval_checks as ic  # noqa: E402


def score_row(r, item):
    resp = r["completion"]
    res = []
    for iid, kw in zip(item["instruction_id_list"], item["kwargs"]):
        if iid not in item["scored_instruction_ids"]:
            continue
        res.append({"id": iid, "strict": int(ic.follows(iid, kw, resp)),
                    "loose": int(ic.follows(iid, kw, resp, loose=True))})
    assert [x["id"] for x in res] == item["scored_instruction_ids"], item["id"]
    return {"id": r["id"], "key": item["key"], "n_scored": len(res), "instructions": res,
            "prompt_strict": int(bool(res) and all(x["strict"] for x in res)),
            "prompt_loose": int(bool(res) and all(x["loose"] for x in res)),
            "hit_max_tokens": int(bool(r.get("hit_max_tokens")))}


def pct(k, n):
    return round(100 * k / n, 2) if n else None


def main():
    rows_path, prompts_path, prefix = sys.argv[1:4]
    items = {it["id"]: it for it in map(json.loads, open(prompts_path, encoding="utf-8"))}
    rows = [json.loads(line) for line in open(rows_path, encoding="utf-8")]
    out = [score_row(r, items[r["id"]]) for r in rows]
    with open(prefix + ".rows.jsonl", "w") as f:
        for d in out:
            f.write(json.dumps(d) + "\n")
    sc = [d for d in out if d["n_scored"]]
    inst = [x for d in sc for x in d["instructions"]]
    per = collections.defaultdict(lambda: [0, 0, 0])
    for x in inst:
        per[x["id"]][0] += 1
        per[x["id"]][1] += x["strict"]
        per[x["id"]][2] += x["loose"]
    rep = {"rows": rows_path, "n_rows": len(out), "n_prompts_scored": len(sc), "n_instructions": len(inst),
           "prompt_strict": pct(sum(d["prompt_strict"] for d in sc), len(sc)),
           "prompt_loose": pct(sum(d["prompt_loose"] for d in sc), len(sc)),
           "inst_strict": pct(sum(x["strict"] for x in inst), len(inst)),
           "inst_loose": pct(sum(x["loose"] for x in inst), len(inst)),
           "hit_max_tokens_pct": pct(sum(d["hit_max_tokens"] for d in out), len(out)),
           "by_instruction": {k: {"n": v[0], "strict": pct(v[1], v[0]), "loose": pct(v[2], v[0])}
                              for k, v in sorted(per.items())}}
    with open(prefix + ".json", "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("n_rows", "n_prompts_scored", "n_instructions", "prompt_strict",
                                          "prompt_loose", "inst_strict", "inst_loose", "hit_max_tokens_pct")}))


if __name__ == "__main__":
    main()
