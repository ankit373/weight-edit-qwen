"""per-row loop flag (guard unit: distinct 4-gram ratio of the answer tokens below 0.5, guard.py
stats) and, optionally, whether the answer starts with an older row's answer. tokenizer only, no
model weights. run in envs/gen (through run_2b.py for the 2B tokenizer).

usage: loops_rows.py <rows.jsonl> <out.jsonl> [--prefix-of OLD.jsonl]
--prefix-of: starts_with_old = this row's output_raw starts with OLD's output_raw (same id)
(long400 vs the existing 100-token seed 1 row, PROTOCOL.md section 4).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G3 = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-run", "scripts"))
sys.path.insert(0, G3)
import guard  # noqa: E402  (LOOP_RATIO, load; also puts gate 3 g3common on the path)


def main():
    a = sys.argv[1:]
    old = None
    if "--prefix-of" in a:
        i = a.index("--prefix-of")
        old = guard.load(a[i + 1])
        del a[i:i + 2]
    rows_path, out_path = a
    rows = guard.load(rows_path)
    tok = guard.g3common.load_tokenizer()
    n_loop = n_pref = 0
    with open(out_path, "w") as f:
        for pid, r in rows.items():
            t = tok(r["completion"], add_special_tokens=False)["input_ids"]
            grams = [tuple(t[i:i + 4]) for i in range(len(t) - 3)]
            loop = int(bool(grams) and len(set(grams)) / len(grams) < guard.LOOP_RATIO)
            d = {"id": pid, "loop": loop}
            if old is not None:
                d["starts_with_old"] = int(pid in old and r["output_raw"].startswith(old[pid]["output_raw"]))
                n_pref += d["starts_with_old"]
            n_loop += loop
            f.write(json.dumps(d) + "\n")
    print(json.dumps({"rows": rows_path, "n": len(rows), "loop": n_loop,
                      "starts_with_old": n_pref if old is not None else None}))


if __name__ == "__main__":
    main()
