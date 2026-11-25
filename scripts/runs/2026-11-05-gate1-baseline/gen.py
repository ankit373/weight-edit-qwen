"""generate LCB completions with qwen3.5-0.8b. see README for settings and sources."""
import argparse
import csv
import glob
import json
import os
import time

import torch
import transformers
from transformers import AutoTokenizer, Qwen3_5ForCausalLM

MODEL = "Qwen/Qwen3.5-0.8B"
REVISION = "2fc06364715b967f1860aea9cf38778875588b17"
ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_SETS = os.path.join(ROOT, "..", "..", "external", "lcb_test_sets", "test_sets")


def load_prompts():
    """all LCB prompts, id = task/source/lang/row."""
    rows = []
    for path in sorted(glob.glob(os.path.join(TEST_SETS, "*", "*", "*.csv"))):
        task, source_dir, fname = path.split(os.sep)[-3:]
        lang = fname.removesuffix(".csv")
        with open(path, newline="") as f:
            for i, r in enumerate(csv.DictReader(f)):
                assert r["language"] == lang, (path, i)
                rows.append({
                    "id": f"{task}/{source_dir}/{lang}/{i}",
                    "task": task,
                    "source": r["source"],
                    "language": lang,
                    "prompt": r["prompt"],
                })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True, help="file with one prompt id per line")
    ap.add_argument("--out", required=True)
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=100)
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--top-p", type=float, default=0.75)
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16")
    args = ap.parse_args()

    by_id = {r["id"]: r for r in load_prompts()}
    index_of = {pid: i for i, pid in enumerate(by_id)}
    ids = [l.strip() for l in open(args.ids) if l.strip()]
    done = set()
    if os.path.exists(args.out):  # resume: skip ids already written
        done = {json.loads(l)["id"] for l in open(args.out)}

    tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
    model = Qwen3_5ForCausalLM.from_pretrained(
        MODEL, revision=REVISION, trust_remote_code=False, use_safetensors=True,
        dtype=getattr(torch, args.dtype),
    ).to(args.device).eval()

    gen_kwargs = dict(
        do_sample=True, max_new_tokens=args.max_new_tokens,
        temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
        min_p=None, repetition_penalty=1.0,
        # repo has no generation_config.json, so the default eos is only <|endoftext|>.
        # chat turns end with <|im_end|> (tokenizer_config eos_token), so stop on both.
        eos_token_id=[tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")],
        pad_token_id=tok.convert_tokens_to_ids("<|endoftext|>"),
    )
    meta = {
        "transformers": transformers.__version__, "torch": torch.__version__,
        "device": args.device, "dtype": args.dtype, "thinking": args.thinking,
        "seed": args.seed, "gen_kwargs": gen_kwargs,
    }
    print(json.dumps(meta), flush=True)

    with open(args.out, "a") as fout:
        for n, pid in enumerate(ids):
            if pid in done:
                continue
            r = by_id[pid]
            text = tok.apply_chat_template(
                [{"role": "user", "content": r["prompt"]}],
                tokenize=False, add_generation_prompt=True,
                enable_thinking=args.thinking,
            )
            enc = tok(text, return_tensors="pt").to(args.device)
            # per-prompt seed: same output for a prompt regardless of order or resume
            torch.manual_seed(args.seed + index_of[pid])
            t0 = time.time()
            with torch.no_grad():
                out = model.generate(**enc, **gen_kwargs)
            if args.device == "mps":
                torch.mps.synchronize()
            dt = time.time() - t0
            new = out[0, enc["input_ids"].shape[1]:].tolist()
            eos = set(gen_kwargs["eos_token_id"])
            stopped_eos = any(t in eos for t in new)
            raw = tok.decode(new, skip_special_tokens=False)
            completion = tok.decode(new, skip_special_tokens=True)
            rec = {
                **r, "mode": "thinking" if args.thinking else "nonthinking",
                "chat_text": text, "output_raw": raw, "completion": completion,
                "n_prompt_tokens": enc["input_ids"].shape[1], "n_new_tokens": len(new),
                "stopped_eos": stopped_eos,
                "hit_max_tokens": (not stopped_eos) and len(new) >= args.max_new_tokens,
                "time_s": round(dt, 3),
            }
            if args.thinking:
                if "</think>" in completion:
                    think, answer = completion.split("</think>", 1)
                    rec["thinking_text"] = think.replace("<think>", "").strip()
                    rec["answer"] = answer.strip()
                    rec["think_closed"] = True
                else:
                    rec["thinking_text"] = completion.replace("<think>", "").strip()
                    rec["answer"] = ""
                    rec["think_closed"] = False
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"{n+1}/{len(ids)} {pid} {len(new)} tok {dt:.2f}s", flush=True)


if __name__ == "__main__":
    main()
