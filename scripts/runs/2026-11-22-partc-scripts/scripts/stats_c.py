"""part C paired stats (PROTOCOL.md section 5), the runs/2026-11-20-stats-2b/scripts/stats.py method
adapted to the part C sets: paired cluster bootstrap (B 10000, seed 20261111, 95% percentile, one
draw shared by every method of a set), group-swap permutation (10000, seed 20261112), exact McNemar.
metrics are recomputed from per-row labels inside each draw (LPR: per-language cell means, then the
mean over cells). run in envs/score (numpy).

usage: stats_c.py <kind> <out.json> <label>=<rows>[,<extra>] ... --pairs a:b[,a:b...]
kinds and row files:
  lpr     per_row_lcb.py output [, loops_rows.py output]  m-ArenaHard, XL-AlpacaEval (cluster base id),
                                                          LCB stress (cluster split v2 task group)
  gmmlu   gmmlu_logit.py rows                             cluster sample_id
  mgsm    mgsm_score.py <prefix>.rows.jsonl               cluster item index
  ifeval  ifeval_score.py <prefix>.rows.jsonl             cluster prompt (single-row clusters)
rows are taken on the first label's ids; every other label must have them (extra ids are ignored,
e.g. seed 1 test rows next to the 714 greedy ids). side kinds also get the damage label of
PROTOCOL.md section 3 for every pair whose b side is a label starting with "baseline".
"""
import json
import math
import sys

import numpy as np

B = 10000
SEED_BOOT, SEED_PERM = 20261111, 20261112
LANGS14 = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
NON_LATIN = ("ar", "hi", "ja", "ko", "ru", "zh")
MGSM_LANGS = ["en", "de", "es", "fr", "ja", "ru", "zh"]
GROUPS = ["Humanities", "STEM", "Social Sciences", "Medical", "Other", "Business"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}


def load_label(kind, spec):
    paths = spec.split(",")
    rows = read(paths[0])
    if len(paths) > 1:  # loops file joined by id
        for pid, x in read(paths[1]).items():
            if pid in rows:
                rows[pid]["loop"] = x["loop"]
    return rows


# ---- features (n x k) and metric functions of the column sums (..., k) per kind

class Kind:
    def __init__(self, kind, ref):
        self.kind = kind
        self.ref = ref
        if kind == "lpr":
            self.langs = sorted({r["language"] for r in ref})
            self.cluster = lambda r: (r["source"], r["cluster"])
            self.stratum = lambda r: r["source"]
        elif kind == "gmmlu":
            self.langs = sorted({r["language"] for r in ref})
            self.cluster = lambda r: r["sample_id"]
            self.stratum = lambda r: 0
        elif kind == "mgsm":
            self.langs = MGSM_LANGS
            self.cluster = lambda r: r["item"]
            self.stratum = lambda r: 0
        elif kind == "ifeval":
            self.cluster = lambda r: r["id"]
            self.stratum = lambda r: 0
        else:
            raise SystemExit(f"unknown kind {kind}")

    def lang_onehot(self, rows):
        L = np.zeros((len(rows), len(self.langs)))
        for i, r in enumerate(rows):
            L[i, self.langs.index(r["language"])] = 1
        return L

    def features(self, rows, unscored="drop"):
        n = len(rows)
        col = lambda k, default=0: np.array([float(r.get(k, default) or 0) for r in rows])
        if self.kind == "lpr":
            sc, fa, fu, wf = col("scored"), col("fail"), col("full"), col("word_fail")
            if unscored == "fail":
                fa, fu, sc = np.where(sc == 0, 1, fa), np.where(sc == 0, 1, fu), np.ones(n)
            elif unscored == "pass":
                fa, fu, sc = np.where(sc == 0, 0, fa), np.where(sc == 0, 0, fu), np.ones(n)
            L = self.lang_onehot(rows)
            extra = np.stack([col("late_switch"), col("loop"), col("hit_max_tokens"), np.ones(n),
                              col("scored")], 1)
            return np.concatenate([L * sc[:, None], L * fa[:, None], L * fu[:, None], L * wf[:, None], extra], 1)
        if self.kind == "gmmlu":
            c = col("correct")
            L = self.lang_onehot(rows)
            G = np.array([[r["group"] == g for g in GROUPS] for r in rows], float)
            C = np.array([[r["cultural_sensitivity_label"] == x for x in ("CS", "CA")] for r in rows], float)
            return np.concatenate([L * c[:, None], L, G * c[:, None], G, C * c[:, None], C], 1)
        if self.kind == "mgsm":
            c = col("correct")
            L = self.lang_onehot(rows)
            extra = np.stack([col("hit_max_tokens"), 1 - col("has_prefix"), np.ones(n)], 1)
            return np.concatenate([L * c[:, None], L, extra], 1)
        has = np.array([1.0 if r["n_scored"] else 0.0 for r in rows])
        return np.stack([col("prompt_strict"), col("prompt_loose"),
                         np.array([sum(x["strict"] for x in r["instructions"]) for r in rows], float),
                         np.array([sum(x["loose"] for x in r["instructions"]) for r in rows], float),
                         col("n_scored"), has, col("hit_max_tokens"), np.ones(n)], 1)

    def metrics(self, S):
        """S: (..., k) column sums -> {name: (...) array}, points."""
        if self.kind == "lpr":
            m = len(self.langs)
            sc, fa, fu, wf = (S[..., i * m:(i + 1) * m] for i in range(4))
            late, loop, hit, n, scored = (S[..., 4 * m + i] for i in range(5))
            lpr = 1 - fa / np.maximum(1, sc)
            nl = [i for i, l in enumerate(self.langs) if l in NON_LATIN]
            wpr = 1 - wf[..., nl] / np.maximum(1, sc[..., nl] - fa[..., nl])
            out = {"lpr": 100 * lpr.mean(-1), "full_pct": 100 * fu.sum(-1) / np.maximum(1, sc.sum(-1)),
                   "wpr": 100 * wpr.mean(-1), "late_switch_pct": 100 * late / np.maximum(1, scored),
                   "loop_pct": 100 * loop / n, "cap_pct": 100 * hit / n}
            for i, l in enumerate(self.langs):
                out[f"lpr_{l}"] = 100 * lpr[..., i]
            return out
        if self.kind == "gmmlu":
            m, g = len(self.langs), len(GROUPS)
            cl, nl = S[..., :m], S[..., m:2 * m]
            cg, ng = S[..., 2 * m:2 * m + g], S[..., 2 * m + g:2 * m + 2 * g]
            cc, nc = S[..., 2 * m + 2 * g:2 * m + 2 * g + 2], S[..., 2 * m + 2 * g + 2:]
            out = {"acc": 100 * cl.sum(-1) / nl.sum(-1)}
            for i, l in enumerate(self.langs):
                out[f"acc_{l}"] = 100 * cl[..., i] / np.maximum(1, nl[..., i])
            for i, x in enumerate(GROUPS):
                out[f"acc_group_{x}"] = 100 * cg[..., i] / np.maximum(1, ng[..., i])
            for i, x in enumerate(("CS", "CA")):
                out[f"acc_{x}"] = 100 * cc[..., i] / np.maximum(1, nc[..., i])
            return out
        if self.kind == "mgsm":
            m = len(self.langs)
            cl, nl = S[..., :m], S[..., m:2 * m]
            hit, nopre, n = S[..., 2 * m], S[..., 2 * m + 1], S[..., 2 * m + 2]
            out = {"acc": 100 * cl.sum(-1) / nl.sum(-1),
                   "acc_en": 100 * cl[..., 0] / np.maximum(1, nl[..., 0]),
                   "acc_non_en": 100 * cl[..., 1:].sum(-1) / np.maximum(1, nl[..., 1:].sum(-1)),
                   "cap_pct": 100 * hit / n, "no_prefix_pct": 100 * nopre / n}
            for i, l in enumerate(self.langs):
                out[f"acc_{l}"] = 100 * cl[..., i] / np.maximum(1, nl[..., i])
            return out
        ps, pl, ins, inl, ni, has, hit, n = (S[..., i] for i in range(8))
        return {"prompt_strict": 100 * ps / has, "prompt_loose": 100 * pl / has,
                "inst_strict": 100 * ins / ni, "inst_loose": 100 * inl / ni, "cap_pct": 100 * hit / n}

    def item_pass(self, rows):
        """per-item pass for McNemar; None = item left out."""
        if self.kind == "lpr":
            return [None if not r["scored"] else int(not r["fail"]) for r in rows]
        if self.kind == "ifeval":
            return [None if not r["n_scored"] else r["prompt_strict"] for r in rows]
        return [int(bool(r["correct"])) for r in rows]


PRIMARY = {"lpr": "lpr", "gmmlu": "acc", "mgsm": "acc", "ifeval": "prompt_strict"}


def cluster_index(kind, rows):
    keys = [(kind.stratum(r), kind.cluster(r)) for r in rows]
    uniq = sorted(set(keys), key=str)
    cid = {k: j for j, k in enumerate(uniq)}
    return np.array([cid[k] for k in keys]), uniq


def boot_weights(kind, rows, cidx, uniq):
    """(B, n) row weights: multinomial cluster counts within each stratum, seed SEED_BOOT."""
    rng = np.random.default_rng(SEED_BOOT)
    Wc = np.zeros((B, len(uniq)), np.float32)
    for s in sorted({u[0] for u in uniq}, key=str):
        js = [j for j, u in enumerate(uniq) if u[0] == s]
        Wc[:, js] = rng.multinomial(len(js), [1 / len(js)] * len(js), size=B)
    return Wc[:, cidx]


def mcnemar(pa, pb):
    x = [(a, b) for a, b in zip(pa, pb) if a is not None and b is not None]
    b_ = sum(1 for p, q in x if p == 1 and q == 0)  # a passes, b fails
    c_ = sum(1 for p, q in x if p == 0 and q == 1)
    k, m = min(b_, c_), b_ + c_
    p = 1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)
    return {"n_pairs": len(x), "a_better": b_, "b_better": c_, "p_exact": p}


def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def damage(d, lo, hi):
    """PROTOCOL.md section 3, edit minus baseline in points."""
    if hi < 0 and d < -1.0:
        lab = "damage"
    elif d < -1.0:
        lab = "possible damage"
    else:
        lab = "no damage shown"
    return {"label": lab, "ruled_out_over_2pts": bool(lab == "no damage shown" and lo >= -2 and hi <= 2)}


def main():
    a = sys.argv[1:]
    pairs = [tuple(p.split(":")) for p in a[a.index("--pairs") + 1].split(",")]
    del a[a.index("--pairs"):a.index("--pairs") + 2]
    kind_name, out = a[0], a[1]
    specs = dict(x.split("=", 1) for x in a[2:])
    labels = list(specs)
    data = {lab: load_label(kind_name, specs[lab]) for lab in labels}
    ids = sorted(data[labels[0]])
    for lab in labels:
        missing = [i for i in ids if i not in data[lab]]
        if missing:
            sys.exit(f"{lab}: {len(missing)} ids missing, e.g. {missing[:3]}")
    rows = {lab: [data[lab][i] for i in ids] for lab in labels}
    K = Kind(kind_name, rows[labels[0]])
    cidx, uniq = cluster_index(K, rows[labels[0]])
    W = boot_weights(K, rows[labels[0]], cidx, uniq)
    prng = np.random.default_rng(SEED_PERM)
    M = prng.integers(0, 2, size=(B, len(uniq))).astype(np.float32)[:, cidx]
    rules = ["drop", "fail", "pass"] if kind_name == "lpr" else ["drop"]
    X = {(lab, ru): K.features(rows[lab], ru) for lab in labels for ru in rules}
    one = lambda x: {k: float(v) for k, v in K.metrics(x.sum(0)).items()}
    obs = {lab: {ru: one(X[(lab, ru)]) for ru in rules} for lab in labels}
    boot = {(lab, ru): K.metrics((W @ X[(lab, ru)].astype(np.float32)).astype(np.float64))
            for lab in labels for ru in rules}
    res = {"kind": kind_name, "B": B, "seed_boot": SEED_BOOT, "seed_perm": SEED_PERM, "n_rows": len(ids),
           "n_clusters": len(uniq), "inputs": specs, "observed": obs, "comparisons": {}}
    for la, lb in pairs:
        comp = {}
        for ru in rules:
            xa, xb = X[(la, ru)], X[(lb, ru)]
            sa = (xa.sum(0) + M @ (xb - xa).astype(np.float32)).astype(np.float64)
            sb = (xa.sum(0) + xb.sum(0)) - sa
            ma, mb = K.metrics(sa), K.metrics(sb)
            e = {}
            for k in obs[la][ru]:
                d = obs[la][ru][k] - obs[lb][ru][k]
                lo, hi = ci(boot[(la, ru)][k] - boot[(lb, ru)][k])
                pd = ma[k] - mb[k]
                e[k] = {"a": obs[la][ru][k], "b": obs[lb][ru][k], "diff": d, "ci": [lo, hi],
                        "p_perm_group": float((1 + np.sum(np.abs(pd) >= abs(d) - 1e-12)) / (B + 1))}
            comp[f"unscored_{ru}" if kind_name == "lpr" else "all"] = e
        prim = comp["unscored_drop" if kind_name == "lpr" else "all"][PRIMARY[kind_name]]
        comp["mcnemar"] = mcnemar(K.item_pass(rows[la]), K.item_pass(rows[lb]))
        if kind_name == "lpr":
            comp["gain_holds"] = prim["ci"][0] > 0
        elif lb.startswith("baseline"):
            comp["damage"] = damage(prim["diff"], *prim["ci"])
            if kind_name in ("gmmlu", "mgsm"):
                comp["language_leads"] = sorted(k for k, v in comp["all"].items()
                                                if k.startswith("acc_") and k[4:] in K.langs and v["ci"][1] < 0)
        res["comparisons"][f"{la}_vs_{lb}"] = comp
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    lines = [f"| {kind_name}: a vs b | metric | a | b | a - b [95% cluster ci] | perm p | note |", "|---|---|---|---|---|---|---|"]
    for name, comp in res["comparisons"].items():
        e = comp["unscored_drop" if kind_name == "lpr" else "all"][PRIMARY[kind_name]]
        note = comp.get("damage", {}).get("label") or ("gain holds" if comp.get("gain_holds") else "")
        lines.append(f"| {name} | {PRIMARY[kind_name]} | {e['a']:.1f} | {e['b']:.1f} | {e['diff']:+.1f} "
                     f"[{e['ci'][0]:+.1f}, {e['ci'][1]:+.1f}] | {e['p_perm_group']:.4f} | {note} |")
    with open(out.removesuffix(".json") + ".md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
