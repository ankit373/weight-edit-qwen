"""score FFN neurons at confusion points and rank them per target language (Nie et al. 2025).

usage: nie_find_neurons.py <cp.jsonl> <out_neurons.json> [--device mps] [--dtype float32]
       [--top-k 300] [--chunk 512] [--limit N]
pools all sources per language (deviation: their code runs per task/source/language,
find_neurons.py:141-149; dev has 6-21 full errors per language in gate 1's sampled outputs).
dtype float32 by default: their from_pretrained sets no dtype (find_neurons.py:136).
"""
import argparse
import collections
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts run with python -I
import g3common  # noqa: E402
import nie  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--top-k", type=int, default=300)  # find_neurons.py:205; paper p.6
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None, help="first N rows only (timing)")
    args = ap.parse_args()

    with open(args.inp) as f:
        rows = [json.loads(line) for line in f][: args.limit]
    model = g3common.load_model(args.device, args.dtype)
    emb = nie.unembedding(model)
    groups = collections.defaultdict(list)
    log = []
    for r in rows:
        t0 = time.time()
        ids = torch.tensor([r["cp_ids"]], device=args.device)
        target, tops = nie.prompt_top_neurons(model, emb, ids, args.top_k, args.chunk)
        groups[r["language"]].append(tops)
        log.append({"id": r["id"], "target": target, "cp_token_id": r.get("cp_token_id"),
                    "target_is_cp_token": target == r.get("cp_token_id"),
                    "seconds": round(time.time() - t0, 2)})
        print(json.dumps(log[-1]), flush=True)
    result = {
        "inp": args.inp, "inp_sha256": g3common.file_sha256(args.inp),
        "model_revision": g3common.REVISION, "args": vars(args),
        "n_prompts": {k: len(v) for k, v in groups.items()},
        "by_language": {k: nie.aggregate(v) for k, v in sorted(groups.items())},
        "per_prompt": log,
    }
    with open(args.out, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
