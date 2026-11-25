"""mmlu-redux generation for the side check. model load, stop tokens and greedy kwargs from
gate 3 g3common.py; method classes Recover / Nie from gate 3 generate.py (imported, unchanged).

usage:
  mmlu_gen.py --items ITEMS --ids IDS --out OUT.jsonl --method none
  ... --method p50c --ckpt DIR --manifest MANIFEST
  ... --method recover --vectors V --alpha A [--restore-norm]
  ... --method nie --neurons N.json --top-n N [--force-lang-cycle]
"""
import argparse
import json
import os
import sys
import time

import torch
import transformers

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts"))
sys.path.insert(0, S)
import g3common  # noqa: E402
import generate  # noqa: E402

# the 14 Nie neuron sets (gate 3 nie/neurons_alldev.json by_language keys)
LANGS14 = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]


def chat_text(tok, item):
    # lm-eval chat path: description as system turn, doc as user turn (task.py:974-979, 1032-1036).
    # non-thinking as in gate 1 / g3common.chat_text
    msgs = [{"role": "system", "content": item["description"]},
            {"role": "user", "content": item["prompt"]}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                   enable_thinking=False)


def load_p50c(ckpt, manifest, device, dtype):
    """local checkpoint + tensor hash check, same rule as mit-p50c scripts/gen_p50c.py:30-49."""
    from transformers import Qwen3_5ForCausalLM
    model = Qwen3_5ForCausalLM.from_pretrained(
        ckpt, trust_remote_code=False, use_safetensors=True, local_files_only=True,
        dtype=getattr(torch, dtype))
    out = []
    with open(manifest) as f:
        tensors = json.load(f)["tensors"]
    for t in tensors:
        assert t["name"].endswith("mlp.down_proj.weight"), t["name"]
        layer = int(t["name"].split(".")[3])
        got = g3common.tensor_sha256(model.model.layers[layer].mlp.down_proj.weight)
        out.append({"name": t["name"], "sha256": got, "ok": got == t["edited_sha256"]})
    print(json.dumps({"ckpt": ckpt, "loaded_tensor_check": out}), flush=True)
    if not all(r["ok"] for r in out):
        sys.exit("loaded weights do not match edited_sha256")
    return model.to(device).eval()


def n_layer_hooks(model):
    return sum(len(layer._forward_hooks) for layer in model.model.layers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", choices=["none", "p50c", "recover", "nie"], required=True)
    ap.add_argument("--max-new-tokens", type=int, default=256)  # lm-eval huggingface.py:628-629
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--ckpt")
    ap.add_argument("--manifest")
    ap.add_argument("--vectors")
    ap.add_argument("--alpha", type=float)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--restore-norm", action="store_true")
    ap.add_argument("--mono-mode", choices=["none", "steer"], default="none")
    ap.add_argument("--last-layer", choices=["postnorm", "prenorm"], default="postnorm")
    ap.add_argument("--neurons")
    ap.add_argument("--top-n", type=int, default=100)
    ap.add_argument("--force-lang-cycle", action="store_true",
                    help="nie only (ours): item k of the ids file gets LANGS14[k %% 14]")
    args = ap.parse_args()

    with open(args.items) as f:
        items = [json.loads(line) for line in f]
    by_id = {it["id"]: it for it in items}
    index_of = {it["id"]: i for i, it in enumerate(items)}
    ids = g3common.read_ids(args.ids)
    lang = {pid: "en" for pid in ids}  # mmlu-redux is english
    if args.force_lang_cycle:
        assert args.method == "nie"
        lang = {pid: LANGS14[k % len(LANGS14)] for k, pid in enumerate(ids)}
    if args.method == "nie":  # nie swaps weights per language: group by language (generate.py:123-124)
        ids = sorted(ids, key=lambda pid: lang[pid])
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(line)["id"] for line in f}

    tok = g3common.load_tokenizer()
    if args.method == "p50c":
        model = load_p50c(args.ckpt, args.manifest, args.device, args.dtype)
    else:
        model = g3common.load_model(args.device, args.dtype)
    method = generate.build_method(model, args) if args.method in ("recover", "nie") \
        else generate.NoMethod()
    kw = g3common.gen_kwargs(tok, greedy=True, max_new_tokens=args.max_new_tokens)
    meta = {"transformers": transformers.__version__, "torch": torch.__version__,
            "items_sha256": g3common.file_sha256(args.items),
            "ids_file": args.ids, "ids_sha256": g3common.file_sha256(args.ids),
            "args": vars(args), "gen_kwargs": kw}
    print(json.dumps(meta), flush=True)
    stop = set(kw["eos_token_id"])

    with open(args.out, "a") as fout:
        for n, pid in enumerate(ids):
            if pid in done:
                continue
            it = by_id[pid]
            row = {"task": "mmlu", "language": lang[pid]}
            text = chat_text(tok, it)
            enc = tok(text, return_tensors="pt").to(args.device)
            torch.manual_seed(args.seed + index_of[pid])  # greedy: no effect, kept as in gate 1
            method.before(row)
            hooks = n_layer_hooks(model)
            nie_active = getattr(method, "active", None)
            t0 = time.time()
            with torch.no_grad():
                out = model.generate(**enc, **kw)
            if args.device == "mps":
                torch.mps.synchronize()
            dt = time.time() - t0
            method.after(row)
            new = out[0, enc["input_ids"].shape[1]:].tolist()
            stopped = any(t in stop for t in new)
            rec = {"id": pid, "subject": it["subject"], "group": it["group"],
                   "target": it["target"], "method": args.method, "language": lang[pid],
                   "layer_hooks": hooks, "nie_active": nie_active, "chat_text": text,
                   "output_raw": tok.decode(new, skip_special_tokens=False),
                   "completion": tok.decode(new, skip_special_tokens=True),
                   "n_prompt_tokens": enc["input_ids"].shape[1], "n_new_tokens": len(new),
                   "stopped_eos": stopped,
                   "hit_max_tokens": (not stopped) and len(new) >= kw["max_new_tokens"],
                   "time_s": round(dt, 3)}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"{n+1}/{len(ids)} {pid} {len(new)} tok {dt:.2f}s", flush=True)

    if args.method == "nie":
        method.restore()
        generate.write_edits(args, method.edits)


if __name__ == "__main__":
    main()
