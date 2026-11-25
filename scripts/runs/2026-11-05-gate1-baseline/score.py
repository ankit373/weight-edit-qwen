"""score LCB completions with the benchmark's own compute_metrics.py (imported, unchanged).

usage: score.py <outputs.jsonl> <out_prefix> [--field completion|answer]
       score.py --csv <their_outputs.csv> <out_prefix>   (check the scorer on their published outputs)
"""
import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "external", "language-confusion"))
WORK = os.path.join(HERE, "scoring_workdir")  # holds `words` + `lid.176.bin`, which the module opens by relative path

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("out_prefix")
ap.add_argument("--field", default="completion")
ap.add_argument("--csv", action="store_true")
args = ap.parse_args()
inp, out_prefix = os.path.abspath(args.inp), os.path.abspath(args.out_prefix)

os.chdir(WORK)
sys.path.insert(0, REPO)
import compute_metrics as cm  # noqa: E402

NON_LATIN = ("ar", "hi", "ja", "ko", "ru", "zh")  # same list as compute_metrics.compute_metrics


def lcpr(lpr, wpr):
    # paper sec 2.2: LCPR = 2 * LPR * WPR / (LPR + WPR)
    if wpr is None:
        return None
    return 0.0 if lpr + wpr == 0 else 2 * lpr * wpr / (lpr + wpr)


def counted(completion, lang):
    """1 if the scorer keeps this response (has a line with >= 5 tokens), using their functions."""
    text = cm.normalize(completion)
    return int(any(len(cm.tokenize(l, lang)) >= 5 for l in text.split("\n")))


if args.csv:
    with open(inp) as f:
        rows = [dict(r) for r in csv.DictReader(f)]
    for r in rows:
        r["hit_max_tokens"] = None
else:
    rows = [json.loads(l) for l in open(inp)]
    for r in rows:
        r["completion"] = r[args.field]

by_task = collections.defaultdict(list)
for r in rows:
    by_task[r["task"]].append(r)

table = []
for task, rs in sorted(by_task.items()):
    allm = cm.compute_all_metrics([{"source": r["source"], "language": r["language"], "completion": r["completion"]} for r in rs])
    groups = collections.defaultdict(list)
    for r in rs:
        groups[(r["source"], r["language"])].append(r)
        groups[(r["source"], "all")].append(r)
        groups[("all", r["language"])].append(r)
        groups[("all", "all")].append(r)
    for (source, lang), m in sorted(allm.items()):
        g = groups[(source, lang)]
        row = {
            "task": task, "source": source, "language": lang, "n": len(g),
            "n_scored": sum(counted(r["completion"], r["language"]) for r in g),
            "n_empty": sum(1 for r in g if not r["completion"].strip()),
            "n_hit_max_tokens": None if g[0]["hit_max_tokens"] is None else sum(1 for r in g if r["hit_max_tokens"]),
            "lpr": m["lpr"], "wpr": m.get("wpr"), "acc": m["acc"],
            "lcpr": lcpr(m["lpr"], m.get("wpr")),
        }
        table.append(row)
        if (source, lang) == ("all", "all"):
            row["lcpr"] = None  # HM of all-language LPR and non-latin WPR is not a paper number
    # two LCPR averages, both checked against the paper on their published outputs (see README):
    # table A5 "Avg" = mean of per-language LCPR over the non-latin languages
    per_lang = [t for t in table if t["task"] == task and t["source"] == "all" and t["language"] in NON_LATIN]
    if per_lang:
        table.append({
            "task": task, "source": "all", "language": "nonlatin_mean_lcpr", "n": sum(t["n"] for t in per_lang),
            "lcpr": sum(t["lcpr"] for t in per_lang) / len(per_lang),
            "lpr": sum(t["lpr"] for t in per_lang) / len(per_lang),
            "wpr": sum(t["wpr"] for t in per_lang) / len(per_lang),
        })
    # table A9 "Avg" = mean over datasets of the dataset-level LCPR
    per_src = [t for t in table if t["task"] == task and t["source"] != "all" and t["language"] == "all"]
    table.append({
        "task": task, "source": "all", "language": "dataset_mean_lcpr", "n": sum(t["n"] for t in per_src),
        # None when some dataset has no non-latin language in the input (only happens on small subsets)
        "lcpr": None if any(t["lcpr"] is None for t in per_src) else sum(t["lcpr"] for t in per_src) / len(per_src),
    })

with open(out_prefix + ".json", "w") as f:
    json.dump(table, f, indent=1)
cols = ["task", "source", "language", "n", "n_scored", "n_empty", "n_hit_max_tokens", "lpr", "wpr", "lcpr", "acc"]
with open(out_prefix + ".tsv", "w") as f:
    f.write("\t".join(cols) + "\n")
    for t in table:
        f.write("\t".join("" if t.get(c) is None else (f"{t[c]*100:.1f}" if c in ("lpr", "wpr", "lcpr", "acc") else str(t[c])) for c in cols) + "\n")
print(open(out_prefix + ".tsv").read())
