"""build gate5b-workspace ids/ and data/ from splits/dev.txt and the 2B B1 baseline outputs. dev rows only.

usage: make_data.py <project root> <2B B1 full_nonthinking.jsonl>
part B copy of gate 4 setup make_data.py: only the workspace and the outputs path changed.
"""
import collections
import csv
import glob
import hashlib
import json
import os
import random
import sys

SCREEN_N = 200
SCREEN_SEED = 20261109

root = os.path.abspath(sys.argv[1])
ws = os.path.join(root, "gate5b-workspace")
test_sets = os.path.join(root, "external", "lcb_test_sets", "test_sets")
gate1_out = os.path.abspath(sys.argv[2])  # 2B baseline rows (B1); file names inside the workspace kept


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# same load order as gate 1 gen.py, so seed_index = gate 1's index_of[pid]
order = []
prompts = {}
for path in sorted(glob.glob(os.path.join(test_sets, "*", "*", "*.csv"))):
    task, source_dir, fname = path.split(os.sep)[-3:]
    lang = fname.removesuffix(".csv")
    with open(path, newline="") as f:
        for i, r in enumerate(csv.DictReader(f)):
            pid = f"{task}/{source_dir}/{lang}/{i}"
            order.append(pid)
            prompts[pid] = {"id": pid, "task": task, "source": r["source"], "language": lang,
                            "prompt": r["prompt"]}
index_of = {pid: i for i, pid in enumerate(order)}
all_ids = [l.strip() for l in open(os.path.join(root, "runs", "2026-11-05-gate1-baseline", "ids", "all.txt")) if l.strip()]
assert all_ids == order, "load order differs from gate 1 ids/all.txt"

dev_src = os.path.join(root, "splits", "dev.txt")
dev = [l.strip() for l in open(dev_src) if l.strip()]
test = set(l.strip() for l in open(os.path.join(root, "splits", "test.txt")) if l.strip())
assert not set(dev) & test

os.makedirs(os.path.join(ws, "ids"), exist_ok=True)
os.makedirs(os.path.join(ws, "data"), exist_ok=True)
dev_dst = os.path.join(ws, "ids", "dev.txt")
open(dev_dst, "wb").write(open(dev_src, "rb").read())
assert sha(dev_dst) == sha(dev_src)

with open(os.path.join(ws, "data", "dev_prompts.jsonl"), "w") as f:
    for pid in dev:
        f.write(json.dumps({**prompts[pid], "seed_index": index_of[pid]}, ensure_ascii=False) + "\n")

devset = set(dev)
with open(os.path.join(ws, "data", "gate1_dev_outputs.jsonl"), "w") as f:
    n = 0
    for line in open(gate1_out):
        if json.loads(line)["id"] in devset:
            f.write(line)
            n += 1
assert n == len(dev), n

# screen200: 4 per (dataset, language) cell = 168, 32 more cells get a 5th, cells and rows by seeded random
cells = collections.defaultdict(list)
for pid in dev:
    _, src, lang, _ = pid.split("/")
    cells[(src, lang)].append(pid)
keys = sorted(cells)
rng = random.Random(SCREEN_SEED)
base = SCREEN_N // len(keys)
extra = set(rng.sample(keys, SCREEN_N - base * len(keys)))
screen = []
for k in keys:
    screen += sorted(rng.sample(cells[k], base + (k in extra)), key=dev.index)
screen.sort(key=dev.index)
assert len(screen) == SCREEN_N and len(set(screen)) == SCREEN_N and set(screen) <= devset
open(os.path.join(ws, "ids", "screen200.txt"), "w").write("\n".join(screen) + "\n")
meta = {"seed": SCREEN_SEED, "n": SCREEN_N, "per_cell_base": base,
        "cells_with_extra": sorted("/".join(k) for k in extra),
        "per_cell": {"/".join(k): sum(1 for p in screen if p.split("/")[1:3] == list(k)) for k in keys},
        "per_dataset": dict(collections.Counter(p.split("/")[1] for p in screen))}
json.dump(meta, open(os.path.join(ws, "ids", "screen200_meta.json"), "w"), indent=1)

for p in ("ids/dev.txt", "ids/screen200.txt", "data/dev_prompts.jsonl", "data/gate1_dev_outputs.jsonl"):
    print(sha(os.path.join(ws, p)), p)
print(json.dumps(meta["per_dataset"]))
