"""counts for the README, from labels/, key/ and packet/. stdlib only, reads only files made in this run.

usage: summary.py   (run from the project root)
"""
import collections
import json
import re

R = "runs/2026-11-24-judge-2b"
FLAG = ("partial", "full")
SETS = ["baseline", "c06", "recover_a0.03", "instr_end", "baseline_mono_en", "c06_mono_en"]
out = {}

# population: flagged and unscored counts per labels file, flagged by language for the cross sets
labs = {s: [json.loads(l) for l in open(f"{R}/labels/{s}.jsonl")] for s in SETS}
out["population"] = {s: dict(collections.Counter(r["status"] for r in rows)) for s, rows in labs.items()}
out["flagged_by_language"] = {s: dict(sorted(collections.Counter(r["language"] for r in labs[s]
                                                                 if r["status"] in FLAG).items()))
                              for s in SETS[:4]}
fl = {s: {r["id"] for r in labs[s] if r["status"] in FLAG} for s in SETS[:4]}
out["flagged_shared_c06_recover"] = len(fl["c06"] & fl["recover_a0.03"])
out["flagged_union_c06_recover"] = len(fl["c06"] | fl["recover_a0.03"])

# sample: fastText status mix, flagged half by language, unscored, reused rows
key = [json.loads(l) for l in open(f"{R}/key/key.jsonl")]
grp = lambda e: ("mono_" if e["set"].startswith("mono") else "") + e["method"]
out["sample_status"] = {g: dict(sorted(collections.Counter(e["fasttext_status"] for e in key if grp(e) == g).items()))
                        for g in sorted({grp(e) for e in key})}
out["sample_flagged_by_language"] = {
    g: dict(sorted(collections.Counter(e["language"] for e in key
                                       if grp(e) == g and e["stratum"].startswith("flagged/")).items()))
    for g in ["baseline", "c06", "recover_a0.03", "instr_end"]}
out["sample_reused_baseline_row"] = sum(e["reused_baseline_row"] for e in key)
out["mono_strata"] = dict(collections.Counter(e["stratum"] for e in key if e["set"].startswith("mono")
                                              and e["method"] == "c06"))

# packet: prompt lengths (the change from the 0.8B judge is that prompts are read in full)
items = [json.loads(l) for l in open(f"{R}/packet/items.jsonl")]
plen = sorted(len(it["prompt"]) for it in items)
out["prompt_chars"] = {"n": len(plen), "over_120": sum(x > 120 for x in plen), "median": plen[len(plen) // 2],
                       "max": plen[-1]}

# substring hits of grep terms that have no whole-word example in leak_check.json
ctx = collections.defaultdict(list)
for t in ["c02", "2b", "instr", "gate", "edit", "nie", "aya", "mono", "recover", "partial"]:
    for it in items:
        for fld in ("item_id", "prompt", "answer"):
            for m in re.finditer(re.escape(t), it[fld], re.I):
                w = re.search(r"\S*$", it[fld][:m.start()]).group() + re.match(r"\S*", it[fld][m.start():]).group()
                ctx[t].append(f"{fld}:{w[:40]}")
out["substring_words"] = {t: dict(collections.Counter(v).most_common(8)) for t, v in ctx.items()}

print(json.dumps(out, indent=1, ensure_ascii=False))
