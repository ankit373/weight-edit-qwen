"""run gate 3 generate.py (unchanged) with a prompt baseline: replace the user prompt
(instr_end) or put a 1-shot user/assistant pair before it (fewshot). seed, sampling, stop
tokens and output fields stay those of generate.py / gate 1.

usage: gen_variant.py --variants <prompts/*.jsonl> --kind instr_end|fewshot <generate.py args>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts")
sys.path.insert(0, os.path.abspath(S))
import g3common  # noqa: E402
import generate  # noqa: E402


def main():
    argv = sys.argv[1:]
    vpath = argv[argv.index("--variants") + 1]
    kind = argv[argv.index("--kind") + 1]
    for flag in ("--variants", "--kind"):
        i = argv.index(flag)
        del argv[i:i + 2]
    variants = {r["id"]: r for r in map(json.loads, open(vpath))}

    base_load = g3common.load_prompts
    base_chat = g3common.chat_text
    turns_by_prompt = {}

    def load_prompts():
        rows = []
        for r in base_load():  # same order as gate 1, so seed = 1234 + global index is kept
            v = variants.get(r["id"])
            if v is not None:
                r = dict(r, variant=kind, prompt_original=r["prompt"])
                if kind == "instr_end":
                    r["prompt"] = v["prompt"]
                else:
                    assert v["prompt"] == r["prompt"]
                    r["fewshot_turns"] = v["fewshot_turns"]
                    key = r["prompt"]
                    assert turns_by_prompt.get(key, v["fewshot_turns"]) == v["fewshot_turns"], key
                    turns_by_prompt[key] = v["fewshot_turns"]
            rows.append(r)
        return rows

    def chat_text(tok, prompt):
        turns = turns_by_prompt.get(prompt) if kind == "fewshot" else None
        if not turns:
            return base_chat(tok, prompt)
        return tok.apply_chat_template(  # same call as g3common.chat_text, with history turns
            turns + [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False,
        )

    g3common.load_prompts = load_prompts
    g3common.chat_text = chat_text
    sys.argv = [generate.__file__] + argv
    generate.main()


if __name__ == "__main__":
    main()
