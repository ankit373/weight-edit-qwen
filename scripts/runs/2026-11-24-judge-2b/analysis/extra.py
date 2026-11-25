# counts only: fastText population rates and where the low-confidence and mixed calls fall
# usage (from the run folder): python3 -I -B analysis/extra.py
import collections
import json

jl = lambda p: [json.loads(x) for x in open(p) if x.strip()]
print("fastText population (labels/<set>.jsonl): fail = partial+full over scored, full over scored")
for s in ("baseline", "c06", "recover_a0.03", "instr_end", "baseline_mono_en", "c06_mono_en"):
    c = collections.Counter(r["status"] for r in jl(f"labels/{s}.jsonl"))
    sc = c["pass"] + c["partial"] + c["full"]
    print(f"  {s}: n {sum(c.values())}, scored {sc}, fail {c['partial'] + c['full']} "
          f"({100 * (c['partial'] + c['full']) / sc:.1f}%), full {c['full']} ({100 * c['full'] / sc:.1f}%)")

rows = {r["item_id"]: r for r in json.load(open("analysis/joined.json"))}
lab = {r["item_id"]: r for r in jl("judge/labels.jsonl")}
items = {d["item_id"]: d for d in jl("packet/items.jsonl")}
cross = [i for i, r in rows.items() if r["set"] == "cross"]


def topic(i):
    p = items[i]["prompt"].lower()
    for k, t in (("headline", "headlines"), ("vowel", "ipa table"), ("weather", "weather tsv"),
                 ("insurance", "insurance json"), ("transcript", "insurance json")):
        if k in p:
            return t
    return "other"


print("\nlow-confidence cross items, method x label")
c = collections.Counter((rows[i]["method"], lab[i]["label"]) for i in cross if lab[i]["confidence"] == "low")
for k, v in sorted(c.items()):
    print(f"  {k[0]} {k[1]}: {v}")
print("\nlow-confidence cross items, method x fastText half")
c = collections.Counter((rows[i]["method"], rows[i]["half"]) for i in cross if lab[i]["confidence"] == "low")
for k, v in sorted(c.items()):
    print(f"  {k[0]} {k[1]}: {v}")
print("\nlow-confidence cross items, method x prompt kind (prompt keyword)")
c = collections.Counter((rows[i]["method"], topic(i)) for i in cross if lab[i]["confidence"] == "low")
for k, v in sorted(c.items()):
    print(f"  {k[0]} {k[1]}: {v}")
print("\nall cross items, method x prompt kind: n / not full_lang / low")
c = collections.defaultdict(lambda: [0, 0, 0])
for i in cross:
    e = c[(rows[i]["method"], topic(i))]
    e[0] += 1; e[1] += lab[i]["label"] != "full_lang"; e[2] += lab[i]["confidence"] == "low"
for k, v in sorted(c.items()):
    print(f"  {k[0]} {k[1]}: {v[0]}/{v[1]}/{v[2]}")
for m in ("c06", "recover_a0.03"):
    print(f"\n{m}: mixed items (lang, half, conf, note)")
    for i in sorted(cross, key=lambda i: rows[i]["lang"]):
        if rows[i]["method"] == m and lab[i]["label"] == "mixed":
            print(f"  {rows[i]['lang']} {rows[i]['half']} {lab[i]['confidence']}: {lab[i]['notes']}")
