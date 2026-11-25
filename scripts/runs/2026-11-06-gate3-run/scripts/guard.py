"""unreadable-text guard (PROTOCOL.md "decisions before gate 3"). units and NLL setup are ours
(README "fixed before any result").

usage:
  guard.py nll <rows.jsonl> <gate1_rows.jsonl> <out_nll.jsonl> [--ids IDS]      (gpu, resumes)
  guard.py summary <rows.jsonl> <rows_nll.jsonl> <gate1_rows.jsonl> <gate1_nll.jsonl> <ids> <out.json>

nll: unedited base model, no hook. context = gate 1 chat_text of the same id (the original
prompt); answer = output_raw of the row, re-tokenized without special-token insertion.
value = mean -log p over the answer tokens. empty answers get no value.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts")))
import g3common  # noqa: E402

LOOP_RATIO = 0.5  # protocol: distinct 4-gram ratio below 0.5
LIMITS = {"empty_pts": 1.0, "loop_pts": 2.0, "nll_nats": 1.0}  # protocol thresholds


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path))}


def nll_main(rows_path, base_path, out_path, ids_path=None):
    import torch
    rows, base = load(rows_path), load(base_path)
    ids = g3common.read_ids(ids_path) if ids_path else list(rows)
    done = set(load(out_path)) if os.path.exists(out_path) else set()
    tok = g3common.load_tokenizer()
    model = g3common.load_model("mps", "bfloat16")
    with open(out_path, "a") as f:
        for pid in ids:
            if pid in done:
                continue
            r = rows[pid]
            if not r["completion"].strip():
                f.write(json.dumps({"id": pid, "nll": None, "n_tok": 0}) + "\n")
                continue
            ctx = tok(base[pid]["chat_text"], return_tensors="pt")["input_ids"]
            ans = tok(r["output_raw"], add_special_tokens=False, return_tensors="pt")["input_ids"]
            ids_t = torch.cat([ctx, ans], dim=1).to("mps")
            n = ans.shape[1]
            with torch.no_grad():
                logits = model(input_ids=ids_t, logits_to_keep=n + 1).logits[0, :n].float()
            lp = torch.log_softmax(logits, dim=-1)
            tgt = ans[0].to("mps")
            nll = -lp.gather(1, tgt[:, None]).mean().item()
            f.write(json.dumps({"id": pid, "nll": nll, "n_tok": n}) + "\n")
            f.flush()


def stats(rows, nll, ids, tok):
    empty = loop = 0
    vals = []
    for pid in ids:
        r = rows[pid]
        if not r["completion"].strip():
            empty += 1
        t = tok(r["completion"], add_special_tokens=False)["input_ids"]
        grams = [tuple(t[i:i + 4]) for i in range(len(t) - 3)]
        if grams and len(set(grams)) / len(grams) < LOOP_RATIO:
            loop += 1
        if nll.get(pid, {}).get("nll") is not None:
            vals.append(nll[pid]["nll"])
    n = len(ids)
    return {"n": n, "empty_pct": 100 * empty / n, "loop_pct": 100 * loop / n,
            "nll_mean": sum(vals) / len(vals) if vals else None, "n_nll": len(vals)}


def summary_main(rows_path, rows_nll, base_path, base_nll, ids_path, out_path):
    tok = g3common.load_tokenizer()
    ids = g3common.read_ids(ids_path)
    new = stats(load(rows_path), load(rows_nll), ids, tok)
    old = stats(load(base_path), load(base_nll), ids, tok)
    assert new["n_nll"] + round(new["empty_pct"] * new["n"] / 100) == new["n"], "nll missing for some ids"
    d = {"empty_pts": new["empty_pct"] - old["empty_pct"], "loop_pts": new["loop_pct"] - old["loop_pct"],
         "nll_nats": new["nll_mean"] - old["nll_mean"]}
    fails = [k for k, v in d.items() if v > LIMITS[k]]
    res = {"rows": rows_path, "ids": ids_path, "new": new, "baseline": old, "delta": d,
           "limits": LIMITS, "failed_checks": fails, "pass_1_to_3": not fails}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    if sys.argv[1] == "nll":
        a = sys.argv[2:]
        ids = a[a.index("--ids") + 1] if "--ids" in a else None
        nll_main(a[0], a[1], a[2], ids)
    else:
        summary_main(*sys.argv[2:8])
