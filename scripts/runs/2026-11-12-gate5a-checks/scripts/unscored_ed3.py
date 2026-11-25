"""part A unscored check, editor 3 (copy of unscored.py, only the method list and comparisons changed): per-prompt drop reasons and complex LPR with unscored filled as fail / pass.

usage: unscored.py <out_dir>
per-prompt rule and reason classes: copied from runs/2026-11-11-stats-gate4/scripts/per_prompt.py.
bootstrap: same settings as runs/2026-11-11-stats-gate4/scripts/stats.py (groups, 10000, seed 20261111).
exits 1 if a rebuilt score cell or failing-id set differs from the score files.
"""
import collections
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G1 = os.path.join(ROOT, "runs", "2026-11-05-gate1-baseline")
G3 = "runs/2026-11-06-gate3-run"
G4 = "runs/2026-11-10-gate4-eval"
W1 = "runs/2026-11-11-gate5a-eval-ws1"
W2 = "runs/2026-11-12-gate5a-eval-ws2"
W3 = "runs/2026-11-13-gate5a-eval-ws3"
METHODS = {  # label: (rows, score prefix)
    "gate1": (f"{G3}/outputs/baseline_test.jsonl", f"{G3}/scores/baseline_test"),
    "ed3": (f"{W3}/outputs/final_test.jsonl", f"{W3}/scores/final_test"),
    "ed3_rand1003": (f"{W3}/outputs/rand_s1003_test.jsonl", f"{W3}/scores/rand_s1003_test"),
    "c02_s1": (f"{G4}/outputs/final_test.jsonl", f"{G4}/scores/final_test"),
    "recover_s1": (f"{G3}/outputs/recover_a0.03_on_test.jsonl", f"{G3}/scores/recover_a0.03_on_test"),
}
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SRCS = ["complex_prompts", "okapi", "sharegpt"]
B, SEED_BOOT = 10000, 20261111

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


def score_one(r):  # same as stats-gate4 per_prompt.py
    comp, lang = r["completion"], r["language"]
    norm = cm.normalize(comp)
    lines = norm.split("\n")
    lens = [len(cm.tokenize(l, lang)) for l in lines]
    kept = [l for l, n in zip(lines, lens) if n >= 5]
    labels = [cm.langid(l) for l in kept]
    bad = [x for x in labels if x != lang]
    d = {"scored": int(bool(kept)), "fail": int(bool(kept) and bool(bad)),
         "full": int(bool(kept) and len(bad) == len(kept)), "empty": int(not comp.strip()), "reason": None}
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
        nonempty = [n for l, n in zip(lines, lens) if l.strip()]
        d["max_line_tokens"] = max(nonempty) if nonempty else 0
        d["n_nonempty_lines"] = len(nonempty)
    return d


def cells(recs):
    c = collections.defaultdict(lambda: [0, 0, 0, 0])  # n, scored, fails, empty
    for r in recs:
        x = c[(r["source"], r["language"])]
        x[0] += 1; x[1] += r["scored"]; x[2] += r["fail"]; x[3] += r["empty"]
    return c


# ---- per-prompt rows + check against the score files
data, check, bad_any = {}, {}, False
for label, (rows_path, prefix) in METHODS.items():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, rows_path))]
    assert sorted(r["id"] for r in rows) == sorted(test_ids), label
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
    c = cells(recs)
    table = json.load(open(os.path.join(ROOT, prefix + ".json")))
    diffs = []
    for t in table:
        if t.get("task") != "crosslingual" or "n_scored" not in t or "all" in (t["source"], t["language"]):
            continue
        n, s, fl, e = c[(t["source"], t["language"])]
        if (n, s, e) != (t["n"], t["n_scored"], t["n_empty"]) or abs(1 - fl / max(1, s) - t["lpr"]) > 1e-12:
            diffs.append([t["source"], t["language"]])
    wl = json.load(open(os.path.join(ROOT, prefix + "_wrong_lang.json")))
    wl_fail = {f["id"]: f["full_response_wrong"] for f in wl["failing_responses"]}
    if wl_fail != {d["id"]: bool(d["full"]) for d in recs if d["fail"]}:
        diffs.append("wrong_lang failing ids differ")
    check[label] = {"rows": rows_path, "score_prefix": prefix, "diffs": diffs}
    bad_any |= bool(diffs)
    rec_by = {d["id"]: d for d in recs}
    data[label] = [rec_by[i] for i in test_ids]
    print(label, "diffs", len(diffs), flush=True)
json.dump(check, open(os.path.join(out_dir, "check.json"), "w"), indent=1)
if bad_any:
    sys.exit(1)

# ---- unscored reasons (complex)
reasons = {}
for lab, rs in data.items():
    cx = [r for r in rs if r["source"] == "complex_prompts" and not r["scored"]]
    other = [r for r in rs if r["source"] != "complex_prompts" and not r["scored"]]
    reasons[lab] = {
        "complex_unscored": len(cx), "complex_scored": 714 - len(cx), "other_unscored": len(other),
        "by_reason": dict(collections.Counter(r["reason"] for r in cx)),
        "hit_cap": sum(1 for r in cx if r["hit_max_tokens"]),
        "by_group": dict(collections.Counter(r["group"] for r in cx).most_common()),
        "by_lang": {l: sum(1 for r in cx if r["language"] == l) for l in LANGS},
        "ids": sorted(r["id"] for r in cx),
    }
g1u = set(reasons["gate1"]["ids"])
for lab in reasons:
    reasons[lab]["shared_with_gate1"] = len(g1u & set(reasons[lab]["ids"]))
for o in ("ed1", "ed2"):  # unscored ids of editors 1 and 2 from the earlier run of unscored.py
    prev = {json.loads(l)["id"] for l in open(os.path.join(out_dir, "..", o + ".jsonl"))
            if json.loads(l)["source"] == "complex_prompts" and not json.loads(l)["scored"]}
    reasons["ed3"]["shared_with_" + o] = len(prev & set(reasons["ed3"]["ids"]))

# ---- LPR with unscored dropped / fail / pass, group bootstrap (stats-gate4 settings)
n = len(test_ids)
ref = data["gate1"]
cell_idx = np.array([SRCS.index(r["source"]) * 14 + LANGS.index(r["language"]) for r in ref])
OH = np.zeros((n, 42)); OH[np.arange(n), cell_idx] = 1
src_idx = np.array([SRCS.index(r["source"]) for r in ref])


def arrays(lab, mode):
    rs = data[lab]
    sc = np.array([r["scored"] for r in rs], float)
    fa = np.array([r["fail"] for r in rs], float)
    fu = np.array([r["full"] for r in rs], float)
    if mode == "fail":
        fa = np.where(sc == 0, 1, fa); fu = np.where(sc == 0, 1, fu); sc = np.ones(n)
    elif mode == "pass":
        fa = np.where(sc == 0, 0, fa); fu = np.where(sc == 0, 0, fu); sc = np.ones(n)
    return sc, fa, fu


def metrics(W, lab, mode):
    S, F, FU = (W @ (OH * x[:, None]) for x in arrays(lab, mode))
    lpr = 1 - F / np.maximum(1, S)
    return {"complex_lpr": 100 * lpr[..., :14].mean(-1),
            "all_lpr": 100 * lpr.reshape(lpr.shape[:-1] + (3, 14)).mean(-2).mean(-1),
            "full_complex": 100 * FU[..., :14].sum(-1) / S[..., :14].sum(-1)}


rng = np.random.default_rng(SEED_BOOT)
W = np.zeros((B, n))
for s in range(3):
    idx = np.where(src_idx == s)[0]
    cl = sorted({ref[i]["group"] for i in idx})
    cid = {c: j for j, c in enumerate(cl)}
    counts = rng.multinomial(len(cl), [1 / len(cl)] * len(cl), size=B)
    W[:, idx] = counts[:, [cid[ref[i]["group"]] for i in idx]]
ONE = np.ones((1, n))

point = {lab: {m: {k: float(v[0]) for k, v in metrics(ONE, lab, m).items()} for m in ("drop", "fail", "pass")}
         for lab in data}
boot = {(lab, m): metrics(W, lab, m) for lab in ("gate1", "ed3", "c02_s1", "recover_s1") for m in ("drop", "fail", "pass")}
comps = []
for a in ("ed3",):
    for b in ("gate1", "c02_s1", "recover_s1"):
        for ma, mb in (("drop", "drop"), ("fail", "fail"), ("pass", "pass"), ("fail", "pass"), ("pass", "fail")):
            row = {"a": a, "b": b, "fill_a": ma, "fill_b": mb}
            for k in ("complex_lpr", "all_lpr", "full_complex"):
                d = boot[(a, ma)][k] - boot[(b, mb)][k]
                row[k] = [point[a][ma][k] - point[b][mb][k],
                          float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
            comps.append(row)

json.dump({"reasons": reasons, "point": point, "comparisons": comps,
           "bootstrap": {"B": B, "seed": SEED_BOOT, "cluster": "split v2 group, within dataset"}},
          open(os.path.join(out_dir, "results.json"), "w"), indent=1, ensure_ascii=False)
for lab, r in reasons.items():
    print(lab, r["complex_unscored"], r["by_reason"], "cap", r["hit_cap"], "shared_g1", r["shared_with_gate1"])
for lab in data:
    print(lab, {m: round(point[lab][m]["complex_lpr"], 1) for m in point[lab]})
for c in comps:
    print(c["a"], "-", c["b"], c["fill_a"], "/", c["fill_b"],
          *(f"{k} {v[0]:+.1f} [{v[1]:+.1f}, {v[2]:+.1f}]" for k, v in c.items() if k in ("complex_lpr", "all_lpr", "full_complex")))
