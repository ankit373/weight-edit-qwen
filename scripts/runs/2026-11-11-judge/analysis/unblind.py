# part C: join judge labels with the key, compare with fastText. stdlib only.
# usage: python3 -I -B unblind.py <judge_dir> <splits/split_meta.json> <out_dir>
import collections
import json
import math
import random
import sys

R, META, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
B = 10000
SEED = 20261111
CROSS = ["baseline", "c02", "recover_a0.03", "instr_end"]
LABS = ["full_lang", "mixed", "wrong", "empty_or_garbage"]
SHORT = {"full_lang": "F", "mixed": "M", "wrong": "W", "empty_or_garbage": "G"}
POP = {"cross": 714, "mono": 200}


def jl(p):
    return [json.loads(x) for x in open(p) if x.strip()]


items = jl(f"{R}/packet/items.jsonl")
key = {k["item_id"]: k for k in jl(f"{R}/key/key.jsonl")}
labels = jl(f"{R}/labels/labels.jsonl")

# ---- checks: one label per packet item
ids = [d["item_id"] for d in items]
lab_ids = [d["item_id"] for d in labels]
cnt = collections.Counter(lab_ids)
check = {
    "n_items": len(ids), "n_label_lines": len(labels), "n_key": len(key),
    "dup_labels": sorted(i for i, c in cnt.items() if c > 1),
    "missing_labels": sorted(set(ids) - set(lab_ids)),
    "extra_labels": sorted(set(lab_ids) - set(ids)),
    "key_eq_packet_ids": set(key) == set(ids),
    "bad_label_values": [d["item_id"] for d in labels if d["label"] not in LABS],
    "bad_conf_values": [d["item_id"] for d in labels if d["confidence"] not in ("high", "low")],
    "last_line": lab_ids[-1],
}
check["ok"] = (not check["dup_labels"] and not check["missing_labels"] and not check["extra_labels"]
               and check["key_eq_packet_ids"] and not check["bad_label_values"] and not check["bad_conf_values"])
assert check["ok"], check
lab = {d["item_id"]: d for d in labels}

# ---- cluster: split v2 group for complex prompts (same rule as stats-gate4 per_prompt.py)
meta = json.load(open(META))
grp = {}
for g in meta["groups"]["complex_prompts"]:
    for r in g:
        grp[r] = f"complex_prompts/{min(g)}"

rows = []
for i in ids:
    k, l = key[i], lab[i]
    s = "mono" if k["set"].startswith("mono") else "cross"
    pid = k["prompt_id"]
    cl = grp[int(pid.split("/")[-1])] if s == "cross" else pid
    rows.append({"item_id": i, "set": s, "method": k["method"], "pid": pid, "cluster": cl,
                 "stratum": k["stratum"], "half": k["stratum"].split("/")[0],
                 "size": k["stratum_size"], "n_sampled": k["stratum_n_sampled"],
                 "ft": k["fasttext_status"], "label": l["label"], "conf": l["confidence"],
                 "reused": k["reused_gate1_row"], "lang": k["language"]})

# check stratum_n_sampled against the rows
sc = collections.Counter((r["set"], r["method"], r["stratum"]) for r in rows)
assert all(sc[(r["set"], r["method"], r["stratum"])] == r["n_sampled"] for r in rows)


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, round(100 * (c - h), 1)), min(100.0, round(100 * (c + h), 1))]


def pct(x):
    return None if x is None else round(100 * x, 1)


def pctl(v, q):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    return v[min(len(v) - 1, max(0, int(round(q * (len(v) - 1)))))]


def ci(v, scale=100):
    lo, hi = pctl(v, 0.025), pctl(v, 0.975)
    return [None if lo is None else round(scale * lo, 1 if scale == 100 else 3),
            None if hi is None else round(scale * hi, 1 if scale == 100 else 3)]


def weights(rs):
    # inverse inclusion probability, using the items kept in this subset
    kept = collections.Counter(r["stratum"] for r in rs)
    return {r["item_id"]: r["size"] / kept[r["stratum"]] for r in rs}


def wshare(rs, w, pred, mult=None):
    num = den = 0.0
    for r in rs:
        m = 1 if mult is None else mult.get(r["cluster"], 0)
        if m:
            num += m * w[r["item_id"]] * pred(r)
            den += m * w[r["item_id"]]
    return num / den if den else None


def kappa(pairs, cats):
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


FT3 = {"pass": "pass", "partial": "partial", "full": "full"}
J3 = {"full_lang": "pass", "mixed": "partial", "wrong": "full", "empty_or_garbage": "full"}
fail = lambda r: r["label"] != "full_lang"
whole = lambda r: r["label"] in ("wrong", "empty_or_garbage")
ftfail = lambda r: r["ft"] in ("partial", "full")


def draws(clusters, rng):
    cl = sorted(clusters)
    out = []
    for _ in range(B):
        out.append(collections.Counter(rng.choice(cl) for _ in cl))
    return out


def analyse(sub_name, keep):
    rng = random.Random(SEED)
    res = {"subset": sub_name}
    rs_all = [r for r in rows if keep(r)]
    res["n_items"] = len(rs_all)
    groups = {("cross", m): [r for r in rs_all if r["set"] == "cross" and r["method"] == m] for m in CROSS}
    groups.update({("mono", m): [r for r in rs_all if r["set"] == "mono" and r["method"] == m]
                   for m in ("baseline", "c02")})
    # same cluster draws for every method of a set (paired comparisons)
    D = {s: draws({r["cluster"] for r in rs_all if r["set"] == s}, rng) for s in ("cross", "mono")}

    res["methods"] = {}
    boot_store = {}
    for (s, m), rs in groups.items():
        e = {"n": len(rs)}
        w = weights(rs)
        strata = {}
        for r in rs:
            strata.setdefault(r["stratum"], {"size": r["size"], "n_kept": 0})["n_kept"] += 1
        for st in strata.values():
            st["weight"] = round(st["size"] / st["n_kept"], 3)
        e["strata"] = dict(sorted(strata.items()))
        e["coverage"] = sum(v["size"] for v in strata.values()) / POP[s]
        # per half, raw shares + wilson
        e["halves"] = {}
        for h in sorted({r["half"] for r in rs}):
            hr = [r for r in rs if r["half"] == h]
            c = collections.Counter(r["label"] for r in hr)
            e["halves"][h] = {"n": len(hr), **{SHORT[l]: [c[l], pct(c[l] / len(hr)), wilson(c[l], len(hr))]
                                                 for l in LABS},
                              "fail": [len(hr) - c["full_lang"], pct((len(hr) - c["full_lang"]) / len(hr)),
                                       wilson(len(hr) - c["full_lang"], len(hr))]}
        # weighted to the full set, cluster bootstrap
        preds = {SHORT[l]: (lambda r, l=l: r["label"] == l) for l in LABS}
        preds["fail"] = fail
        preds["whole"] = whole
        e["weighted"] = {}
        bs = {}
        for name, p in preds.items():
            obs = wshare(rs, w, p)
            bv = [wshare(rs, w, p, d) for d in D[s]]
            bs[name] = bv
            e["weighted"][name] = [pct(obs), ci(bv)]
        # judge fail among fastText-scored answers vs fastText fail rate (same base)
        sc_rs = [r for r in rs if r["ft"] != "unscored"]
        obs = wshare(sc_rs, w, fail)
        bv = [wshare(sc_rs, w, fail, d) for d in D[s]]
        bs["fail_scored"] = bv
        e["weighted"]["fail_scored"] = [pct(obs), ci(bv)]
        boot_store[(s, m)] = bs
        # agreement with fastText (scored items only)
        cm = collections.Counter((r["ft"], SHORT[r["label"]]) for r in rs)
        e["confusion"] = {ft: {SHORT[l]: cm[(ft, SHORT[l])] for l in LABS}
                          for ft in ("pass", "partial", "full", "unscored")}
        p3 = [(FT3[r["ft"]], J3[r["label"]]) for r in sc_rs]
        p2 = [(ftfail(r), fail(r)) for r in sc_rs]
        k3, k2 = kappa(p3, ["pass", "partial", "full"]), kappa(p2, [True, False])
        kb3, kb2 = [], []
        for d in D[s]:
            q3 = [x for r, x in zip(sc_rs, p3) for _ in range(d.get(r["cluster"], 0))]
            q2 = [x for r, x in zip(sc_rs, p2) for _ in range(d.get(r["cluster"], 0))]
            kb3.append(kappa(q3, ["pass", "partial", "full"]))
            kb2.append(kappa(q2, [True, False]))
        e["kappa3"] = [None if k3 is None else round(k3, 3), ci(kb3, 1)]
        e["kappa2"] = [None if k2 is None else round(k2, 3), ci(kb2, 1)]
        e["n_scored_in_sample"] = len(sc_rs)
        # harsh / soft: fastText flagged but judge full_lang; fastText pass but judge not full_lang
        fl = [r for r in rs if ftfail(r)]
        ps = [r for r in rs if r["ft"] == "pass"]
        a = sum(r["label"] == "full_lang" for r in fl)
        b = sum(fail(r) for r in ps)
        e["ft_flag_judge_full"] = [a, len(fl), pct(a / len(fl)) if fl else None, wilson(a, len(fl))]
        e["ft_pass_judge_fail"] = [b, len(ps), pct(b / len(ps)) if ps else None, wilson(b, len(ps))]
        bl = collections.defaultdict(lambda: [0, 0, 0])
        for r in rs:
            bl[r["lang"]][0] += 1
            bl[r["lang"]][1] += fail(r)
            bl[r["lang"]][2] += r["conf"] == "low"
        e["by_language_n_notfull_low"] = dict(sorted(bl.items()))
        res["methods"][f"{s}|{m}"] = e

    # c02 vs recover (and vs baseline) on weighted judge rates, same draws
    res["diffs"] = {}
    for a_, b_ in (("c02", "recover_a0.03"), ("c02", "baseline"), ("recover_a0.03", "baseline")):
        for name in ("fail", "whole", "fail_scored"):
            ea, eb = res["methods"][f"cross|{a_}"], res["methods"][f"cross|{b_}"]
            obs = ea["weighted"][name][0] - eb["weighted"][name][0]
            bv = [None if (x is None or y is None) else x - y
                  for x, y in zip(boot_store[("cross", a_)][name], boot_store[("cross", b_)][name])]
            res["diffs"][f"{a_}-{b_}|{name}"] = [round(obs, 1), ci(bv)]
    bv = [None if (x is None or y is None) else x - y
          for x, y in zip(boot_store[("mono", "c02")]["fail"], boot_store[("mono", "baseline")]["fail"])]
    mo = res["methods"]
    res["diffs"]["mono c02-baseline|fail"] = [round(mo["mono|c02"]["weighted"]["fail"][0]
                                                   - mo["mono|baseline"]["weighted"]["fail"][0], 1), ci(bv)]

    # paired: prompts sampled for both methods
    def paired(s, ma, mb):
        A = {r["pid"]: r for r in rs_all if r["set"] == s and r["method"] == ma}
        Bm = {r["pid"]: r for r in rs_all if r["set"] == s and r["method"] == mb}
        common = sorted(set(A) & set(Bm))
        tab = collections.Counter((SHORT[A[p]["label"]], SHORT[Bm[p]["label"]]) for p in common)
        sev = {"F": 0, "M": 1, "W": 2, "G": 2}
        a_better = sum(sev[x] < sev[y] for (x, y), c in tab.items() for _ in range(c))
        b_better = sum(sev[x] > sev[y] for (x, y), c in tab.items() for _ in range(c))
        a_only_fail = sum(c for (x, y), c in tab.items() if x != "F" and y == "F")
        b_only_fail = sum(c for (x, y), c in tab.items() if x == "F" and y != "F")
        n = a_only_fail + b_only_fail
        p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a_only_fail, b_only_fail) + 1)) / 2 ** n) if n else 1.0
        fa = sum(A[p_]["label"] != "full_lang" for p_ in common)
        fb = sum(Bm[p_]["label"] != "full_lang" for p_ in common)
        return {"n": len(common), "table": {f"{x}/{y}": c for (x, y), c in sorted(tab.items())},
                f"{ma}_fail": [fa, pct(fa / len(common)) if common else None, wilson(fa, len(common))],
                f"{mb}_fail": [fb, pct(fb / len(common)) if common else None, wilson(fb, len(common))],
                f"{ma}_fails_only": a_only_fail, f"{mb}_fails_only": b_only_fail, "mcnemar_exact_p": round(p, 4),
                f"{ma}_less_severe": a_better, f"{mb}_less_severe": b_better,
                "ft": {f"{ma}_flagged": sum(ftfail(A[p_]) for p_ in common),
                       f"{mb}_flagged": sum(ftfail(Bm[p_]) for p_ in common)},
                "rows": [{"pid": p_, ma: SHORT[A[p_]["label"]], mb: SHORT[Bm[p_]["label"]],
                          f"ft_{ma}": A[p_]["ft"], f"ft_{mb}": Bm[p_]["ft"]} for p_ in common]}

    res["paired_c02_recover"] = paired("cross", "c02", "recover_a0.03")
    res["paired_mono"] = paired("mono", "c02", "baseline")
    # mono per source, weighted (gate 4 en LPR = mean over aya and okapi; each source has 100 prompts)
    res["mono_by_source"] = {}
    for m in ("baseline", "c02"):
        rs = groups[("mono", m)]
        w = weights(rs)
        for src in ("aya_human_annotated", "okapi"):
            sr = [r for r in rs if r["stratum"].endswith(src)]
            res["mono_by_source"][f"{m}|{src}"] = {"n": len(sr), "fail_w": pct(wshare(sr, w, fail)),
                                                   "ft_fail_in_sample": sum(ftfail(r) for r in sr)}
    return res


# repeat-consistency: exact duplicate answers (baseline vs instr_end reused rows)
dup = collections.defaultdict(list)
for it in items:
    dup[(it["target_language"], it["prompt"], it["answer"])].append(it["item_id"])
dups = [v for v in dup.values() if len(v) > 1]
same = sum(len({lab[i]["label"] for i in v}) == 1 for v in dups)

out = {"check": check, "B": B, "seed": SEED,
       "dup_groups": len(dups), "dup_groups_same_label": same,
       "dup_detail": [[(i, key[i]["method"], lab[i]["label"], lab[i]["confidence"]) for i in v] for v in dups],
       "all": analyse("all 340", lambda r: True),
       "high": analyse("high confidence only", lambda r: r["conf"] == "high"),
       "low_by_method": dict(collections.Counter(f"{r['set']}|{r['method']}" for r in rows if r["conf"] == "low"))}
json.dump(out, open(f"{OUT}/results.json", "w"), indent=1)
json.dump(rows, open(f"{OUT}/joined.json", "w"), indent=0)
print(json.dumps(check))
print("dup groups", len(dups), "same label", same)
