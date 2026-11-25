"""gate 3 generation: gate 1's loop (gen.py:81-125) plus one method. output rows have the
same fields as gate 1, so gate 1 score.py scores them unchanged.

usage:
  generate.py --ids IDS --out OUT.jsonl --method none
  generate.py ... --method recover --vectors V.safetensors --alpha A [--restore-norm]
              [--mono-mode none|steer] [--last-layer postnorm|prenorm]
  generate.py ... --method nie --neurons NEURONS.json --top-n N
  --greedy        greedy decoding (Nie selection pass); default = gate 1 sampling
  --save-tokens   also save new token ids and per-token strings (input to nie_label_cp.py)
"""
import argparse
import json
import os
import sys
import time

import torch
import transformers

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts run with python -I
import g3common  # noqa: E402
import nie  # noqa: E402
import recover  # noqa: E402

SOURCE_LANG = "en"  # LCB cross prompts are english; recover/predict_lcb.py:93 anchor "eng"


class Recover:
    def __init__(self, model, args):
        vectors = recover.load_vectors(args.vectors, args.last_layer)
        self.r = recover.content_removed(vectors)
        self.steer = recover.Steerer(model, args.alpha, args.restore_norm)
        self.mono_mode = args.mono_mode
        self.beta = args.beta

    def before(self, row):
        tgt = g3common.LCB_TO_FLORES[row["language"]]
        if row["task"] == "crosslingual":
            src = g3common.LCB_TO_FLORES[SOURCE_LANG]
            self.steer.set(recover.steering_dirs(self.r, tgt, src, self.beta))  # eq. 3
        elif self.mono_mode == "steer":
            self.steer.set(recover.steering_dirs(self.r, tgt))  # eq. 2
        else:
            self.steer.clear()

    def after(self, row):
        self.steer.clear()


class Nie:
    """one neuron set per target language, applied while that language's prompts run."""

    def __init__(self, model, args):
        with open(args.neurons) as f:
            self.ranked = json.load(f)["by_language"]
        self.model, self.top_n = model, args.top_n
        self.active, self.saved, self.edits = None, None, {}

    def before(self, row):
        lang = row["language"]
        if lang == self.active:
            return
        self.restore()
        if lang in self.ranked:
            neurons = nie.select_score(self.ranked[lang], self.top_n)
            self.saved, self.edits[lang] = nie.zero_columns(self.model, neurons)
            self.active = lang

    def after(self, row):
        pass

    def restore(self):
        """put the base columns back and check the tensors hash to the base again."""
        if self.saved is not None:
            nie.restore_columns(self.model, self.saved)
            for rec in self.edits[self.active]:
                w = self.model.model.layers[rec["layer"]].mlp.down_proj.weight
                assert g3common.tensor_sha256(w) == rec["base_sha256"], rec["layer"]
        self.saved, self.active = None, None


class NoMethod:
    def before(self, row):
        pass

    def after(self, row):
        pass


def build_method(model, args):
    if args.method == "recover":
        return Recover(model, args)
    if args.method == "nie":
        return Nie(model, args)
    return NoMethod()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", choices=["none", "recover", "nie"], required=True)
    ap.add_argument("--greedy", action="store_true")
    ap.add_argument("--save-tokens", action="store_true")
    ap.add_argument("--seed", type=int, default=1234)  # gen.py:47
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--vectors")
    ap.add_argument("--alpha", type=float)
    ap.add_argument("--beta", type=float, default=1.0)  # predict_lcb.py:49
    ap.add_argument("--restore-norm", action="store_true")
    ap.add_argument("--mono-mode", choices=["none", "steer"], default="none")
    ap.add_argument("--last-layer", choices=["postnorm", "prenorm"], default="postnorm")
    ap.add_argument("--neurons")
    ap.add_argument("--top-n", type=int, default=100)  # paper sec 5.1, p.7
    args = ap.parse_args()

    by_id = {r["id"]: r for r in g3common.load_prompts()}
    index_of = {pid: i for i, pid in enumerate(by_id)}
    ids = g3common.read_ids(args.ids)
    # nie swaps weights per language: run grouped by language, keep order inside a group
    if args.method == "nie":
        ids = sorted(ids, key=lambda pid: by_id[pid]["language"])
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(line)["id"] for line in f}

    tok = g3common.load_tokenizer()
    model = g3common.load_model(args.device, args.dtype)
    method = build_method(model, args)
    kw = g3common.gen_kwargs(tok, args.greedy)
    meta = {"transformers": transformers.__version__, "torch": torch.__version__,
            "ids_file": args.ids, "ids_sha256": g3common.file_sha256(args.ids),
            "args": vars(args), "gen_kwargs": kw}
    print(json.dumps(meta), flush=True)
    stop = set(kw["eos_token_id"])

    with open(args.out, "a") as fout:
        for n, pid in enumerate(ids):
            if pid in done:
                continue
            row = by_id[pid]
            text = g3common.chat_text(tok, row["prompt"])
            enc = tok(text, return_tensors="pt").to(args.device)
            torch.manual_seed(args.seed + index_of[pid])  # gen.py:93
            method.before(row)
            t0 = time.time()
            with torch.no_grad():
                out = model.generate(**enc, **kw)
            if args.device == "mps":
                torch.mps.synchronize()
            dt = time.time() - t0
            method.after(row)
            new = out[0, enc["input_ids"].shape[1]:].tolist()
            stopped = any(t in stop for t in new)
            rec = {**row, "mode": "nonthinking", "method": args.method, "chat_text": text,
                   "output_raw": tok.decode(new, skip_special_tokens=False),
                   "completion": tok.decode(new, skip_special_tokens=True),
                   "n_prompt_tokens": enc["input_ids"].shape[1], "n_new_tokens": len(new),
                   "stopped_eos": stopped,
                   "hit_max_tokens": (not stopped) and len(new) >= kw["max_new_tokens"],
                   "time_s": round(dt, 3)}
            if args.save_tokens:
                rec["prompt_ids"] = enc["input_ids"][0].tolist()
                rec["new_ids"] = new
                rec["new_tokens"] = [tok.decode(t).strip() for t in new]  # generate_cp.py:54
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"{n+1}/{len(ids)} {pid} {len(new)} tok {dt:.2f}s", flush=True)

    if args.method == "nie":
        method.restore()
        write_edits(args, method.edits)


def write_edits(args, edits):
    """diff record per language (protocol: sha256 of base and edited tensors). merges on resume."""
    path = args.out + ".edits.json"
    rec = {"top_n": args.top_n, "neurons_file": args.neurons,
           "neurons_sha256": g3common.file_sha256(args.neurons), "by_language": {}}
    if os.path.exists(path):
        with open(path) as f:
            rec["by_language"] = json.load(f)["by_language"]
    rec["by_language"].update(edits)
    with open(path, "w") as f:
        json.dump(rec, f, indent=1)


if __name__ == "__main__":
    main()
