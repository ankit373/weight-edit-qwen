"""paired cluster-bootstrap + permutation + mcnemar on per-prompt LCB scores (from per_prompt.py).

usage: stats.py <per_prompt_dir> <out_dir>
writes <out_dir>/headline_check.json, results.json, tables.md. exits 1 if headline numbers differ.
"""
import collections
import json
import math
import os
import sys

import numpy as np

B = 10000
SEED_BOOT, SEED_PERM = 20261111, 20261112
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G4 = os.path.join(ROOT, "runs", "2026-11-17-gate5b-eval", "scores")  # name kept; 2B eval scores folder
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SRCS = ["complex_prompts", "okapi", "sharegpt"]
LABELS = ["baseline_s1", "instr_end_s1", "recover_s1", "recover_a1_s1", "c06_s1", "rand1001_s1", "rand1002_s1",
          "rand1003_s1", "baseline_s2", "instr_end_s2", "recover_s2", "c06_s2"]
METRICS = ["complex_lpr", "all_lpr", "full_all", "full_complex"]

pp_dir, out_dir = sys.argv[1], sys.argv[2]
ids = [l.strip() for l in open(os.path.join(ROOT, "splits", "test.txt")) if l.strip()]
data = {}
for lab in LABELS:
    recs = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(pp_dir, lab + ".jsonl"))}
    data[lab] = [recs[i] for i in ids]
ref = data["c06_s1"]
n = len(ids)
cell_idx = np.array([SRCS.index(r["source"]) * 14 + LANGS.index(r["language"]) for r in ref])
OH = np.zeros((n, 42), np.float32); OH[np.arange(n), cell_idx] = 1
src_idx = np.array([SRCS.index(r["source"]) for r in ref])
lang_of = [r["language"] for r in ref]


def arrays(lab, unscored=None):
    rs = data[lab]
    sc = np.array([r["scored"] for r in rs], float)
    fa = np.array([r["fail"] for r in rs], float)
    fu = np.array([r["full"] for r in rs], float)
    if unscored == "fail":
        fa = np.where(sc == 0, 1, fa); fu = np.where(sc == 0, 1, fu); sc = np.ones(n)
    elif unscored == "pass":
        fa = np.where(sc == 0, 0, fa); fu = np.where(sc == 0, 0, fu); sc = np.ones(n)
    return sc, fa, fu


def metrics_from_sums(S, F, FU):
    """S, F, FU: (..., 42) weighted cell sums. compute_metrics averaging."""
    lpr = 1 - F / np.maximum(1, S)
    cx = lpr[..., :14].mean(-1)
    per_lang = lpr.reshape(lpr.shape[:-1] + (3, 14)).mean(-2)  # mean over sources per language
    al = per_lang.mean(-1)
    full_all = 100 * FU.sum(-1) / S.sum(-1)
    full_cx = 100 * FU[..., :14].sum(-1) / S[..., :14].sum(-1)
    return {"complex_lpr": 100 * cx, "all_lpr": 100 * al, "full_all": full_all, "full_complex": full_cx,
            "lang_complex": 100 * lpr[..., :14]}


def metrics(W, arr):
    sc, fa, fu = (x.astype(np.float32) for x in arr)
    return metrics_from_sums(*((W @ (OH * x[:, None])).astype(np.float64) for x in (sc, fa, fu)))


ONE = np.ones((1, n), np.float32)

# ---- headline check against the gate 4 table files
tab = json.load(open(os.path.join(G4, "table_eval.json")))  # 2B has one table file, no table_cited.json
TKEY = {"baseline_s1": "baseline", "instr_end_s1": "instr_end", "recover_s1": "recover_a0.03_off",
        "recover_a1_s1": "recover_a1_on",
        "c06_s1": "final_test", "rand1001_s1": "rand_s1001_test", "rand1002_s1": "rand_s1002_test",
        "rand1003_s1": "rand_s1003_test", "baseline_s2": "base_test_s2", "instr_end_s2": "instr_end_s2",
        "recover_s2": "recover_a0.03_off_s2", "c06_s2": "final_test_s2"}
obs = {lab: {k: float(v[0]) if k != "lang_complex" else v[0].tolist()
             for k, v in metrics(ONE, arrays(lab)).items()} for lab in LABELS}
chk, bad = {}, []
for lab in LABELS:
    t = tab[TKEY[lab]]
    rs = data[lab]
    mine = {"complex_lpr": round(obs[lab]["complex_lpr"], 1), "all_lpr": round(obs[lab]["all_lpr"], 1),
            "full_all": round(obs[lab]["full_all"], 1), "full_complex": round(obs[lab]["full_complex"], 1),
            "complex_scored": sum(r["scored"] for r in rs if r["source"] == "complex_prompts"),
            "all_scored": sum(r["scored"] for r in rs)}
    theirs = {"complex_lpr": t["complex"]["lpr"], "all_lpr": t["all"]["lpr"], "full_all": t["all"]["full_pct"],
              "full_complex": t["complex"]["full_pct"], "complex_scored": t["complex"]["scored"],
              "all_scored": t["all"]["scored"]}
    chk[lab] = {"mine": mine, "table_json": theirs}
    if mine != theirs:
        bad.append(lab)
md_chk = {}  # 2B eval has no final_table.md; check is against table_eval.json only
json.dump({"per_method": chk, "final_table_md": md_chk, "mismatch": bad},
          open(os.path.join(out_dir, "headline_check.json"), "w"), indent=1)
print("headline mismatches:", bad, flush=True)
if bad:
    sys.exit(1)

# ---- cluster bootstrap weights (same draws for every method)
def cluster_weights(key, rng):
    W = np.zeros((B, n), np.float32)
    for s in range(3):
        idx = np.where(src_idx == s)[0]
        clusters = sorted({key(ref[i]) for i in idx})
        cid = {c: j for j, c in enumerate(clusters)}
        counts = rng.multinomial(len(clusters), [1 / len(clusters)] * len(clusters), size=B)
        W[:, idx] = counts[:, [cid[key(ref[i])] for i in idx]]
    return W, {SRCS[s]: len({key(ref[i]) for i in np.where(src_idx == s)[0]}) for s in range(3)}


rng = np.random.default_rng(SEED_BOOT)
W_group, n_groups = cluster_weights(lambda r: r["group"], rng)
W_row, n_rows = cluster_weights(lambda r: (r["source"], r["row"]), rng)
print("clusters group", n_groups, "row", n_rows, flush=True)

boot = {}
for name, W in (("group", W_group), ("row", W_row)):
    boot[name] = {lab: metrics(W, arrays(lab)) for lab in LABELS}
boot_unsc = {mode: {lab: metrics(W_group, arrays(lab, mode)) for lab in LABELS}
             for mode in ("fail", "pass")}
obs_unsc = {mode: {lab: {k: v[0] for k, v in metrics(ONE, arrays(lab, mode)).items()}
                   for lab in LABELS} for mode in ("fail", "pass")}


def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def pair_specs(a, b):
    """seed-wise and pooled comparisons of method a vs b."""
    if a == "randmean":  # mean of the three random controls (same draw) vs b seed 1
        return [("s1", [f"rand{x}_s1" for x in (1001, 1002, 1003)], [f"{b}_s1"])]
    if a.startswith("rand") or b.startswith("rand") or a.endswith("_a1") or b.endswith("_a1"):
        return [("s1", [f"{a}_s1"], [f"{b}_s1"])]
    return [("s1", [f"{a}_s1"], [f"{b}_s1"]), ("s2", [f"{a}_s2"], [f"{b}_s2"]),
            ("pooled", [f"{a}_s1", f"{a}_s2"], [f"{b}_s1", f"{b}_s2"])]


def mean_over(d, labs, k):
    return sum(d[l][k] for l in labs) / len(labs)


# ---- permutation (prompt-level and group-level label swap)
prng = np.random.default_rng(SEED_PERM)
M_prompt = [prng.integers(0, 2, size=(B, n)).astype(np.float32) for _ in range(2)]  # one mask per seed
gid = {g: j for j, g in enumerate(sorted({r["group"] for r in ref}))}
gidx = np.array([gid[r["group"]] for r in ref])
M_group = [prng.integers(0, 2, size=(B, len(gid))).astype(np.float32)[:, gidx] for _ in range(2)]


_perm_cache = {}


def perm_diff(la, lb, M):
    key = (la, lb, id(M))
    if key not in _perm_cache:
        _perm_cache[key] = _perm_diff(la, lb, M)
    return _perm_cache[key]


def _perm_diff(la, lb, M):
    A, Bb = arrays(la), arrays(lb)
    sums_a, sums_b = [], []
    for xa, xb in zip(A, Bb):
        ca, cb = OH * xa.astype(np.float32)[:, None], OH * xb.astype(np.float32)[:, None]
        sa = (ca.sum(0) + M @ (cb - ca)).astype(np.float64)  # (1-M)@ca + M@cb
        sums_a.append(sa)
        sums_b.append((ca + cb).sum(0).astype(np.float64) - sa)
    ma, mb = metrics_from_sums(*sums_a), metrics_from_sums(*sums_b)
    return {k: ma[k] - mb[k] for k in METRICS}


def mcnemar(A, Bb, what):
    if what == "fail":
        both = [(a, b) for a, b in zip(A, Bb) if a["scored"] and b["scored"]]
        x = [(a["fail"], b["fail"]) for a, b in both]
    else:
        x = [(a["full"], b["full"]) for a, b in zip(A, Bb)]
    b_ = sum(1 for p, q in x if p == 0 and q == 1)  # a passes, b fails
    c_ = sum(1 for p, q in x if p == 1 and q == 0)
    k, m = min(b_, c_), b_ + c_
    p = 1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)
    return {"n_pairs": len(x), "a_better": b_, "b_better": c_, "p_exact": p}


def compare(a, b):
    res = {}
    for tag, la, lb in pair_specs(a, b):
        r = {}
        for k in METRICS:
            d_obs = mean_over(obs, la, k) - mean_over(obs, lb, k)
            e = {"a": mean_over(obs, la, k), "b": mean_over(obs, lb, k), "diff": d_obs}
            for cl in ("group", "row"):
                d = mean_over(boot[cl], la, k) - mean_over(boot[cl], lb, k)
                e[f"ci_{cl}"] = ci(d)
            for mname, Ms in (("perm_prompt", M_prompt), ("perm_group", M_group)):
                if len(la) != len(lb):
                    e[f"p_{mname}"] = None; continue
                ds = [perm_diff(x, y, Ms[i])[k] for i, (x, y) in enumerate(zip(la, lb))]
                dp = sum(ds) / len(ds)
                e[f"p_{mname}"] = float((1 + np.sum(np.abs(dp) >= abs(d_obs) - 1e-12)) / (B + 1))
            for mode in ("fail", "pass"):
                d_obs_u = mean_over(obs_unsc[mode], la, k) - mean_over(obs_unsc[mode], lb, k)
                d_u = mean_over(boot_unsc[mode], la, k) - mean_over(boot_unsc[mode], lb, k)
                e[f"unscored_{mode}"] = {"a": float(mean_over(obs_unsc[mode], la, k)),
                                         "b": float(mean_over(obs_unsc[mode], lb, k)),
                                         "diff": float(d_obs_u), "ci_group": ci(d_u)}
            r[k] = e
        if len(la) == 1 and len(lb) == 1:
            sub = lambda lab: [x for x in data[lab] if x["source"] == "complex_prompts"]
            r["mcnemar_complex_fail"] = mcnemar(sub(la[0]), sub(lb[0]), "fail")
            r["mcnemar_complex_full"] = mcnemar(sub(la[0]), sub(lb[0]), "full")
            r["mcnemar_all_fail"] = mcnemar(data[la[0]], data[lb[0]], "fail")
            r["mcnemar_all_full"] = mcnemar(data[la[0]], data[lb[0]], "full")
        res[tag] = r
    return res


results = {"B": B, "seed_boot": SEED_BOOT, "seed_perm": SEED_PERM, "n_groups": n_groups, "n_row_clusters": n_rows,
           "observed": obs, "comparisons": {}}
PAIRS = [("c06", b) for b in ("recover", "baseline", "instr_end", "rand1001", "rand1002", "rand1003")]
PAIRS += [("recover", "baseline"), ("recover_a1", "baseline"),
          ("rand1001", "baseline"), ("rand1002", "baseline"), ("rand1003", "baseline"), ("randmean", "baseline")]
for a, b in PAIRS:
    results["comparisons"][f"{a}_vs_{b}"] = compare(a, b)
    print("done", a, b, flush=True)

# ---- q2: unscored as fail / pass (both methods), and one-sided bounds
q2 = {}
for tag, la, lb in pair_specs("c06", "recover"):
    q2[tag] = {}
    for mode_a, mode_b in (("fail", "fail"), ("pass", "pass"), ("fail", "pass"), ("pass", "fail")):
        e = {}
        for k in METRICS:
            d_obs = mean_over(obs_unsc[mode_a], la, k) - mean_over(obs_unsc[mode_b], lb, k)
            d = mean_over(boot_unsc[mode_a], la, k) - mean_over(boot_unsc[mode_b], lb, k)
            e[k] = {"diff": float(d_obs), "ci_group": ci(d), "a": float(mean_over(obs_unsc[mode_a], la, k)),
                    "b": float(mean_over(obs_unsc[mode_b], lb, k))}
        q2[tag][f"c06_unscored_{mode_a}__recover_unscored_{mode_b}"] = e
results["q2_unscored_bounds"] = q2

# unscored reasons
reasons = {}
for lab in LABELS:
    c = collections.Counter()
    for r in data[lab]:
        if not r["scored"]:
            c[(r["source"], r["language"], r["reason"])] += 1
    reasons[lab] = {"rows": [[*k, v] for k, v in sorted(c.items())]}
    br = collections.Counter(); bs = collections.Counter(); bl = collections.Counter()
    for (s, l, why), v in c.items():
        br[why] += v; bs[s] += v
        if s == "complex_prompts":
            bl[l] += v
    reasons[lab]["by_reason"] = dict(br); reasons[lab]["by_source"] = dict(bs); reasons[lab]["complex_by_lang"] = dict(bl)
    cx_uns = [r for r in data[lab] if r["source"] == "complex_prompts" and not r["scored"]]
    reasons[lab]["complex_unscored"] = len(cx_uns)
    reasons[lab]["complex_unscored_by_reason"] = dict(collections.Counter(r["reason"] for r in cx_uns))
    reasons[lab]["complex_unscored_hit_max_tokens"] = sum(1 for r in cx_uns if r["hit_max_tokens"])
    reasons[lab]["complex_unscored_max_line_tokens_hist"] = dict(sorted(collections.Counter(r["max_line_tokens"] for r in cx_uns).items()))
    reasons[lab]["complex_unscored_nonempty_lines_hist"] = dict(sorted(collections.Counter(r["n_nonempty_lines"] for r in cx_uns).items()))
    reasons[lab]["complex_unscored_by_group"] = dict(collections.Counter(r["group"] for r in cx_uns))
    reasons[lab]["fail_only_unknown_lines_all"] = sum(1 for r in data[lab] if r["fail"] and r["n_bad"] == r["n_unknown"])
    reasons[lab]["fail_only_unknown_lines_complex"] = sum(1 for r in data[lab] if r["fail"] and r["n_bad"] == r["n_unknown"] and r["source"] == "complex_prompts")
uns = lambda lab: {r["id"] for r in data[lab] if r["source"] == "complex_prompts" and not r["scored"]}
reasons["_overlap_complex"] = {
    "c06_s1_and_baseline_s1": len(uns("c06_s1") & uns("baseline_s1")),
    "c06_s1_and_recover_s1": len(uns("c06_s1") & uns("recover_s1")),
    "c06_s1_and_c06_s2": len(uns("c06_s1") & uns("c06_s2")),
    "c06_s1_ids": sorted(uns("c06_s1"))}
results["q2_reasons"] = reasons

# ---- q3: per-language complex LPR
q3 = {}
for li, lang in enumerate(LANGS):
    e = {}
    for lab in LABELS:
        e[lab] = obs[lab]["lang_complex"][li]
    for b in ("recover", "baseline"):
        for tag, la, lb in pair_specs("c06", b):
            d_obs = sum(obs[x]["lang_complex"][li] for x in la) / len(la) - sum(obs[x]["lang_complex"][li] for x in lb) / len(lb)
            d = (sum(boot["group"][x]["lang_complex"][:, li] for x in la) / len(la)
                 - sum(boot["group"][x]["lang_complex"][:, li] for x in lb) / len(lb))
            c = ci(d)
            e[f"c06_vs_{b}_{tag}"] = {"diff": d_obs, "ci_group": c, "worse": c[1] < 0, "better": c[0] > 0}
    q3[lang] = e
results["q3_lang"] = q3
# ---- mono (2B only): c06 vs baseline, all mono LPR. no split groups here, so clusters = (source, row)
# stratified by source, and a prompt-level view. own rng with the same seed.
def mono_rows(lab):
    return sorted((json.loads(l) for l in open(os.path.join(pp_dir, lab + ".jsonl"))), key=lambda r: r["id"])


ma, mb = mono_rows("c06_mono"), mono_rows("baseline_mono")
assert [r["id"] for r in ma] == [r["id"] for r in mb]
mcells = sorted({(r["source"], r["language"]) for r in ma})
mlangs = sorted({c[1] for c in mcells})
mOH = np.zeros((len(ma), len(mcells)), np.float32)
mOH[np.arange(len(ma)), [mcells.index((r["source"], r["language"])) for r in ma]] = 1
lang_mask = np.array([[c[1] == l for c in mcells] for l in mlangs], np.float64)  # (langs, cells)


def mono_lpr(W, rs):
    sc = np.array([r["scored"] for r in rs], np.float32); fa = np.array([r["fail"] for r in rs], np.float32)
    S = (W @ (mOH * sc[:, None])).astype(np.float64); F = (W @ (mOH * fa[:, None])).astype(np.float64)
    lpr = 1 - F / np.maximum(1, S)
    per_lang = (lpr @ lang_mask.T) / lang_mask.sum(1)  # mean over sources per language
    return 100 * per_lang.mean(-1)


msrc = sorted({r["source"] for r in ma})
mrng = np.random.default_rng(SEED_BOOT)
mono_res = {"n": len(ma), "cells": len(mcells)}
oneM = np.ones((1, len(ma)), np.float32)
o_a, o_b = float(mono_lpr(oneM, ma)[0]), float(mono_lpr(oneM, mb)[0])
mono_res.update({"c06": o_a, "baseline": o_b, "diff": o_a - o_b})
for cname, key in (("source_row", lambda r: (r["source"], r["row"])), ("prompt", lambda r: r["id"])):
    W = np.zeros((B, len(ma)), np.float32)
    for s_ in msrc:
        idx = [i for i, r in enumerate(ma) if r["source"] == s_]
        cl = sorted({key(ma[i]) for i in idx}); cid = {c: j for j, c in enumerate(cl)}
        counts = mrng.multinomial(len(cl), [1 / len(cl)] * len(cl), size=B)
        W[:, idx] = counts[:, [cid[key(ma[i])] for i in idx]]
    mono_res[f"ci_{cname}"] = ci(mono_lpr(W, ma) - mono_lpr(W, mb))
    mono_res[f"n_clusters_{cname}"] = {s_: len({key(r) for r in ma if r["source"] == s_}) for s_ in msrc}
mono_res["mcnemar_fail"] = mcnemar(ma, mb, "fail")
mono_res["mcnemar_full"] = mcnemar(ma, mb, "full")
results["mono"] = mono_res
print("mono", mono_res, flush=True)
json.dump(results, open(os.path.join(out_dir, "results.json"), "w"), indent=1, default=float)
print("wrote results.json", flush=True)
