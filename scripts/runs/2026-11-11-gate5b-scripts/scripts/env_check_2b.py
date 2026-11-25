"""B1 step 1 load check for the 2B, light version (one bf16 load). based on gate 1 env_check.py.

usage: env_check_2b.py [--mock DIR]
one load: Qwen3_5ForCausalLM, bf16, as g3common.load_model (the pipeline's model). checks:
versions, mps, chat template + special tokens (as gate 1), missing / unexpected keys, widths and
param count vs the setup numbers, weights file sha256, and every loaded tensor equal to its
checkpoint tensor (safetensors, read one at a time and freed; checkpoint key
model.language_model.<x> -> model.<x>, lm_head must be tied to the embedding). then the model
moves to mps and one forward pass on the template prompt logs the top-5 last-token ids.
dropped vs gate 1 (would need a 2nd full model): logits vs the full ConditionalGeneration model,
and mps bf16 vs cpu fp32 logits. the per-tensor equality covers "same weights as the checkpoint".
--mock DIR: tiny random model + fake checkpoint written to DIR, cpu only, no mps, no real weights.
"""
import gc
import json
import platform
import sys

import torch
import transformers
from safetensors import safe_open

MODEL = "Qwen/Qwen3.5-2B"
REV = "15852e8c16360a2fea060d615a32b45270f8a8fc"
WEIGHTS_FILE = "model.safetensors-00001-of-00001.safetensors"
WEIGHTS_SHA256 = "aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1"  # setup README
EXPECT = {"hidden_size": 2048, "intermediate_size": 6144, "num_hidden_layers": 24}  # config_2b.json
N_PARAMS = 1881825088  # setup env/cpu_check.json
PREFIX = "model.language_model."


def file_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def compare_to_checkpoint(model, path):
    """every model tensor vs its checkpoint tensor, one at a time (peak = 1 extra tensor)."""
    sd = model.state_dict()
    emb = model.model.embed_tokens.weight
    res = {"n_checked": 0, "mismatch": [], "missing_in_file": [], "dtype_pairs": {},
           "lm_head_tied": model.lm_head.weight.data_ptr() == emb.data_ptr(), "unused_lm_keys": []}
    with safe_open(path, framework="pt") as f:
        keys = set(f.keys())
        used = set()
        for name, t in sd.items():
            if name == "lm_head.weight":
                continue  # tied, checked by data_ptr above
            key = PREFIX + name.removeprefix("model.")
            if key not in keys:
                res["missing_in_file"].append(name)
                continue
            used.add(key)
            c = f.get_tensor(key)
            pair = f"{c.dtype}->{t.dtype}".replace("torch.", "")
            res["dtype_pairs"][pair] = res["dtype_pairs"].get(pair, 0) + 1
            if tuple(c.shape) != tuple(t.shape) or not torch.equal(c.to(t.dtype), t.detach().cpu()):
                res["mismatch"].append(name)
            res["n_checked"] += 1
            del c
        res["unused_lm_keys"] = sorted(k for k in keys - used if k.startswith(PREFIX))[:20]
    gc.collect()
    res["ok"] = (not res["mismatch"] and not res["missing_in_file"] and res["lm_head_tied"]
                 and not res["unused_lm_keys"])
    return res


def template_checks(tok, res):
    # same as gate 1 env_check.py
    msgs = [{"role": "user", "content": "Reply in French. What is a cat?"}]
    res["template_nonthinking"] = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    res["template_thinking"] = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=True)
    for t in ["<think>", "</think>", "<|im_end|>", "<|endoftext|>"]:
        res[f"tok {t}"] = tok.encode(t, add_special_tokens=False)
    res["all_special_tokens"] = tok.all_special_tokens
    res["think_is_special_skipped"] = tok.decode(tok.encode("<think>a</think>b", add_special_tokens=False), skip_special_tokens=True)


def mock(dirpath):
    """tiny random model, fake checkpoint in the 2B key layout (+ ignored mtp / visual keys)."""
    import os
    from safetensors.torch import save_file
    from transformers import Qwen3_5ForCausalLM
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                                    "2026-11-06-gate3-scripts", "scripts")))
    import test_methods  # gate 3 tiny_model
    os.makedirs(dirpath, exist_ok=True)
    model = test_methods.tiny_model().to(torch.bfloat16)
    store = {PREFIX + n.removeprefix("model."): t.clone().contiguous()
             for n, t in model.state_dict().items() if n != "lm_head.weight"}
    store["mtp.fc.weight"] = torch.zeros(2, 2)
    store["model.visual.x"] = torch.zeros(2)
    good = os.path.join(dirpath, "good.safetensors")
    save_file(store, good)
    key = PREFIX + "layers.1.mlp.down_proj.weight"
    store[key] = store[key].clone()
    store[key][0, 0] += 1
    bad = os.path.join(dirpath, "bad.safetensors")
    save_file(store, bad)
    out = {"mock": True, "params": sum(p.numel() for p in model.parameters()),
           "good": compare_to_checkpoint(model, good), "bad": compare_to_checkpoint(model, bad)}
    out["pass"] = out["good"]["ok"] and out["bad"]["mismatch"] == ["model.layers.1.mlp.down_proj.weight"]
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["pass"] else 1)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--mock":
        mock(sys.argv[2])
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer, Qwen3_5ForCausalLM
    res = {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
           "torch": torch.__version__, "transformers": transformers.__version__,
           "mps_built": torch.backends.mps.is_built(), "mps_available": torch.backends.mps.is_available(),
           "model": MODEL, "revision": REV}
    tok = AutoTokenizer.from_pretrained(MODEL, revision=REV, trust_remote_code=False)
    template_checks(tok, res)
    path = hf_hub_download(MODEL, WEIGHTS_FILE, revision=REV, local_files_only=True)
    res["weights_sha256"] = file_sha256(path)
    res["weights_sha256_ok"] = res["weights_sha256"] == WEIGHTS_SHA256
    lm, info = Qwen3_5ForCausalLM.from_pretrained(  # = g3common.load_model, plus loading info
        MODEL, revision=REV, trust_remote_code=False, use_safetensors=True, dtype=torch.bfloat16,
        output_loading_info=True)
    lm.eval()
    res["loading_info"] = {k: sorted(v)[:20] for k, v in info.items()}
    res["config"] = {k: getattr(lm.config, k) for k in EXPECT}
    res["n_params"] = sum(p.numel() for p in lm.parameters())
    res["config_ok"] = res["config"] == EXPECT and res["n_params"] == N_PARAMS
    res["generation_config"] = lm.generation_config.to_dict()
    res["checkpoint_compare"] = compare_to_checkpoint(lm, path)
    lm = lm.to("mps")
    enc = tok(res["template_nonthinking"], return_tensors="pt").to("mps")
    with torch.no_grad():
        logits = lm(**enc).logits[0, -1].float().cpu()
    res["last_token_top5_mps_bf16"] = logits.topk(5).indices.tolist()
    res["logits_finite"] = bool(torch.isfinite(logits).all())
    res["pass"] = (res["weights_sha256_ok"] and res["config_ok"] and res["checkpoint_compare"]["ok"]
                   and res["logits_finite"] and not res["loading_info"].get("missing_keys"))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
