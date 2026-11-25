"""id files for gate 3. usage: make_ids.py <project_root> <out_dir>
all lists keep the order of splits/dev.txt or splits/test.txt.
"""
import json
import os
import random
import sys

root, out = sys.argv[1], sys.argv[2]


def read(p):
    return [x.strip() for x in open(p) if x.strip()]


def write(name, ids):
    with open(os.path.join(out, name), "w") as f:
        f.write("".join(i + "\n" for i in ids))
    print(name, len(ids))


dev = read(os.path.join(root, "splits/dev.txt"))
test = read(os.path.join(root, "splits/test.txt"))
allids = read(os.path.join(root, "runs/2026-11-05-gate1-baseline/ids/all.txt"))
meta = json.load(open(os.path.join(root, "splits/split_meta.json")))

write("repro20_dev.txt", sorted(random.Random(0).sample(dev, 20), key=dev.index))
write("dev_complex.txt", [i for i in dev if "/complex_prompts/" in i])
write("test_complex.txt", [i for i in test if "/complex_prompts/" in i])
mono = [i for i in allids if i.startswith("monolingual/")]
write("mono_all.txt", mono)
write("mono20.txt", sorted(random.Random(1).sample(mono, 20), key=mono.index))

# nie folds: dev task groups, half per dataset to fold A, by group (no group on both sides)
row_group = {}
for ds, groups in meta["groups"].items():
    for g in groups:
        for r in g:
            row_group[(ds, r)] = f"{ds}/{g[0]}"
dev_groups = sorted({row_group[(i.split("/")[1], int(i.split("/")[3]))] for i in dev})
rng = random.Random(20261107)
fold_a = set()
for ds in sorted({g.split("/")[0] for g in dev_groups}):
    gs = [g for g in dev_groups if g.startswith(ds + "/")]
    rng.shuffle(gs)
    fold_a.update(gs[: len(gs) // 2])
a = [i for i in dev if row_group[(i.split("/")[1], int(i.split("/")[3]))] in fold_a]
b = [i for i in dev if i not in set(a)]
write("dev_foldA.txt", a)
write("dev_foldB.txt", b)
write("dev_foldB_complex.txt", [i for i in b if "/complex_prompts/" in i])
json.dump(sorted(fold_a), open(os.path.join(out, "dev_foldA_groups.json"), "w"), indent=0)
