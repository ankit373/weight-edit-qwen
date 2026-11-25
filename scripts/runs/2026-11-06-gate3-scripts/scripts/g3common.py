"""shared helpers for gate 3. model, prompts and generation settings come from gate 1 gen.py."""
import hashlib
import importlib.util
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GATE1 = os.path.join(PROJECT, "runs", "2026-11-05-gate1-baseline")


def _load_gate1_gen():
    # one definition of MODEL, REVISION, load_prompts: gate 1 gen.py:13-35
    spec = importlib.util.spec_from_file_location("gate1_gen", os.path.join(GATE1, "gen.py"))
    mod = importlib.util.module_from_spec(spec)
    old, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ in gate 1
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


gate1 = _load_gate1_gen()
MODEL, REVISION, load_prompts = gate1.MODEL, gate1.REVISION, gate1.load_prompts

# LCB code -> FLORES-200 file stem. iso codes as in recover/language_utils.py:2-21;
# script picks as in collect_language_vectors/collect.py:55-61 (arb+Arab, cmn+Hans).
LCB_TO_FLORES = {
    "ar": "arb_Arab", "de": "deu_Latn", "en": "eng_Latn", "es": "spa_Latn",
    "fr": "fra_Latn", "hi": "hin_Deva", "id": "ind_Latn", "it": "ita_Latn",
    "ja": "jpn_Jpan", "ko": "kor_Hang", "pt": "por_Latn", "ru": "rus_Cyrl",
    "tr": "tur_Latn", "vi": "vie_Latn", "zh": "zho_Hans",
}


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)


def load_model(device, dtype):
    from transformers import Qwen3_5ForCausalLM
    model = Qwen3_5ForCausalLM.from_pretrained(
        MODEL, revision=REVISION, trust_remote_code=False, use_safetensors=True,
        dtype=getattr(torch, dtype),
    )
    return model.to(device).eval()


def chat_text(tok, prompt):
    # same call as gate 1 gen.py:86-90 (non-thinking, no system prompt)
    return tok.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False,
    )


def gen_kwargs(tok, greedy, max_new_tokens=100):
    """gate 1 settings (gen.py:65-73), or greedy as in Nie generate_outputs.py:30-34."""
    stop = [tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")]
    kw = dict(max_new_tokens=max_new_tokens, eos_token_id=stop,
              pad_token_id=tok.convert_tokens_to_ids("<|endoftext|>"), repetition_penalty=1.0)
    if greedy:
        kw.update(do_sample=False, temperature=None, top_p=None, top_k=None)
    else:
        kw.update(do_sample=True, temperature=0.3, top_p=0.75, top_k=20, min_p=None)
    return kw


def read_ids(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tensor_sha256(t):
    # hash of the raw bytes on cpu, dtype kept (bf16 viewed as int16)
    t = t.detach().contiguous().cpu()
    if t.dtype == torch.bfloat16:
        t = t.view(torch.int16)
    return hashlib.sha256(t.numpy().tobytes()).hexdigest()
