"""per-row LCB language labels for part C cross-lingual rows (m-ArenaHard, XL-AlpacaEval, LCB stress).
run in envs/score. labels use LCB compute_metrics.py functions (imported unchanged); score_one is the
function of runs/2026-11-20-stats-2b/scripts/per_prompt.py, copied (that file runs at import), plus
word_fail (WPR) and late_switch.

usage: per_row_lcb.py <rows.jsonl> <out.jsonl> [--check <score_prefix>]
cluster per row: LCB ids -> split v2 task group (splits/split_meta.json); other ids -> base_id.
--check: rebuild per-cell n / n_scored / lpr and compare with <score_prefix>.json (score.sh output);
exit 1 on any difference.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G1 = os.path.join(ROOT, "runs", "2026-11-05-gate1-baseline")
a = sys.argv[1:]
check = None
if "--check" in a:
    i = a.index("--check")
    check = os.path.abspath(a[i + 1])
    del a[i:i + 2]
rows_path, out_path = (os.path.abspath(x) for x in a)

meta = json.load(open(os.path.join(ROOT, "splits", "split_meta.json")))
group = {}
for src, gl in meta["groups"].items():
    for g in gl:
        for r in g:
            group[(src, r)] = f"{src}/{min(g)}"

os.chdir(os.path.join(G1, "scoring_workdir"))
sys.path.insert(0, os.path.join(ROOT, "external", "language-confusion"))
import compute_metrics as cm  # noqa: E402


def score_one(r):
    comp, lang = r["completion"], r["language"]
    norm = cm.normalize(comp)
    lines = norm.split("\n")
    lens = [len(cm.tokenize(l, lang)) for l in lines]
    kept = [l for l, n in zip(lines, lens) if n >= 5]
    labels = [cm.langid(l) for l in kept]
    bad = [x for x in labels if x != lang]
    d = {"scored": int(bool(kept)), "n_lines": len(kept), "n_bad": len(bad),
         "n_unknown": labels.count("unknown"),
         "fail": int(bool(kept) and bool(bad)), "full": int(bool(kept) and len(bad) == len(kept)),
         "empty": int(not comp.strip()), "reason": None}
    if not kept:
        if not comp.strip():
            d["reason"] = "empty"
        elif not norm.strip():
            d["reason"] = "punct_only"
        else:
            alt = comp.strip().translate(str.maketrans("", "", cm.string.punctuation))
            alt = alt.replace("—", " ").replace("،", "")
            if any(len(cm.tokenize(l, lang)) >= 5 for l in alt.split("\n")):
                d["reason"] = "q_cut"
            else:
                d["reason"] = "short_lines"
    # ours: WPR unit (compute_metrics: no line error, some token in en_words) and late switch
    toks = [cm.tokenize(l, lang) for l in kept]
    d["word_fail"] = int(bool(kept) and not bad and any(t.strip() in cm.en_words for ts in toks for t in ts))
    d["late_switch"] = int(len(labels) > 1 and labels[0] == lang and any(x != lang for x in labels[1:]))
    return d


def cluster_of(r):
    parts = r["id"].split("/")
    if r["source"] in ("m-arenahard", "xl-alpacaeval"):
        return r["source"], r["base_id"]
    src, row = parts[1], int(parts[3])
    return src, group[(src, row)]


rows = [json.loads(l) for l in open(rows_path, encoding="utf-8")]
ids = [r["id"] for r in rows]
assert len(set(ids)) == len(ids), "duplicate ids"
recs = []
for r in rows:
    src, cl = cluster_of(r)
    d = {"id": r["id"], "source": src, "language": r["language"], "cluster": cl,
         "hit_max_tokens": int(bool(r.get("hit_max_tokens"))), "n_new_tokens": r.get("n_new_tokens")}
    d.update(score_one(r))
    recs.append(d)
with open(out_path, "w") as f:
    for d in recs:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

bad = []
if check:
    cell = collections.defaultdict(lambda: [0, 0, 0])
    for d, r in zip(recs, rows):
        c = cell[(r["source"], r["language"])]
        c[0] += 1; c[1] += d["scored"]; c[2] += d["fail"]
    table = json.load(open(check + ".json"))
    for t in table:
        k = (t["source"], t["language"])
        if k in cell and "n_scored" in t:
            n, s, fl = cell[k]
            if (n, s) != (t["n"], t["n_scored"]) or abs((1 - fl / max(1, s)) - t["lpr"]) > 1e-12:
                bad.append([list(k), n, s, t["n"], t["n_scored"]])
    print(json.dumps({"checked_against": check, "n_cells": len(cell), "diffs": bad[:10]}))
print(json.dumps({"rows": rows_path, "n": len(recs), "scored": sum(d["scored"] for d in recs),
                  "fail": sum(d["fail"] for d in recs), "full": sum(d["full"] for d in recs)}))
sys.exit(1 if bad else 0)
