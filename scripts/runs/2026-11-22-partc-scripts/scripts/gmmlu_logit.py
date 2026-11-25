"""Global-MMLU logit scoring (PROTOCOL.md section 3). one forward pass per item, no decoding.

usage (through partc_gen.py --entry gmmlu, which adds --diff / run_2b / mocks):
  gmmlu_logit.py --items ITEMS --ids IDS --out OUT.jsonl --method none|recover [recover args]
chat text: mmlu-redux mmlu_gen.chat_text (description as system turn, prompt as user turn,
generation prompt, non-thinking), imported unchanged. methods: gate 3 generate.build_method.
at the first assistant position the logits of the tokens A, B, C, D are compared; argmax = answer.
each letter must be one token, else the run stops before any item. saved per item: the four
logits, the answer, the softmax mass on the four letters, sha256 of the full last-position logit
vector (float32), and the forward hooks on the decoder layers. resumes by id.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import torch
import transformers

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.abspath(os.path.join(HERE, "..", ".."))
S = os.path.join(RUNS, "2026-11-06-gate3-scripts", "scripts")
MM = os.path.join(RUNS, "2026-11-08-side-mmlu-redux", "scripts")
sys.path.insert(0, S)
sys.path.insert(1, MM)
import g3common  # noqa: E402
import generate  # noqa: E402
import mmlu_gen  # noqa: E402

LETTERS = ["A", "B", "C", "D"]


def letter_ids(tok):
    ids = {}
    for L in LETTERS:
        t = tok.encode(L, add_special_tokens=False)
        if len(t) != 1:
            sys.exit(f"gmmlu_logit: letter {L} is {len(t)} tokens {t}. stop.")
        ids[L] = t[0]
    if len(set(ids.values())) != 4:
        sys.exit(f"gmmlu_logit: letter ids not distinct {ids}")
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", choices=["none", "recover"], required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--vectors")
    ap.add_argument("--alpha", type=float)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--restore-norm", action="store_true")
    ap.add_argument("--mono-mode", choices=["none"], default="none")
    ap.add_argument("--last-layer", choices=["postnorm", "prenorm"], default="postnorm")
    args = ap.parse_args()

    with open(args.items, encoding="utf-8") as f:
        items = [json.loads(line) for line in f]
    by_id = {it["id"]: it for it in items}
    ids = g3common.read_ids(args.ids)
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(line)["id"] for line in f}

    tok = g3common.load_tokenizer()
    lid = letter_ids(tok)
    model = g3common.load_model(args.device, args.dtype)
    method = generate.build_method(model, args) if args.method == "recover" else generate.NoMethod()
    meta = {"transformers": transformers.__version__, "torch": torch.__version__,
            "items_sha256": g3common.file_sha256(args.items), "ids_file": args.ids,
            "ids_sha256": g3common.file_sha256(args.ids), "letter_ids": lid, "args": vars(args)}
    print(json.dumps(meta), flush=True)
    col = torch.tensor([lid[L] for L in LETTERS])

    with open(args.out, "a") as fout:
        for n, pid in enumerate(ids):
            if pid in done:
                continue
            it = by_id[pid]
            text = mmlu_gen.chat_text(tok, it)
            enc = tok(text, return_tensors="pt").to(args.device)
            method.before(it)  # task "monolingual": ReCoVeR clears its hooks (generate.py:37-45)
            hooks = mmlu_gen.n_layer_hooks(model)
            t0 = time.time()
            with torch.no_grad():
                logits = model(**enc, logits_to_keep=1).logits[0, -1].float().cpu()
            if args.device == "mps":
                torch.mps.synchronize()
            dt = time.time() - t0
            method.after(it)
            four = logits[col]
            pred = LETTERS[int(torch.argmax(four))]
            mass = float(torch.softmax(logits, dim=-1)[col].sum())
            rec = {"id": pid, "task": it["task"], "source": it["source"], "language": it["language"],
                   "sample_id": it["sample_id"], "subject": it["subject"], "group": it["group"],
                   "cultural_sensitivity_label": it["cultural_sensitivity_label"],
                   "target": it["target"], "method": args.method, "layer_hooks": hooks,
                   "chat_text": text, "logits_abcd": [float(x) for x in four], "pred": pred,
                   "correct": pred == it["target"], "mass_abcd": mass,
                   "logits_sha256": hashlib.sha256(logits.numpy().tobytes()).hexdigest(),
                   "n_prompt_tokens": enc["input_ids"].shape[1], "time_s": round(dt, 3)}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"{n+1}/{len(ids)} {pid} 1 tok {dt:.2f}s", flush=True)


if __name__ == "__main__":
    main()
