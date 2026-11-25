"""split v2: cross-lingual LCB prompts into dev / test by base task, so no task text is on both sides.

usage: make_split_v2.py <gate1 ids/all.txt> <lcb test_sets dir> <out_dir>
grouping, worked out from the prompt text (no model outputs read):
  1. same row index in the 14 language files = same base (checked: text equal once the language
     instruction is removed).
  2. different rows that hold the same task with the instruction moved (start / inline / end) are
     merged too: key = prompt with the language instruction removed, lowercased, letters+digits only;
     rows whose keys share >= JACCARD of word 3-gram shingles are joined (union-find).
split: groups shuffled with SEED per dataset, first floor(n/2) groups -> dev, rest -> test.
"""
import collections
import csv
import hashlib
import json
import os
import random
import re
import sys

SEED = 20261106
JACCARD = 0.8
NAME = dict(ar="Arabic", de="German", es="Spanish", fr="French", hi="Hindi", id="Indonesian",
            it="Italian", ja="Japanese", ko="Korean", pt="Portuguese", ru="Russian",
            tr="Turkish", vi="Vietnamese", zh="Chinese")

ids_path, sets_dir, out_dir = sys.argv[1:4]
ids = [l.strip() for l in open(ids_path) if l.strip().startswith("crosslingual/")]
assert len(ids) == 4186, len(ids)


def strip_instruction(text, lang):
    n = NAME[lang]
    t = re.sub(rf"\bWrite your response using {n}\b\.?", " ", text)
    t = re.sub(rf"\b(Reply|Respond|Answer|Write|Make sure to respond|respond|write) in {n}\b\.?", " ", t)
    t = re.sub(rf"\b[Uu]s(e|ing) {n}\b(?!-)\.?", " ", t)
    t = re.sub(rf"\bin {n}\b(?!-)", " ", t)
    return t


def key(text, lang):
    t = strip_instruction(text, lang).lower()
    return " ".join(re.findall(r"[^\W_]+", t))


def shingles(k):
    w = k.split()
    return {" ".join(w[i:i + 3]) for i in range(max(1, len(w) - 2))}


prompt = {}
for pid in ids:
    _, src, lang, row = pid.split("/")
    prompt[pid] = None
for src in sorted({p.split("/")[1] for p in ids}):
    for lang in NAME:
        with open(os.path.join(sets_dir, "crosslingual", src, f"{lang}.csv"), newline="") as f:
            for i, r in enumerate(csv.DictReader(f)):
                prompt[f"crosslingual/{src}/{lang}/{i}"] = r["prompt"]
assert all(prompt[p] is not None for p in ids) and len(prompt) == len(ids)

report = {"seed": SEED, "jaccard": JACCARD}
groups_all = {}
for src in sorted({p.split("/")[1] for p in ids}):
    rows = sorted({int(p.split("/")[3]) for p in ids if p.split("/")[1] == src})
    langs_per_row = collections.Counter(int(p.split("/")[3]) for p in ids if p.split("/")[1] == src)
    # check 1: same row index = same text once the instruction is removed
    misaligned = []
    for r in rows:
        keys = {key(prompt[f"crosslingual/{src}/{l}/{r}"], l) for l in NAME}
        if len(keys) > 1:
            misaligned.append(r)
    # check 2: join rows with the same task (instruction moved); use the first language as reference
    ref = {r: shingles(key(prompt[f"crosslingual/{src}/ar/{r}"], "ar")) for r in rows}
    parent = {r: r for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    joins = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            j = len(ref[a] & ref[b]) / len(ref[a] | ref[b])
            if j >= JACCARD:
                joins.append((a, b, round(j, 3)))
                parent[find(a)] = find(b)
    # same joins must hold in every language (grouping is language independent)
    lang_disagree = []
    for l in NAME:
        sh = {r: shingles(key(prompt[f"crosslingual/{src}/{l}/{r}"], l)) for r in rows}
        for a, b, _ in joins:
            if len(sh[a] & sh[b]) / len(sh[a] | sh[b]) < JACCARD:
                lang_disagree.append((l, a, b))
    groups = collections.defaultdict(list)
    for r in rows:
        groups[find(r)].append(r)
    gl = sorted(groups.values())
    groups_all[src] = gl
    report[src] = {
        "rows": len(rows), "prompts": sum(langs_per_row.values()),
        "rows_missing_a_language": [r for r in rows if langs_per_row[r] != 14],
        "rows_misaligned_after_instruction_removed": misaligned,
        "n_row_joins": len(joins), "joins_failing_in_some_language": lang_disagree[:50],
        "n_groups": len(gl), "group_size_hist": dict(collections.Counter(len(g) for g in gl)),
        "groups_not_size_3": [g for g in gl if len(g) != 3]}

rng = random.Random(SEED)
side = {}
for src in sorted(groups_all):
    gl = list(groups_all[src])
    rng.shuffle(gl)
    k = len(gl) // 2
    for gi, g in enumerate(gl):
        for r in g:
            side[(src, r)] = "dev" if gi < k else "test"
    report[src]["groups_dev"], report[src]["groups_test"] = k, len(gl) - k

dev = [p for p in ids if side[(p.split("/")[1], int(p.split("/")[3]))] == "dev"]
test = [p for p in ids if side[(p.split("/")[1], int(p.split("/")[3]))] == "test"]
assert len(dev) + len(test) == len(ids) and not set(dev) & set(test)

# leak check: no group and no instruction-stripped task key on both sides
gid = {}
for src, gl in groups_all.items():
    for g in gl:
        for r in g:
            gid[(src, r)] = (src, min(g))
dev_g = {gid[(p.split("/")[1], int(p.split("/")[3]))] for p in dev}
test_g = {gid[(p.split("/")[1], int(p.split("/")[3]))] for p in test}
dev_k = {key(prompt[p], p.split("/")[2]) for p in dev}
test_k = {key(prompt[p], p.split("/")[2]) for p in test}
report["leak_check"] = {"groups_in_both": len(dev_g & test_g), "task_keys_in_both": len(dev_k & test_k)}
assert not dev_g & test_g and not dev_k & test_k

cells = collections.defaultdict(lambda: {"dev": 0, "test": 0})
for name, lst in (("dev", dev), ("test", test)):
    for p in lst:
        _, src, lang, _ = p.split("/")
        cells[f"{src}/{lang}"][name] += 1
report["cells"] = dict(sorted(cells.items()))
report["n_dev"], report["n_test"] = len(dev), len(test)
report["groups"] = {s: [g for g in gl] for s, gl in groups_all.items()}
report["group_side"] = {f"{s}/{min(g)}": side[(s, g[0])] for s, gl in groups_all.items() for g in gl}
sha = {}
for name, lst in (("dev.txt", dev), ("test.txt", test)):
    path = os.path.join(out_dir, name)
    with open(path, "w") as f:
        f.write("\n".join(lst) + "\n")
    sha[name] = hashlib.sha256(open(path, "rb").read()).hexdigest()
report["sha256"] = sha
report["source_ids_sha256"] = hashlib.sha256(open(ids_path, "rb").read()).hexdigest()
json.dump(report, open(os.path.join(out_dir, "split_meta.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in report.items() if k not in ("cells", "groups", "group_side")}, indent=1))
