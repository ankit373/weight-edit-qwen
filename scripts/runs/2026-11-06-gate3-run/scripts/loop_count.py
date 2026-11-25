"""empty / looping counts (guard units, guard.py) for rows of an id file. no model.
usage: loop_count.py <rows.jsonl> <ids.txt>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard
rows = guard.load(sys.argv[1]); ids = [x.strip() for x in open(sys.argv[2]) if x.strip()]
ids = [i for i in ids if i in rows]
s = guard.stats(rows, {}, ids, guard.g3common.load_tokenizer())
print(json.dumps({"n": s["n"], "empty": round(s["empty_pct"] * s["n"] / 100), "loop": round(s["loop_pct"] * s["n"] / 100),
                  "empty_pct": s["empty_pct"], "loop_pct": s["loop_pct"]}))
