"""byte-identity check of two row files on an id list. stdlib only.

usage: same_rows.py <a.jsonl> <b.jsonl> <ids.txt> <out.json> [--hooks-zero A_HOOKS]
generation rows: output_raw and chat_text equal. logit rows (have logits_sha256): logits_sha256,
logits_abcd and chat_text equal. --hooks-zero: also every id has 0 decoder-layer forward hooks,
read from A_HOOKS (a partc_gen.py <out>.hooks.jsonl, last line per id) or, if that is "-", from the
rows' own layer_hooks field. uses: the 20-row determinism check (same rows twice) and the ReCoVeR
no-op check (ReCoVeR rows vs baseline rows, PROTOCOL.md section 1). exit 1 unless all ids match.
"""
import json
import sys


def load(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows[r["id"]] = r
    return rows


def key(r):
    if "logits_sha256" in r:
        return (r["logits_sha256"], tuple(r["logits_abcd"]), r["chat_text"])
    return (r["output_raw"], r["chat_text"])


def main():
    a = sys.argv[1:]
    hooks_src = None
    if "--hooks-zero" in a:
        i = a.index("--hooks-zero")
        hooks_src = a[i + 1]
        del a[i:i + 2]
    if len(a) != 4:
        sys.exit(__doc__)
    pa, pb, pids, out = a
    A, B = load(pa), load(pb)
    ids = [x.strip() for x in open(pids) if x.strip()]
    hooks = {}
    if hooks_src == "-":
        hooks = {i: A[i].get("layer_hooks") for i in ids if i in A}
    elif hooks_src:
        hooks = {r["id"]: r["n_layer_hooks"] for r in map(json.loads, open(hooks_src))}
    res = {"a": pa, "b": pb, "ids": pids, "n": len(ids), "missing_a": [i for i in ids if i not in A],
           "missing_b": [i for i in ids if i not in B], "differ": [], "hooks_nonzero": []}
    same = 0
    for i in ids:
        if i in A and i in B:
            if key(A[i]) == key(B[i]):
                same += 1
            else:
                res["differ"].append(i)
        if hooks_src and hooks.get(i) != 0:
            res["hooks_nonzero"].append([i, hooks.get(i)])
    res["identical"] = same
    res["hooks_checked"] = bool(hooks_src)
    res["ok"] = same == len(ids) and not res["hooks_nonzero"]
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("n", "identical", "ok")} | {"n_differ": len(res["differ"]),
                                                                       "n_hooks_nonzero": len(res["hooks_nonzero"])}))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
