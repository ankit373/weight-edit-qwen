"""paired cluster-bootstrap + permutation + mcnemar on per-prompt LCB scores (from per_prompt.py).

usage: stats.py <per_prompt_dir> <out_dir> <recover tag, e.g. a0.05_on>
writes <out_dir>/headline_check.json, results.json, tables.md. exits 1 if headline numbers differ.
part B copy of the gate 4 stats script: headline check against the 2B eval folder's table_eval.json
(queue_b6.sh score) and final_table.md; the edit label is "edit" (gate 4: "c02").
"""
import collections
import glob
import json
import math
import os
import sys

import numpy as np

B = 10000
SEED_BOOT, SEED_PERM = 20261111, 20261112
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
_ev = sorted(glob.glob(os.path.join(ROOT, "runs", "[0-9]*-gate5b-eval")))
assert len(_ev) == 1, _ev
G4 = os.path.join(_ev[0], "scores")  # name kept from the gate 4 script: the 2B eval scores folder
TAG = sys.argv[3]
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SRCS = ["complex_prompts", "okapi", "sharegpt"]
LABELS = ["baseline_s1", "instr_end_s1", "recover_s1", "edit_s1", "rand1001_s1", "rand1002_s1",
          "rand1003_s1", "baseline_s2", "instr_end_s2", "recover_s2", "edit_s2"]
METRICS = ["complex_lpr", "all_lpr", "full_all", "full_complex"]

pp_dir, out_dir = sys.argv[1], sys.argv[2]
ids = [l.strip() for l in open(os.path.join(ROOT, "splits", "test.txt")) if l.strip()]
data = {}
for lab in LABELS:
    recs = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(pp_dir, lab + ".jsonl"))}
    data[lab] = [recs[i] for i in ids]
ref = data["edit_s1"]
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
tab = json.load(open(os.path.join(G4, "table_eval.json")))
TKEY = {"baseline_s1": "baseline", "instr_end_s1": "instr_end", "recover_s1": f"recover_{TAG}",
        "edit_s1": "final_test", "rand1001_s1": "rand_s1001_test", "rand1002_s1": "rand_s1002_test",
        "rand1003_s1": "rand_s1003_test", "baseline_s2": "base_test_s2", "instr_end_s2": "instr_end_s2",
        "recover_s2": f"recover_{TAG}_s2", "edit_s2": "final_test_s2"}
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
# final_table.md main-table rows (s1 / s2 strings)
md = open(os.path.join(G4, "final_table.md")).read().split("\n")
rowname = {"baseline": "| baseline |", "instr_end": "| instruction at end |",
           "recover": "| ReCoVeR winner |", "edit": "| **final edit** |"}  # row starts final_table.md must use
md_chk = {}
for m, prefix in rowname.items():
    line = next(l for l in md if l.startswith(prefix))
    for key in ("complex_lpr", "all_lpr", "full_all"):
        s = f"{chk[m + '_s1']['mine'][key]:.1f} / {chk[m + '_s2']['mine'][key]:.1f}"
        md_chk[f"{m} {key}"] = [s, s in line]
        if s not in line:
            bad.append(f"md {m} {key}")
rmean = {k: sum(chk[f"rand{s}_s1"]["mine"][k] for s in (1001, 1002, 1003)) / 3 for k in ("complex_lpr", "all_lpr")}
line = next(l for l in md if l.startswith("| random control, mean"))
for k in ("complex_lpr", "all_lpr"):
    vals = [chk[f"rand{s}_s1"]["mine"][k] for s in (1001, 1002, 1003)]
    s = f"{round(rmean[k], 1):.1f} ({min(vals):.1f} - {max(vals):.1f})"
    md_chk[f"random {k}"] = [s, s in line]
    if s not in line:
        bad.append(f"md random {k}")
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
boot_unsc = {mode: {lab: metrics(W_group, arrays(lab, mode)) for lab in ("edit_s1", "edit_s2", "recover_s1", "recover_s2")}
             for mode in ("fail", "pass")}
obs_unsc = {mode: {lab: {k: v[0] for k, v in metrics(ONE, arrays(lab, mode)).items()}
                   for lab in ("edit_s1", "edit_s2", "recover_s1", "recover_s2")} for mode in ("fail", "pass")}


def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def pair_specs(a, b):
    """seed-wise and pooled comparisons of method a vs b."""
    if b.startswith("rand"):
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
                ds = [perm_diff(x, y, Ms[i])[k] for i, (x, y) in enumerate(zip(la, lb))]
                dp = sum(ds) / len(ds)
                e[f"p_{mname}"] = float((1 + np.sum(np.abs(dp) >= abs(d_obs) - 1e-12)) / (B + 1))
            r[k] = e
        if len(la) == 1:
            sub = lambda lab: [x for x in data[lab] if x["source"] == "complex_prompts"]
            r["mcnemar_complex_fail"] = mcnemar(sub(la[0]), sub(lb[0]), "fail")
            r["mcnemar_complex_full"] = mcnemar(sub(la[0]), sub(lb[0]), "full")
            r["mcnemar_all_fail"] = mcnemar(data[la[0]], data[lb[0]], "fail")
            r["mcnemar_all_full"] = mcnemar(data[la[0]], data[lb[0]], "full")
        res[tag] = r
    return res


results = {"B": B, "seed_boot": SEED_BOOT, "seed_perm": SEED_PERM, "n_groups": n_groups, "n_row_clusters": n_rows,
           "observed": obs, "comparisons": {}}
for b in ("recover", "baseline", "instr_end", "rand1001", "rand1002", "rand1003"):
    results["comparisons"][f"edit_vs_{b}"] = compare("edit", b)
    print("done", b, flush=True)

# ---- q2: unscored as fail / pass (both methods), and one-sided bounds
q2 = {}
for tag, la, lb in pair_specs("edit", "recover"):
    q2[tag] = {}
    for mode_a, mode_b in (("fail", "fail"), ("pass", "pass"), ("fail", "pass"), ("pass", "fail")):
        e = {}
        for k in METRICS:
            d_obs = mean_over(obs_unsc[mode_a], la, k) - mean_over(obs_unsc[mode_b], lb, k)
            d = mean_over(boot_unsc[mode_a], la, k) - mean_over(boot_unsc[mode_b], lb, k)
            e[k] = {"diff": float(d_obs), "ci_group": ci(d), "a": float(mean_over(obs_unsc[mode_a], la, k)),
                    "b": float(mean_over(obs_unsc[mode_b], lb, k))}
        q2[tag][f"edit_unscored_{mode_a}__recover_unscored_{mode_b}"] = e
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
    "edit_s1_and_baseline_s1": len(uns("edit_s1") & uns("baseline_s1")),
    "edit_s1_and_recover_s1": len(uns("edit_s1") & uns("recover_s1")),
    "edit_s1_and_edit_s2": len(uns("edit_s1") & uns("edit_s2")),
    "edit_s1_ids": sorted(uns("edit_s1"))}
results["q2_reasons"] = reasons

# ---- q3: per-language complex LPR
q3 = {}
for li, lang in enumerate(LANGS):
    e = {}
    for lab in LABELS:
        e[lab] = obs[lab]["lang_complex"][li]
    for b in ("recover", "baseline"):
        for tag, la, lb in pair_specs("edit", b):
            d_obs = sum(obs[x]["lang_complex"][li] for x in la) / len(la) - sum(obs[x]["lang_complex"][li] for x in lb) / len(lb)
            d = (sum(boot["group"][x]["lang_complex"][:, li] for x in la) / len(la)
                 - sum(boot["group"][x]["lang_complex"][:, li] for x in lb) / len(lb))
            c = ci(d)
            e[f"edit_vs_{b}_{tag}"] = {"diff": d_obs, "ci_group": c, "worse": c[1] < 0, "better": c[0] > 0}
    q3[lang] = e
results["q3_lang"] = q3
json.dump(results, open(os.path.join(out_dir, "results.json"), "w"), indent=1, default=float)
print("wrote results.json", flush=True)
