"""instr_end output for a split = generated rows (changed prompts) + gate 1 rows (unchanged
prompts, marked reused_gate1). usage: merge_instr_end.py <changed.jsonl> <gate1_split.jsonl> <split_ids> <out.jsonl>"""
import json, sys
gen = {r["id"]: r for r in map(json.loads, open(sys.argv[1]))}
g1 = {r["id"]: r for r in map(json.loads, open(sys.argv[2]))}
ids = [x.strip() for x in open(sys.argv[3]) if x.strip()]
n_gen = 0
with open(sys.argv[4], "w") as f:
    for i in ids:
        if i in gen:
            r = gen[i]; n_gen += 1
        else:
            r = dict(g1[i], variant="instr_end", reused_gate1=True)
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("generated", n_gen, "reused", len(ids) - n_gen)
