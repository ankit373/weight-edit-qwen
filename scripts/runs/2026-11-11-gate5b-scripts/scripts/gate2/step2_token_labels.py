"""step 2a: label every vocab token by script, and build per-language contrast sets.

usage: step2_token_labels.py <gate1 full_nonthinking.jsonl> <out_dir>
script label: unicode script of the token's letters (decoded text). one script -> that script,
none -> "none", several -> "mixed", undecodable byte piece -> "partial".
contrast sets (needed for latin-script targets, where script cannot tell english from target):
from gate 1 MONOLINGUAL outputs only (no cross-lingual dev/test text), re-tokenized.
  X_set[X]  = latin letter-only tokens seen >= MIN times in X monolingual outputs and never in en ones
  EN_set[X] = latin letter-only tokens seen >= MIN times in en monolingual outputs and never in X ones
"""
import collections
import json
import os
import sys
import unicodedata

import numpy as np
from transformers import AutoTokenizer

MODEL, REVISION = "Qwen/Qwen3.5-2B", "15852e8c16360a2fea060d615a32b45270f8a8fc"  # part B: 2B pin
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SCRIPTS = ["latin", "arabic", "devanagari", "cyrillic", "hangul", "han", "kana", "other", "none", "mixed", "partial"]
MIN = 3
inp, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
V = len(tok)


def char_script(ch):
    n = unicodedata.name(ch, "")
    for key, lab in (("LATIN", "latin"), ("ARABIC", "arabic"), ("DEVANAGARI", "devanagari"),
                     ("CYRILLIC", "cyrillic"), ("HANGUL", "hangul"), ("CJK", "han"),
                     ("HIRAGANA", "kana"), ("KATAKANA", "kana")):
        if n.startswith(key):
            return lab
    return "other"


texts = [tok.decode([i]) for i in range(V)]
script = np.zeros(V, dtype=np.int8)
letters_only_latin = np.zeros(V, dtype=bool)
for i, t in enumerate(texts):
    if "�" in t:
        lab = "partial"
    else:
        s = {char_script(c) for c in t if c.isalpha()}
        lab = "none" if not s else (s.pop() if len(s) == 1 else "mixed")
    script[i] = SCRIPTS.index(lab)
    core = t.strip()
    letters_only_latin[i] = lab == "latin" and len(core) >= 2 and core.isalpha()
special = set(tok.all_special_ids)
for i in special:
    script[i] = SCRIPTS.index("none")
    letters_only_latin[i] = False

counts = collections.defaultdict(collections.Counter)
n_resp = collections.Counter()
for l in open(inp):
    r = json.loads(l)
    if r["task"] != "monolingual":
        continue  # contrast sets come from monolingual outputs only
    counts[r["language"]].update(tok(r["completion"], add_special_tokens=False)["input_ids"])
    n_resp[r["language"]] += 1

x_set = np.zeros((len(LANGS), V), dtype=bool)
en_set = np.zeros((len(LANGS), V), dtype=bool)
summary = {"vocab": V, "min_count": MIN, "mono_responses": dict(n_resp),
           "script_counts": {s: int((script == k).sum()) for k, s in enumerate(SCRIPTS)}, "contrast": {}}
en = counts["en"]
for j, X in enumerate(LANGS):
    cx = counts[X]
    xs = [i for i, c in cx.items() if c >= MIN and en[i] == 0 and letters_only_latin[i]]
    es = [i for i, c in en.items() if c >= MIN and cx[i] == 0 and letters_only_latin[i]]
    x_set[j, xs] = True
    en_set[j, es] = True
    summary["contrast"][X] = {
        "n_X_set": len(xs), "n_EN_set": len(es),
        "X_examples": [texts[i] for i in sorted(xs, key=lambda i: -cx[i])[:15]],
        "EN_examples": [texts[i] for i in sorted(es, key=lambda i: -en[i])[:15]]}

np.save(os.path.join(out_dir, "script.npy"), script, allow_pickle=False)
np.save(os.path.join(out_dir, "x_set.npy"), x_set, allow_pickle=False)
np.save(os.path.join(out_dir, "en_set.npy"), en_set, allow_pickle=False)
json.dump({"scripts": SCRIPTS, "langs": LANGS, **summary}, open(os.path.join(out_dir, "token_labels.json"), "w"),
          indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in summary.items() if k != "contrast"}, indent=1))
print({X: (v["n_X_set"], v["n_EN_set"]) for X, v in summary["contrast"].items()})
