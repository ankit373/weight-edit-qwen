"""check the judge packet for label leaks. stdlib only. writes logs/leak_check.json, prints a summary.

usage: leak_check.py   (run from the project root)
"""
import collections
import json
import os
import random
import re

R = "runs/2026-11-24-judge-2b"
TERMS = ["c02", "c06", "2b", "recover", "recovery", "steer", "steering", "instr", "instruction", "baseline", "gate",
         "method", "fasttext", "lpr", "seed", "qwen", "edit", "edited", "random", "control", "nie", "judge", "key",
         "flagged", "partial", "score", "complex_prompts", "crosslingual", "monolingual", "okapi", "aya", "mono"]
out = {}

files = sorted(os.listdir(f"{R}/packet"))
out["packet_files"] = files
out["packet_files_ok"] = files == ["RUBRIC.md", "items.jsonl"]

items = [json.loads(l) for l in open(f"{R}/packet/items.jsonl")]
key = {e["item_id"]: e for e in map(json.loads, open(f"{R}/key/key.jsonl"))}
out["n_items"] = len(items)
out["fields_ok"] = all(set(it) == {"item_id", "target_language", "prompt", "answer"} for it in items)
out["ids_ok"] = (len({it["item_id"] for it in items}) == len(items)
                 and all(re.fullmatch(r"[0-9a-f]{8}", it["item_id"]) for it in items)
                 and set(key) == {it["item_id"] for it in items})


def group(e):
    return ("mono_" if e["set"].startswith("mono") else "") + e["method"]


grp = [group(key[it["item_id"]]) for it in items]
groups = sorted(set(grp))

# 1. term grep, case-insensitive. whole-word hits and raw substring hits, per field and per group
rubric = open(f"{R}/packet/RUBRIC.md").read()
grep = {}
for t in TERMS:
    word = re.compile(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", re.I)
    sub = re.compile(re.escape(t), re.I)
    rec = {"rubric_word": len(word.findall(rubric)), "rubric_sub": len(sub.findall(rubric))}
    for fld in ("item_id", "target_language", "prompt", "answer"):
        rec[fld + "_word"] = sum(bool(word.search(it[fld])) for it in items)
        rec[fld + "_sub"] = sum(bool(sub.search(it[fld])) for it in items)
    hits = [(g, it) for g, it in zip(grp, items) if word.search(it["answer"]) or word.search(it["prompt"])]
    rec["word_hits_by_group"] = dict(collections.Counter(g for g, _ in hits))
    rec["examples"] = []
    for g, it in hits[:4]:
        for fld in ("prompt", "answer"):
            m = word.search(it[fld])
            if m:
                rec["examples"].append(f"{fld}: ...{it[fld][max(0, m.start() - 40):m.end() + 40]}...".replace("\n", " "))
    grep[t] = rec
out["grep"] = grep
out["id_pattern_hits"] = sum(bool(re.search(r"(crosslingual|monolingual|complex_prompts)/", it["prompt"] + it["answer"]))
                             for it in items)
out["special_token_hits"] = {g: sum(bool(re.search(r"<\|[a-z_]+\|>|</?think>", it["answer"]))
                                    for gg, it in zip(grp, items) if gg == g) for g in groups}


# 2. order: file position and item-id order vs group. chi-square on quintile x group, permutation p
def chi2(labels, bins):
    tab = collections.Counter(zip(labels, bins))
    rt, ct, n = collections.Counter(labels), collections.Counter(bins), len(labels)
    return sum((tab[(a, b)] - rt[a] * ct[b] / n) ** 2 / (rt[a] * ct[b] / n) for a in rt for b in ct)


def perm_p(labels, bins, n=10000, seed=1):
    rng, obs, lab, hit = random.Random(seed), chi2(labels, bins), list(labels), 0
    for _ in range(n):
        rng.shuffle(lab)
        hit += chi2(lab, bins) >= obs
    return obs, (hit + 1) / (n + 1)


N = len(items)
pos_q = [5 * i // N for i in range(N)]
rank = {iid: r for r, iid in enumerate(sorted(it["item_id"] for it in items))}
id_q = [5 * rank[it["item_id"]] // N for it in items]
out["order"] = {
    "mean_file_position_by_group": {g: round(sum(i for i, gg in enumerate(grp) if gg == g) / grp.count(g) / N, 3)
                                    for g in groups},
    "file_position_quintile_chi2_perm_p": perm_p(grp, pos_q),
    "item_id_rank_quintile_chi2_perm_p": perm_p(grp, id_q),
}


# 3. answer length bands by group (characters), share at the 100-token cap, length-only separability
def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


lens = collections.defaultdict(list)
for g, it in zip(grp, items):
    lens[g].append(len(it["answer"]))
out["length_chars"] = {g: {"n": len(v), "min": min(v), "q25": q(v, .25), "median": q(v, .5), "q75": q(v, .75),
                           "max": max(v)} for g, v in lens.items()}
out["hit_max_tokens_share"] = {g: round(sum(key[it["item_id"]]["hit_max_tokens"] for gg, it in zip(grp, items)
                                            if gg == g) / grp.count(g), 3) for g in groups}


def auc(a, b):  # P(len a > len b), ties half
    return sum((x > y) + 0.5 * (x == y) for x in a for y in b) / (len(a) * len(b))


out["length_auc"] = {f"{a} vs {b}": round(auc(lens[a], lens[b]), 3)
                     for a, b in [("c06", "recover_a0.03"), ("c06", "baseline"), ("recover_a0.03", "baseline"),
                                  ("instr_end", "baseline"), ("mono_c06", "mono_baseline")]}
qz = [q(sum(lens.values(), []), p) for p in (.25, .5, .75)]
lband = [sum(len(it["answer"]) > t for t in qz) for it in items]
out["length_quartile_chi2_perm_p_cross_only"] = perm_p(
    [g for g in grp if not g.startswith("mono")], [b for g, b in zip(grp, lband) if not g.startswith("mono")])

# 4. target-language mix by group (comes from the per-method strata)
mix = {g: dict(sorted(collections.Counter(it["target_language"] for gg, it in zip(grp, items) if gg == g).items()))
       for g in groups}
out["language_mix"] = mix
a, b = mix["c06"], mix["recover_a0.03"]
out["language_mix_tvd_c06_vs_recover"] = round(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b)) / 120, 3)

# 5. exact duplicate (prompt, answer) pairs in the packet
dup = collections.defaultdict(list)
for g, it in zip(grp, items):
    dup[(it["target_language"], it["prompt"], it["answer"])].append(g)
dups = [v for v in dup.values() if len(v) > 1]
out["duplicate_groups"] = len(dups)
out["duplicate_groups_by_methods"] = dict(collections.Counter("+".join(sorted(v)) for v in dups))
out["duplicates_from_reused_baseline_row"] = sum(key[it["item_id"]]["reused_baseline_row"] for it in items
                                              if len(dup[(it["target_language"], it["prompt"], it["answer"])]) > 1)

json.dump(out, open(f"{R}/logs/leak_check.json", "w"), indent=1, ensure_ascii=False)
short = {k: v for k, v in out.items() if k != "grep"}
short["grep_nonzero"] = {t: {k: v for k, v in r.items() if v and k != "examples"} for t, r in grep.items()
                         if any(v for k, v in r.items() if k not in ("examples", "word_hits_by_group"))}
print(json.dumps(short, indent=1, ensure_ascii=False))
