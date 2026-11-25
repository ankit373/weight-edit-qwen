"""gate 3 generate.py, unchanged, on a local checkpoint folder. only g3common.load_model is swapped.

usage: gen_p50c.py --ckpt DIR --manifest MANIFEST --expect edited|base <generate.py args>

tokenizer stays the pinned hub base (g3common.load_tokenizer). after loading, the manifest
tensors must hash to edited_sha256 (or base_sha256 with --expect base), else exit.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts"))
sys.path.insert(0, S)
import torch  # noqa: E402
import g3common  # noqa: E402


def pop_arg(name):
    i = sys.argv.index(name)
    val = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    return val


CKPT, MANIFEST, EXPECT = pop_arg("--ckpt"), pop_arg("--manifest"), pop_arg("--expect")
assert EXPECT in ("edited", "base"), EXPECT


def check_hashes(model):
    out = []
    for t in json.load(open(MANIFEST))["tensors"]:
        layer = int(t["name"].split(".")[3])  # model.language_model.layers.<n>.mlp.down_proj.weight
        assert t["name"].endswith("mlp.down_proj.weight"), t["name"]
        got = g3common.tensor_sha256(model.model.layers[layer].mlp.down_proj.weight)
        want = t["edited_sha256"] if EXPECT == "edited" else t["base_sha256"]
        out.append({"name": t["name"], "sha256": got, "ok": got == want})
    print(json.dumps({"ckpt": CKPT, "expect": EXPECT, "loaded_tensor_check": out}), flush=True)
    if not all(r["ok"] for r in out):
        sys.exit("loaded weights do not match the expected hashes")


def load_model(device, dtype):
    from transformers import Qwen3_5ForCausalLM
    model = Qwen3_5ForCausalLM.from_pretrained(
        CKPT, trust_remote_code=False, use_safetensors=True, local_files_only=True,
        dtype=getattr(torch, dtype),
    )
    check_hashes(model)
    return model.to(device).eval()


g3common.load_model = load_model
import generate  # noqa: E402  (imports the same g3common module object)

if __name__ == "__main__":
    sys.argv[0] = os.path.join(S, "generate.py")
    generate.main()
