"""collect ReCoVeR language vectors from FLORES-200 dev (plain text, one sentence per line).

usage: recover_collect.py --flores-dir DIR --langs eng_Latn,deu_Latn,... --out vectors.safetensors
       [--device mps] [--dtype bfloat16] [--limit N]
output: safetensors with "<lang>" (L+1, d) and "<lang>.last_prenorm" (d,), float32,
plus a .json sidecar with counts, file hashes and timing.
"""
import argparse
import json
import os
import sys
import time

import torch
from safetensors.torch import save_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts run with python -I
import g3common  # noqa: E402
import recover  # noqa: E402

MAX_LEN = 512  # collect.py:149 default max_seq_length, truncation=True (:85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flores-dir", required=True)
    ap.add_argument("--langs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16")  # collect.py:70
    ap.add_argument("--limit", type=int, default=None, help="first N sentences only (timing)")
    args = ap.parse_args()

    tok = g3common.load_tokenizer()
    model = g3common.load_model(args.device, args.dtype)
    tensors, meta = {}, {"model_revision": g3common.REVISION, "langs": {}, "max_len": MAX_LEN}
    for lang in args.langs.split(","):
        path = os.path.join(args.flores_dir, f"{lang}.dev")
        with open(path, encoding="utf-8") as f:
            sentences = f.read().splitlines()[: args.limit]
        t0 = time.time()
        per_sent, pre_sent, skipped, truncated = [], [], 0, 0
        for s in sentences:
            ids = tok(s, truncation=True, max_length=MAX_LEN)["input_ids"]
            truncated += len(ids) == MAX_LEN
            v, pre = recover.sentence_states(model, torch.tensor([ids], device=args.device))
            if v is None:
                skipped += 1
                continue
            per_sent.append(v)
            pre_sent.append(pre)
        tensors[lang] = recover.mean_vectors(per_sent).contiguous()
        tensors[f"{lang}.last_prenorm"] = recover.mean_vectors(pre_sent).contiguous()
        meta["langs"][lang] = {
            "file": path, "sha256": g3common.file_sha256(path), "n_sentences": len(sentences),
            "n_used": len(per_sent), "n_skipped_too_short": skipped, "n_truncated": truncated,
            "seconds": round(time.time() - t0, 2),
        }
        print(json.dumps({lang: meta["langs"][lang]}), flush=True)
    save_file(tensors, args.out)
    meta["out_sha256"] = g3common.file_sha256(args.out)
    with open(args.out + ".json", "w") as f:
        json.dump(meta, f, indent=1)


if __name__ == "__main__":
    main()
