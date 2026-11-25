"""compare two jsonl output files on shared ids: output_raw byte-equal or not.
usage: compare_outputs.py <a.jsonl> <b.jsonl> <out.json> [--ids IDS]
"""
import json
import sys

a_path, b_path, out = sys.argv[1:4]
ids = None
if len(sys.argv) > 5 and sys.argv[4] == "--ids":
    ids = [x.strip() for x in open(sys.argv[5]) if x.strip()]


def load(p):
    return {r["id"]: r for r in map(json.loads, open(p))}


a, b = load(a_path), load(b_path)
ids = ids or [i for i in a if i in b]
res = {"n": len(ids), "missing_in_a": [i for i in ids if i not in a],
       "missing_in_b": [i for i in ids if i not in b], "diff": []}
same = 0
for i in ids:
    if i in a and i in b:
        if a[i]["output_raw"] == b[i]["output_raw"] and a[i].get("chat_text") == b[i].get("chat_text"):
            same += 1
        else:
            res["diff"].append({"id": i, "a": a[i]["output_raw"][:200], "b": b[i]["output_raw"][:200],
                                "chat_text_equal": a[i].get("chat_text") == b[i].get("chat_text")})
res["identical"] = same
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "diff"}), "n_diff", len(res["diff"]))
