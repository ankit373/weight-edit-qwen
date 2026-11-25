"""build the blinded judge packet and its key. stdlib only, cpu, fixed seed.

usage: sample.py   (run from the project root; paths and seed are fixed below)
"""
import collections
import json
import os
import random

SEED = 20261122
R = "runs/2026-11-24-judge-2b"
B1 = "runs/2026-11-11-gate5b-baseline/outputs"
IE = "runs/2026-11-13-gate5b-instr-end/outputs"
RC = "runs/2026-11-14-gate5b-recover/outputs"
EV = "runs/2026-11-17-gate5b-eval/outputs"
CROSS = {  # method: (rows file, labels file)
    "baseline": (f"{B1}/baseline_test.jsonl", f"{R}/labels/baseline.jsonl"),
    "c06": (f"{EV}/final_test.jsonl", f"{R}/labels/c06.jsonl"),
    "recover_a0.03": (f"{RC}/recover_a0.03_off_test.jsonl", f"{R}/labels/recover_a0.03.jsonl"),
    "instr_end": (f"{IE}/instr_end_test.jsonl", f"{R}/labels/instr_end.jsonl"),
}
MONO = {
    "baseline": (f"{B1}/baseline_mono.jsonl", f"{R}/labels/baseline_mono_en.jsonl"),
    "c06": (f"{EV}/final_mono.jsonl", f"{R}/labels/c06_mono_en.jsonl"),
}
N_CROSS, N_FLAG = 60, 30   # per method; flagged half
N_MONO_PER_SOURCE = 25     # 2 sources x 25 = 50 per method
NAMES = {"ar": "Arabic", "de": "German", "en": "English", "es": "Spanish", "fr": "French", "hi": "Hindi",
         "id": "Indonesian", "it": "Italian", "ja": "Japanese", "ko": "Korean", "pt": "Portuguese",
         "ru": "Russian", "tr": "Turkish", "vi": "Vietnamese", "zh": "Chinese"}
FLAG = ("partial", "full")


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path))}


def allocate(sizes, total):
    """split total over strata: 1 per non-empty stratum, rest by largest remainder of size share."""
    keys = sorted(k for k, v in sizes.items() if v > 0)
    alloc = {k: 1 for k in keys}
    left, pool = total - len(keys), {k: sizes[k] - 1 for k in keys}
    cap = sum(pool.values())
    quota = {k: left * pool[k] / cap for k in keys}
    for k in keys:
        alloc[k] += int(quota[k])
    rest = left - sum(int(q) for q in quota.values())
    for k in sorted(keys, key=lambda k: (-(quota[k] - int(quota[k])), k))[:rest]:
        alloc[k] += 1
    assert sum(alloc.values()) == total and all(alloc[k] <= sizes[k] for k in keys)
    return alloc


rng = random.Random(SEED)
# one shared random priority per prompt id (coordinated sampling): every method takes the lowest
# priorities inside its own strata, so the same prompt ids are picked across methods where possible.
base_rows = load(CROSS["baseline"][0])
cx_ids = sorted(i for i, r in base_rows.items() if r["source"] == "complex_prompts")
prio = {i: rng.random() for i in cx_ids}


def original_prompt(r):  # instr_end rows: prompt_original is set only where the prompt was changed
    return r.get("prompt_original", r["prompt"])


# the packet shows the baseline prompt for every method; check it equals each method's original prompt
prompt_check = {}
for m, (rows_f, _) in CROSS.items():
    rows = load(rows_f)
    prompt_check[m] = sum(original_prompt(rows[i]) == base_rows[i]["prompt"] for i in cx_ids)
    assert prompt_check[m] == len(cx_ids), (m, prompt_check[m])

key, picked = [], {}
for m, (rows_f, lab_f) in CROSS.items():
    rows, labs = load(rows_f), load(lab_f)
    strata = collections.defaultdict(list)  # (flagged?, language) -> ids
    for i in cx_ids:
        strata[(labs[i]["status"] in FLAG, labs[i]["language"])].append(i)
    langs = sorted({lang for _, lang in strata})
    for flag, n in ((True, N_FLAG), (False, N_CROSS - N_FLAG)):
        alloc = allocate({g: len(strata[(flag, g)]) for g in langs}, n)
        for g, k in alloc.items():
            pop = strata[(flag, g)]
            for i in sorted(pop, key=prio.get)[:k]:
                r, lab = rows[i], labs[i]
                key.append({
                    "set": "cross_complex_test_seed1", "method": m, "prompt_id": i, "language": g,
                    "stratum": ("flagged" if flag else "not_flagged") + "/" + g,
                    "stratum_size": len(pop), "stratum_n_sampled": k,
                    "fasttext_status": lab["status"], "fasttext_line_idx": lab["line_idx"],
                    "fasttext_line_labels": lab["line_labels"], "fasttext_en_word": lab["en_word"],
                    "reused_baseline_row": m == "instr_end" and "prompt_original" not in r,
                    "hit_max_tokens": r["hit_max_tokens"],
                    "_prompt": base_rows[i]["prompt"], "_answer": r["completion"],
                })
    picked[m] = {e["prompt_id"] for e in key if e["method"] == m}

# mono english: one shared id set for both methods (fully paired). ids flagged by either method all
# go in; the rest of each source's 25 is filled by the lowest shared priority.
mono = {m: (load(rf), load(lf)) for m, (rf, lf) in MONO.items()}
mono_prompt_same = sum(mono["baseline"][0][i]["prompt"] == mono["c06"][0][i]["prompt"] for i in mono["baseline"][0])
assert mono_prompt_same == len(mono["baseline"][0]) == len(mono["c06"][0])
en_ids = sorted(mono["baseline"][1])
mprio = {i: rng.random() for i in en_ids}
src = {i: mono["baseline"][0][i]["source"] for i in en_ids}
flag_any = {i for i in en_ids if any(mono[m][1][i]["status"] in FLAG for m in MONO)}
mono_ids, mono_stratum = [], {}
for s in sorted(set(src.values())):
    f_ids = sorted(i for i in flag_any if src[i] == s)
    rest = sorted((i for i in en_ids if src[i] == s and i not in flag_any), key=mprio.get)
    take = rest[:N_MONO_PER_SOURCE - len(f_ids)]
    for i in f_ids:
        mono_stratum[i] = ("flagged_any/" + s, len(f_ids), len(f_ids))
    for i in take:
        mono_stratum[i] = ("not_flagged/" + s, len(rest), len(take))
    mono_ids += f_ids + take
for m, (rows, labs) in mono.items():
    for i in mono_ids:
        r, lab = rows[i], labs[i]
        st, size, k = mono_stratum[i]
        key.append({
            "set": "mono_en_seed1", "method": m, "prompt_id": i, "language": "en",
            "stratum": st, "stratum_size": size, "stratum_n_sampled": k,
            "fasttext_status": lab["status"], "fasttext_line_idx": lab["line_idx"],
            "fasttext_line_labels": lab["line_labels"], "fasttext_en_word": lab["en_word"],
            "reused_baseline_row": False, "hit_max_tokens": r["hit_max_tokens"],
            "_prompt": rows[i]["prompt"], "_answer": r["completion"],
        })

# shuffle all items together, then give random ids (drawn after the shuffle, so ids carry no order)
rng.shuffle(key)
ids = set()
while len(ids) < len(key):
    ids.add("%08x" % rng.getrandbits(32))
ids = sorted(ids)
rng.shuffle(ids)
os.makedirs(f"{R}/packet", exist_ok=True)
os.makedirs(f"{R}/key", exist_ok=True)
with open(f"{R}/packet/items.jsonl", "w") as fp, open(f"{R}/key/key.jsonl", "w") as fk:
    for iid, e in zip(ids, key):
        fp.write(json.dumps({"item_id": iid, "target_language": NAMES[e["language"]],
                             "prompt": e.pop("_prompt"), "answer": e.pop("_answer")}, ensure_ascii=False) + "\n")
        fk.write(json.dumps({"item_id": iid, **e}, ensure_ascii=False) + "\n")

# summary for the README
summ = collections.Counter((e["set"], e["method"], e["stratum"].split("/")[0]) for e in key)
print(json.dumps({"n_items": len(key), "by_set_method_stratum": {"|".join(k): v for k, v in sorted(summ.items())},
                  "cross_shared_all4": len(set.intersection(*picked.values())),
                  "cross_shared_c06_recover": len(picked["c06"] & picked["recover_a0.03"]),
                  "cross_distinct_prompts": len(set.union(*picked.values())),
                  "mono_ids": len(mono_ids), "mono_flagged_any": len(flag_any),
                  "prompt_equal_to_baseline_complex": prompt_check, "mono_prompt_equal_all": mono_prompt_same,
                  "instr_end_reused_baseline_rows_complex": sum("prompt_original" not in r for i, r in
                                                                load(CROSS["instr_end"][0]).items() if i in prio)}, indent=1))
