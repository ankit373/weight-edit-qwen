"""row check after a (resumed) step: every line parses, no duplicate ids. stdlib only.
usage: check_rows.py <rows.jsonl>   exit 1 on a bad line or a duplicate id"""
import collections
import json
import sys

path = sys.argv[1]
ids, bad = collections.Counter(), 0
for line in open(path):
    try:
        ids[json.loads(line)["id"]] += 1
    except (ValueError, KeyError):
        bad += 1
dup = [i for i, c in ids.items() if c > 1]
print(json.dumps({"rows_file": path, "n_rows": sum(ids.values()), "n_unique": len(ids),
                  "bad_lines": bad, "duplicates": dup[:10], "n_dup": len(dup)}))
sys.exit(1 if bad or dup else 0)
