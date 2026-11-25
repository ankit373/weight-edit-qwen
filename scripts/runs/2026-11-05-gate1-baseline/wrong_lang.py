"""for responses that fail LPR: which language did fastText give the bad lines. uses compute_metrics' own functions."""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
inp, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
field = sys.argv[3] if len(sys.argv) > 3 else "completion"
os.chdir(os.path.join(HERE, "scoring_workdir"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "external", "language-confusion"))
import compute_metrics as cm  # noqa: E402

res = collections.defaultdict(collections.Counter)
examples = []
for l in open(inp):
    r = json.loads(l)
    lang = r["language"]
    lines = cm.normalize(r[field]).split("\n")
    lines = [x for x in lines if len(cm.tokenize(x, lang)) >= 5]
    bad = [cm.langid(x) for x in lines if cm.langid(x) != lang]
    if not lines:
        continue
    if bad:
        full = len(bad) == len(lines)
        res[(r["task"], lang)]["full" if full else "partial"] += 1
        for b in bad:
            res[(r["task"], lang)]["line:" + b] += 1
        examples.append({"id": r["id"], "full_response_wrong": full, "bad_labels": bad})
summary = {f"{t}/{l}": dict(c.most_common()) for (t, l), c in sorted(res.items())}
tot = collections.defaultdict(collections.Counter)
for (t, l), c in res.items():
    for k, v in c.items():
        if k.startswith("line:") or k in ("full", "partial"):
            tot[t][k] += v
summary["_totals"] = {t: dict(c.most_common(8)) for t, c in tot.items()}
json.dump({"summary": summary, "failing_responses": examples}, open(out, "w"), indent=1)
print(json.dumps(summary["_totals"], indent=1))
