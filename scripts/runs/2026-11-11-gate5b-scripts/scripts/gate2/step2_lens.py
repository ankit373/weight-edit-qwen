"""step 2b: teacher-force gate 1 responses on dev prompts, logit lens over the 24 layers.

usage: step2_lens.py --ids <dev ids> --gate1 <gate1 jsonl> --beh <step1 jsonl> --labels <dir> --out <jsonl>
input = gate 1 chat_text (same template, same tokenizer call as gen.py) + gate 1 output_raw tokens.
no sampling. hidden_states[l] for l=1..23 is the residual after layer l: final norm + tied lm_head
applied. hidden_states[24] is already the final-normed state in transformers 5.22.1
(utils/output_capturing.py, tie_last_hidden_states), so layer 24 uses lm_head only (checked vs logits).
"""
import argparse
import json
import os
import time

import numpy as np
import torch
from transformers import (AutoTokenizer, Qwen3_5ForCausalLM, TemperatureLogitsWarper,
                          TopKLogitsWarper, TopPLogitsWarper)

MODEL, REVISION = "Qwen/Qwen3.5-2B", "15852e8c16360a2fea060d615a32b45270f8a8fc"  # part B: 2B pin
NONLATIN_SCRIPT = {"ar": ["arabic"], "hi": ["devanagari"], "ru": ["cyrillic"], "ko": ["hangul"],
                   "zh": ["han"], "ja": ["kana", "han"]}
N_FIRST = 8  # lens at the positions that predict answer tokens 0..7
WARPERS = [TemperatureLogitsWarper(0.3), TopKLogitsWarper(20), TopPLogitsWarper(0.75)]  # gate 1 order


def r4(x):
    return [round(float(v), 4) for v in x]


def main():
    ap = argparse.ArgumentParser()
    for a in ("ids", "gate1", "beh", "labels", "out"):
        ap.add_argument("--" + a, required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--device", default="mps")
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
    model = Qwen3_5ForCausalLM.from_pretrained(
        MODEL, revision=REVISION, trust_remote_code=False, use_safetensors=True, dtype=torch.bfloat16,
    ).to(args.device).eval()
    assert model.config.num_hidden_layers == 24, "range(1, 25) below assumes 24 layers"  # part B guard
    lm_w = model.lm_head.weight
    tied = lm_w.data_ptr() == model.model.embed_tokens.weight.data_ptr()
    W = lm_w.float()  # [Vmodel, d], fp32 copy for the lens
    Vm = W.shape[0]
    norm = model.model.norm

    meta = json.load(open(os.path.join(args.labels, "token_labels.json")))
    script = np.load(os.path.join(args.labels, "script.npy"))
    x_set = np.load(os.path.join(args.labels, "x_set.npy"))
    en_set = np.load(os.path.join(args.labels, "en_set.npy"))
    S, L = meta["scripts"], meta["langs"]
    pad = Vm - len(script)  # model vocab is padded past the tokenizer vocab; padded ids get no label

    def col(mask):
        m = np.concatenate([mask, np.zeros(pad, dtype=bool)])
        return torch.tensor(m, dtype=torch.float32)

    cols = {}
    for j, X in enumerate(L):
        tscript = np.isin(script, [S.index(s) for s in NONLATIN_SCRIPT.get(X, ["latin"])])
        latin = script == S.index("latin")
        cols[X] = torch.stack([col(tscript), col(latin), col(x_set[j]), col(en_set[j])], 1).to(args.device)
    COLS = ["tscript", "latin", "xset", "enset"]
    content_ids = set(np.where(~np.isin(script, [S.index("none"), S.index("partial")]))[0].tolist())

    beh = {}
    for l in open(args.beh):
        r = json.loads(l)
        beh[r["id"]] = r
    g1 = {}
    for l in open(args.gate1):
        r = json.loads(l)
        g1[r["id"]] = r
    ids = [l.strip() for l in open(args.ids) if l.strip()]
    if args.limit:
        ids = ids[: args.limit]
    done = set()
    if os.path.exists(args.out):
        done = {json.loads(l)["id"] for l in open(args.out)}
    print(json.dumps({"tied_unembedding": tied, "vocab_model": Vm, "vocab_tok": len(script), "n_ids": len(ids),
                      "already_done": len(done)}), flush=True)

    with open(args.out, "a") as fout:
        for n, pid in enumerate(ids):
            if pid in done:
                continue
            t0 = time.time()
            r, b = g1[pid], beh[pid]
            X = r["language"]
            p_ids = tok(r["chat_text"], return_tensors="pt")["input_ids"][0]  # same call as gen.py
            enc_a = tok(r["output_raw"], add_special_tokens=False, return_offsets_mapping=True)
            a_ids = torch.tensor(enc_a["input_ids"])
            P, A = len(p_ids), len(a_ids)
            ids_t = torch.cat([p_ids, a_ids]).unsqueeze(0).to(args.device)
            with torch.no_grad():
                out = model(input_ids=ids_t, output_hidden_states=True, use_cache=False, logits_to_keep=A + 1)
            hs = out.hidden_states
            logits = out.logits[0].float()  # positions P-1 .. P+A-1
            # answer-token positions to look at
            k_content = next((k for k, t in enumerate(a_ids.tolist()) if t in content_ids), None)
            k_bad = None
            if b["fail"] and b["first_bad_char"] is not None:
                c = b["first_bad_char"]
                k_bad = next((k for k, (s, e) in enumerate(enc_a["offset_mapping"]) if e > c), None)
            ks = {f"k{k}": k for k in range(min(N_FIRST, A))}
            if k_content is not None:
                ks["content"] = k_content
            if k_bad:
                ks["bad"] = k_bad
            names = list(ks)
            pos = torch.tensor([P - 1 + ks[nm] for nm in names], device=args.device)
            lens = {nm: {c: [] for c in COLS + ["top1"]} for nm in names}
            with torch.no_grad():
                for layer in range(1, 25):
                    h = hs[layer][0, pos].float()
                    z = (h if layer == 24 else norm(h)) @ W.T
                    pr = torch.softmax(z, -1)
                    m = (pr @ cols[X]).cpu().numpy()
                    t1 = z.argmax(-1).tolist()
                    for i, nm in enumerate(names):
                        for ci, c in enumerate(COLS):
                            lens[nm][c].append(round(float(m[i, ci]), 4))
                        lens[nm]["top1"].append(t1[i])
                    if layer == 24:
                        lens_check = float((z - logits[[ks[nm] for nm in names]]).abs().max())
                        # what layer 24 would give if the final norm were applied a second time
                        dbl_check = float((norm(h) @ W.T - logits[[ks[nm] for nm in names]]).abs().max())
                # consistency of teacher forcing with gate 1 sampling
                gen = a_ids.to(args.device)
                lp = torch.log_softmax(logits[:A], -1).gather(1, gen[:, None])[:, 0]
                warped = logits[:A].clone()
                for w in WARPERS:
                    warped = w(None, warped)
                in_support = torch.isfinite(warped.gather(1, gen[:, None]))[:, 0]
                # first-token decisions at k0 and at the first content token
                decisions = {}
                for nm in ("k0", "content"):
                    if nm not in ks:
                        continue
                    k = ks[nm]
                    pr = torch.softmax(logits[k], -1)
                    tgt = cols[X][:, 2 if X not in NONLATIN_SCRIPT else 0]
                    eng = cols[X][:, 3 if X not in NONLATIN_SCRIPT else 1]
                    best_t = int(torch.argmax(pr * tgt))
                    best_e = int(torch.argmax(pr * eng))
                    sp = torch.softmax(warped[k], -1)
                    rank_t = int((pr > pr[best_t]).sum())
                    decisions[nm] = {
                        "k": k, "gen_id": int(a_ids[k]), "gen_tok": tok.decode([int(a_ids[k])]),
                        "gen_script": S[int(script[a_ids[k]])] if int(a_ids[k]) < len(script) else "pad",
                        "gen_in_xset": bool(int(a_ids[k]) < len(script) and x_set[L.index(X), a_ids[k]]),
                        "gen_in_enset": bool(int(a_ids[k]) < len(script) and en_set[L.index(X), a_ids[k]]),
                        "p_gen": round(float(pr[a_ids[k]]), 4),
                        "top1_tok": tok.decode([int(pr.argmax())]), "p_top1": round(float(pr.max()), 4),
                        "best_target_tok": tok.decode([best_t]), "p_best_target": round(float(pr[best_t]), 5),
                        "rank_best_target": rank_t,
                        "best_eng_tok": tok.decode([best_e]), "p_best_eng": round(float(pr[best_e]), 5),
                        "mass_target": round(float(pr @ tgt), 4), "mass_eng": round(float(pr @ eng), 4),
                        "samp_mass_target": round(float(sp @ tgt), 4), "samp_mass_eng": round(float(sp @ eng), 4),
                        "samp_support": int(torch.isfinite(warped[k]).sum()),
                    }
            if args.device == "mps":
                torch.mps.synchronize()
            rec = {
                "id": pid, "source": r["source"], "language": X, "fail": b["fail"], "scored": b["scored"],
                "kind": b["kind"], "whole_label": b["whole_label"], "P": P, "A": A,
                "P_matches_gate1": P == r["n_prompt_tokens"], "A_matches_gate1": A == r["n_new_tokens"],
                "positions": ks, "lens": lens, "decisions": decisions,
                "gen_logprob_mean": round(float(lp.mean()), 4),
                "gen_in_sampling_support": round(float(in_support.float().mean()), 4),
                "lens24_vs_logits_maxabs": lens_check, "lens24_doublenorm_vs_logits_maxabs": dbl_check,
                "time_s": round(time.time() - t0, 3),
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"{n+1}/{len(ids)} {pid} P={P} A={A} {rec['time_s']}s", flush=True)


if __name__ == "__main__":
    main()
