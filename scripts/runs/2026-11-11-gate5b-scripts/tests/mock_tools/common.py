"""shared paths, model loading, prompts and hashes for the gate 4 tools (gen env)."""
import hashlib
import json
import os

MODEL = "Qwen/Qwen3.5-2B"
REVISION = "15852e8c16360a2fea060d615a32b45270f8a8fc"
# sha256 of model.safetensors at REVISION (equals the hub LFS oid, gate 1 README security 4)
BASE_FILE_SHA256 = "aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1"

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEV_IDS = os.path.join(WS, "ids", "dev.txt")
SCREEN_IDS = os.path.join(WS, "ids", "screen200.txt")
DEV_PROMPTS = os.path.join(WS, "data", "dev_prompts.jsonl")
GATE1_DEV = os.path.join(WS, "data", "gate1_dev_outputs.jsonl")
GATE1_DEV_NLL = os.path.join(WS, "data", "gate1_dev_nll.jsonl")

# gate 1 settings (ref/gate1-baseline/README.md "settings"), fixed for every scoring run
GEN = dict(max_new_tokens=100, temperature=0.3, top_p=0.75, top_k=20, seed=1234)


def read_ids(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def read_jsonl(path):
    with open(path) as f:
        return {r["id"]: r for r in map(json.loads, f)}


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tensor_sha256(t):
    """sha256 of the raw bytes of a tensor (cpu, contiguous, its own dtype)."""
    import torch
    b = t.detach().to("cpu").contiguous().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(b).hexdigest()


def base_file_path():
    """the pinned safetensors file in the local hf cache; checked against BASE_FILE_SHA256."""
    from huggingface_hub import hf_hub_download
    return hf_hub_download(MODEL, "model.safetensors-00001-of-00001.safetensors",
                           revision=REVISION, local_files_only=True)


def check_base_file():
    got = file_sha256(base_file_path())
    if got != BASE_FILE_SHA256:
        raise SystemExit(f"base weights sha256 mismatch: {got}")
    return got


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)


def load_model(device="mps", dtype="bfloat16"):
    import torch
    from transformers import Qwen3_5ForCausalLM
    model = Qwen3_5ForCausalLM.from_pretrained(
        MODEL, revision=REVISION, trust_remote_code=False, use_safetensors=True,
        dtype=getattr(torch, dtype),
    )
    return model.to(device).eval()


def chat_text(tok, prompt):
    """one user turn, non-thinking chat template, as in gate 1."""
    return tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)
