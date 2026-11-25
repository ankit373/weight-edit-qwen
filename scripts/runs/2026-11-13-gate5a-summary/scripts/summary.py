"""part A summary: 4 blind editors vs baseline, ReCoVeR 0.03, instr_end and own random controls (test, seed 1).

usage: summary.py <out_dir>
reads per-prompt rows only (no scoring): runs/2026-11-11-stats-gate4/out/per_prompt and
runs/2026-11-12-gate5a-checks/out (+ out/ed3). bootstrap = runs/2026-11-11-stats-gate4/scripts/stats.py
settings: split v2 group clusters within dataset, 10000 draws, default_rng(20261111).
exits 1 if a point metric differs from the score tables.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PP4 = "runs/2026-11-11-stats-gate4/out/per_prompt"
CHK = "runs/2026-11-12-gate5a-checks/out"
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SRCS = ["complex_prompts", "okapi", "sharegpt"]
B, SEED = 10000, 20261111
FILLS = ("drop", "fail")
METRICS = ("complex_lpr", "all_lpr", "full_all", "full_complex")

# label: (per-prompt rows, score table json, table key)
G4T = "runs/2026-11-10-gate4-eval/scores"
SRC = {
    "baseline": (f"{PP4}/baseline_s1.jsonl", f"{G4T}/table_cited.json", "baseline"),
    "recover": (f"{PP4}/recover_s1.jsonl", f"{G4T}/table_cited.json", "recover_a0.03_on"),
    "instr_end": (f"{PP4}/instr_end_s1.jsonl", f"{G4T}/table_cited.json", "instr_end"),
    "ed0": (f"{PP4}/c02_s1.jsonl", f"{G4T}/table_eval.json", "final_test"),
    "ed0_rand1001": (f"{PP4}/rand1001_s1.jsonl", f"{G4T}/table_eval.json", "rand_s1001_test"),
    "ed0_rand1002": (f"{PP4}/rand1002_s1.jsonl", f"{G4T}/table_eval.json", "rand_s1002_test"),
    "ed0_rand1003": (f"{PP4}/rand1003_s1.jsonl", f"{G4T}/table_eval.json", "rand_s1003_test"),
    "ed1": (f"{CHK}/ed1.jsonl", "runs/2026-11-11-gate5a-eval-ws1/scores/table_eval.json", "final"),
    "ed1_rand1001": (f"{CHK}/ed1_rand1001.jsonl", "runs/2026-11-11-gate5a-eval-ws1/scores/table_eval.json", "rand_s1001"),
    "ed2": (f"{CHK}/ed2.jsonl", "runs/2026-11-12-gate5a-eval-ws2/scores/table_eval.json", "final"),
    "ed2_rand1002": (f"{CHK}/ed2_rand1002.jsonl", "runs/2026-11-12-gate5a-eval-ws2/scores/table_eval.json", "rand_s1002"),
    "ed3": (f"{CHK}/ed3/ed3.jsonl", "runs/2026-11-13-gate5a-eval-ws3/scores/table_eval.json", "final"),
    "ed3_rand1003": (f"{CHK}/ed3/ed3_rand1003.jsonl", "runs/2026-11-13-gate5a-eval-ws3/scores/table_eval.json", "rand_s1003"),
    # editor 0 seed 2 (the only editor with a second sampling seed)
    "baseline_s2": (f"{PP4}/baseline_s2.jsonl", f"{G4T}/table_eval.json", "base_test_s2"),
    "recover_s2": (f"{PP4}/recover_s2.jsonl", f"{G4T}/table_eval.json", "recover_a0.03_on_s2"),
    "ed0_s2": (f"{PP4}/c02_s2.jsonl", f"{G4T}/table_eval.json", "final_test_s2"),
}
EDS = ["ed0", "ed1", "ed2", "ed3"]
RAND = {"ed0": ["ed0_rand1001", "ed0_rand1002", "ed0_rand1003"], "ed1": ["ed1_rand1001"],
        "ed2": ["ed2_rand1002"], "ed3": ["ed3_rand1003"]}

out_dir = os.path.abspath(sys.argv[1])
os.makedirs(out_dir, exist_ok=True)
ids = [l.strip() for l in open(os.path.join(ROOT, "splits", "test.txt")) if l.strip()]
n = len(ids)
data = {}
for lab, (path, _, _) in SRC.items():
    recs = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, path))}
    assert sorted(recs) == sorted(ids), lab
    data[lab] = [recs[i] for i in ids]

# the gate 1 and c02 rows of the two per-prompt sources must agree
for a, b in ((f"{CHK}/gate1.jsonl", "baseline"), (f"{CHK}/c02_s1.jsonl", "ed0"), (f"{CHK}/recover_s1.jsonl", "recover")):
    other = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, a))}
    for r in data[b]:
        o = other[r["id"]]
        assert (o["scored"], o["fail"], o["full"], o["group"]) == (r["scored"], r["fail"], r["full"], r["group"]), (a, r["id"])

ref = data["baseline"]
cell = np.array([SRCS.index(r["source"]) * 14 + LANGS.index(r["language"]) for r in ref])
OH = np.zeros((n, 42)); OH[np.arange(n), cell] = 1
src_idx = np.array([SRCS.index(r["source"]) for r in ref])


def arrays(lab, fill):
    rs = data[lab]
    sc = np.array([r["scored"] for r in rs], float)
    fa = np.array([r["fail"] for r in rs], float)
    fu = np.array([r["full"] for r in rs], float)
    if fill == "fail":
        fa = np.where(sc == 0, 1, fa); fu = np.where(sc == 0, 1, fu); sc = np.ones(n)
    return sc, fa, fu


def metrics(W, lab, fill):  # compute_metrics averaging, as stats-gate4 stats.py
    S, F, FU = (W @ (OH * x[:, None]) for x in arrays(lab, fill))
    lpr = 1 - F / np.maximum(1, S)
    return {"complex_lpr": 100 * lpr[..., :14].mean(-1),
            "all_lpr": 100 * lpr.reshape(lpr.shape[:-1] + (3, 14)).mean(-2).mean(-1),
            "full_all": 100 * FU.sum(-1) / S.sum(-1),
            "full_complex": 100 * FU[..., :14].sum(-1) / S[..., :14].sum(-1)}


# ---- point values + check against the score tables (drop rule = reported numbers)
ONE = np.ones((1, n))
point = {lab: {f: {k: float(v[0]) for k, v in metrics(ONE, lab, f).items()} for f in FILLS} for lab in data}
check, bad = {}, []
for lab, (_, tpath, tkey) in SRC.items():
    t = json.load(open(os.path.join(ROOT, tpath)))[tkey]
    rs = data[lab]
    mine = {"complex_lpr": round(point[lab]["drop"]["complex_lpr"], 1), "all_lpr": round(point[lab]["drop"]["all_lpr"], 1),
            "full_all": round(point[lab]["drop"]["full_all"], 1), "full_complex": round(point[lab]["drop"]["full_complex"], 1),
            "complex_scored": sum(r["scored"] for r in rs if r["source"] == "complex_prompts"),
            "all_scored": sum(r["scored"] for r in rs)}
    theirs = {"complex_lpr": t["complex"]["lpr"], "all_lpr": t["all"]["lpr"], "full_all": t["all"]["full_pct"],
              "full_complex": t["complex"]["full_pct"], "complex_scored": t["complex"]["scored"],
              "all_scored": t["all"]["scored"]}
    check[lab] = {"table": f"{tpath} [{tkey}]", "mine": mine, "table_values": theirs}
    point[lab]["scored"] = {"complex": mine["complex_scored"], "all": mine["all_scored"]}
    if mine != theirs:
        bad.append(lab)
json.dump({"per_method": check, "mismatch": bad}, open(os.path.join(out_dir, "headline_check.json"), "w"), indent=1)
print("headline mismatches:", bad, flush=True)
if bad:
    sys.exit(1)

# ---- cluster bootstrap (same draws as stats-gate4 and gate5a-checks)
rng = np.random.default_rng(SEED)
W = np.zeros((B, n))
for s in range(3):
    idx = np.where(src_idx == s)[0]
    cl = sorted({ref[i]["group"] for i in idx})
    cid = {c: j for j, c in enumerate(cl)}
    counts = rng.multinomial(len(cl), [1 / len(cl)] * len(cl), size=B)
    W[:, idx] = counts[:, [cid[ref[i]["group"]] for i in idx]]
boot = {(lab, f): metrics(W, lab, f) for lab in data for f in FILLS}


def avg(labs, f, src):  # mean metric over labels, on the same draw (src = boot or point-as-arrays)
    return {k: sum(src[(l, f)][k] for l in labs) / len(labs) for k in METRICS}


pt = {(lab, f): {k: np.array([point[lab][f][k]]) for k in METRICS} for lab in data for f in FILLS}
named = {lab: [lab] for lab in data}
for e in EDS:
    named[e + "_rand"] = RAND[e]
named["mean_editor"] = EDS


def diff_row(a, b, f):
    """a, b: names in `named` (a mean over its labels). paired diff with group ci."""
    if b == "own_rand":
        da_p = {k: np.mean([pt[(e, f)][k][0] - avg(RAND[e], f, pt)[k][0] for e in named[a]]) for k in METRICS}
        da_b = {k: np.mean([boot[(e, f)][k] - avg(RAND[e], f, boot)[k] for e in named[a]], axis=0) for k in METRICS}
    else:
        pa, pb = avg(named[a], f, pt), avg(named[b], f, pt)
        ba, bb = avg(named[a], f, boot), avg(named[b], f, boot)
        da_p = {k: float(pa[k][0] - pb[k][0]) for k in METRICS}
        da_b = {k: ba[k] - bb[k] for k in METRICS}
    return {k: [float(da_p[k]), float(np.percentile(da_b[k], 2.5)), float(np.percentile(da_b[k], 97.5))] for k in METRICS}


comps = []
for f in FILLS:
    for a in EDS + ["mean_editor"]:
        for b in ("baseline", "recover", "own_rand", "instr_end"):
            comps.append({"a": a, "b": b, "fill": f, **diff_row(a, b, f)})
    comps.append({"a": "ed0_s2", "b": "baseline_s2", "fill": f, **diff_row("ed0_s2", "baseline_s2", f)})
    comps.append({"a": "ed0_s2", "b": "recover_s2", "fill": f, **diff_row("ed0_s2", "recover_s2", f)})
    comps.append({"a": "instr_end", "b": "baseline", "fill": f, **diff_row("instr_end", "baseline", f)})

spread = {}
for f in FILLS:
    for b in ("baseline", "recover"):
        for k in METRICS:
            v = [point[e][f][k] - point[b][f][k] for e in EDS]
            spread[f"{f} {b} {k}"] = {"per_editor": v, "mean": float(np.mean(v)), "min": min(v), "max": max(v)}

json.dump({"point": point, "comparisons": comps, "editor_spread": spread,
           "bootstrap": {"B": B, "seed": SEED, "cluster": "split v2 group, within dataset"}},
          open(os.path.join(out_dir, "results.json"), "w"), indent=1)
for lab in data:
    print(lab, {f: {k: round(point[lab][f][k], 1) for k in METRICS} for f in FILLS}, point[lab]["scored"])
for c in comps:
    print(c["a"], "-", c["b"], c["fill"], *(f"{k} {c[k][0]:+.1f} [{c[k][1]:+.1f}, {c[k][2]:+.1f}]" for k in METRICS))
