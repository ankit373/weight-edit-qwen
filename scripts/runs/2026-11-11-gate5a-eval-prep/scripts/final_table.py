"""step 6 table rows: test complex / okapi / sharegpt / all LPR, full-failure %, loops %, from files.

usage: final_table.py <out.json> <label>=<rows.jsonl>=<score_prefix> ...
LPR and full % via gate 3 report.py (load, row): dataset/all LPR = mean over language cells,
full % = pooled share of scored responses fully in a wrong language. loops via gate 3 guard.py
stats (distinct 4-gram ratio < 0.5 on token ids). no model, tokenizer only (gen env).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G3 = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-run", "scripts"))
sys.path.insert(0, G3)
import guard  # noqa: E402
import report  # noqa: E402

tok = guard.g3common.load_tokenizer()
res = {}
for arg in sys.argv[2:]:
    label, rows_path, prefix = arg.split("=", 2)
    cells, full = report.load(prefix)
    rows = guard.load(rows_path)
    ids = sorted(rows)
    s = guard.stats(rows, {}, ids, tok)
    r = {"rows": rows_path, "score_prefix": prefix, "n_rows": len(ids),
         "loops_pct": round(s["loop_pct"], 2), "loops_n": round(s["loop_pct"] * s["n"] / 100),
         "empty_pct": round(s["empty_pct"], 2)}
    for src, name in report.SETS:
        x = report.row(cells, full, (src, "all"))
        r[name] = {"lpr": round(100 * x["lpr"], 1), "full_pct": round(x["full"], 1),
                   "scored": x["scored"], "n": x["n"],
                   "wpr": None if x["wpr"] is None else round(100 * x["wpr"], 1),
                   "lcpr": None if x["lcpr"] is None else round(100 * x["lcpr"], 1)}
    res[label] = r
    print(label, json.dumps({k: (v["lpr"], v["full_pct"]) for k, v in r.items() if isinstance(v, dict)}),
          "loops", r["loops_pct"], flush=True)
with open(sys.argv[1], "w") as f:
    json.dump(res, f, indent=1)
