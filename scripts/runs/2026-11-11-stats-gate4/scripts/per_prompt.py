"""per-prompt LCB scores with the benchmark's own functions, then rebuild the score files from them.

usage: per_prompt.py <out_dir>
writes <out_dir>/<label>.jsonl and <out_dir>/check.json. exits 1 if any score-file cell differs.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G1 = os.path.join(ROOT, "runs", "2026-11-05-gate1-baseline")
G3 = "runs/2026-11-06-gate3-run"
G4 = "runs/2026-11-10-gate4-eval"
METHODS = {  # label: (rows, score prefix)
    "baseline_s1": (f"{G3}/outputs/baseline_test.jsonl", f"{G3}/scores/baseline_test"),
    "instr_end_s1": (f"{G3}/outputs/instr_end_test.jsonl", f"{G3}/scores/instr_end_test"),
    "recover_s1": (f"{G3}/outputs/recover_a0.03_on_test.jsonl", f"{G3}/scores/recover_a0.03_on_test"),
    "c02_s1": (f"{G4}/outputs/final_test.jsonl", f"{G4}/scores/final_test"),
    "rand1001_s1": (f"{G4}/outputs/rand_s1001_test.jsonl", f"{G4}/scores/rand_s1001_test"),
    "rand1002_s1": (f"{G4}/outputs/rand_s1002_test.jsonl", f"{G4}/scores/rand_s1002_test"),
    "rand1003_s1": (f"{G4}/outputs/rand_s1003_test.jsonl", f"{G4}/scores/rand_s1003_test"),
    "baseline_s2": (f"{G4}/outputs/base_test_s2.jsonl", f"{G4}/scores/base_test_s2"),
    "instr_end_s2": (f"{G4}/outputs/instr_end_test_s2.jsonl", f"{G4}/scores/instr_end_test_s2"),
    "recover_s2": (f"{G4}/outputs/recover_a0.03_on_test_s2.jsonl", f"{G4}/scores/recover_a0.03_on_test_s2"),
    "c02_s2": (f"{G4}/outputs/final_test_s2.jsonl", f"{G4}/scores/final_test_s2"),
}

out_dir = os.path.abspath(sys.argv[1])
os.makedirs(out_dir, exist_ok=True)
meta = json.load(open(os.path.join(ROOT, "splits", "split_meta.json")))
test_ids = [l.strip() for l in open(os.path.join(ROOT, "splits", "test.txt")) if l.strip()]
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
            # normalize without the "\nQ:" cut: would a long line exist?
            alt = comp.strip().translate(str.maketrans("", "", cm.string.punctuation))
            alt = alt.replace("—", " ").replace("،", "")
            if any(len(cm.tokenize(l, lang)) >= 5 for l in alt.split("\n")):
                d["reason"] = "q_cut"
            else:
                d["reason"] = "short_lines"
        nonempty = [n for l, n in zip(lines, lens) if l.strip()]
        d["max_line_tokens"] = max(nonempty) if nonempty else 0
        d["n_nonempty_lines"] = len(nonempty)
    return d


def rebuild(rows):
    """score.py cells from per-prompt rows, same averaging as compute_metrics."""
    cell = collections.defaultdict(lambda: [0, 0, 0, 0])  # n, scored, fails, empty
    for r in rows:
        c = cell[(r["source"], r["language"])]
        c[0] += 1; c[1] += r["scored"]; c[2] += r["fail"]; c[3] += r["empty"]
    lpr = {k: 1 - v[2] / max(1, v[1]) for k, v in cell.items()}
    out = {k: {"n": v[0], "n_scored": v[1], "n_empty": v[3], "lpr": lpr[k]} for k, v in cell.items()}
    srcs = sorted({k[0] for k in cell}); langs = sorted({k[1] for k in cell})
    per_lang = {}
    for s in srcs:
        ks = [k for k in cell if k[0] == s]
        out[(s, "all")] = {"n": sum(cell[k][0] for k in ks), "n_scored": sum(cell[k][1] for k in ks),
                           "n_empty": sum(cell[k][3] for k in ks), "lpr": sum(lpr[k] for k in ks) / len(ks)}
    for l in langs:
        ks = [k for k in cell if k[1] == l]
        per_lang[l] = sum(lpr[k] for k in ks) / len(ks)
        out[("all", l)] = {"n": sum(cell[k][0] for k in ks), "n_scored": sum(cell[k][1] for k in ks),
                           "n_empty": sum(cell[k][3] for k in ks), "lpr": per_lang[l]}
    out[("all", "all")] = {"n": len(rows), "n_scored": sum(r["scored"] for r in rows),
                           "n_empty": sum(r["empty"] for r in rows),
                           "lpr": sum(per_lang.values()) / len(per_lang)}
    return out


check = {}
bad_any = False
for label, (rows_path, prefix) in METHODS.items():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, rows_path))]
    ids = [r["id"] for r in rows]
    assert sorted(ids) == sorted(test_ids) and len(set(ids)) == len(ids), label
    recs = []
    for r in rows:
        _, src, lang, row = r["id"].split("/")
        d = {"id": r["id"], "source": src, "language": lang, "row": int(row),
             "group": group[(src, int(row))], "hit_max_tokens": r.get("hit_max_tokens")}
        d.update(score_one(r))
        recs.append(d)
    with open(os.path.join(out_dir, label + ".jsonl"), "w") as f:
        for d in recs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    mine = rebuild(recs)
    table = json.load(open(os.path.join(ROOT, prefix + ".json")))
    theirs = {(t["source"], t["language"]): t for t in table
              if t.get("task") == "crosslingual" and "n_scored" in t}
    diffs = []
    for k, t in theirs.items():
        m = mine.get(k)
        if m is None:
            diffs.append([list(k), "missing"]); continue
        for f in ("n", "n_scored", "n_empty"):
            if m[f] != t[f]:
                diffs.append([list(k), f, m[f], t[f]])
        if abs(m["lpr"] - t["lpr"]) > 1e-12:
            diffs.append([list(k), "lpr", m["lpr"], t["lpr"]])
    if set(mine) != set(theirs):
        diffs.append(["key sets differ", sorted(map(list, set(mine) ^ set(theirs)))])
    # full-failure ids vs wrong_lang.py
    wl = json.load(open(os.path.join(ROOT, prefix + "_wrong_lang.json")))
    wl_fail = {f["id"]: f["full_response_wrong"] for f in wl["failing_responses"]}
    my_fail = {d["id"]: bool(d["full"]) for d in recs if d["fail"]}
    if wl_fail != my_fail:
        diffs.append(["wrong_lang failing ids differ", len(wl_fail), len(my_fail)])
    check[label] = {"rows": rows_path, "score_prefix": prefix, "n_cells_checked": len(theirs),
                    "n_fail_ids": len(my_fail), "n_full": sum(my_fail.values()), "diffs": diffs[:30],
                    "complex_lpr": mine[("complex_prompts", "all")]["lpr"],
                    "all_lpr": mine[("all", "all")]["lpr"],
                    "complex_scored": mine[("complex_prompts", "all")]["n_scored"],
                    "all_scored": mine[("all", "all")]["n_scored"]}
    bad_any |= bool(diffs)
    print(label, "cells", len(theirs), "diffs", len(diffs), flush=True)

json.dump(check, open(os.path.join(out_dir, "check.json"), "w"), indent=1)
sys.exit(1 if bad_any else 0)
