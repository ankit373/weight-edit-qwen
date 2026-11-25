"""build the two prompt baselines for every cross-lingual prompt (dev + test).

usage: prompt_variants.py <out_dir>
writes:
  instr_end.jsonl   id, language, source, where (gate 2 rule), rule, changed, prompt_original, prompt
  fewshot.jsonl     id, language, prompt, fewshot_turns (the 1-shot user/assistant pair)
  fewshot_overlap.json   30-char overlap of the few-shot examples with every LCB prompt
  instr_end_check.json   task text check (original minus instruction == new minus instruction)
"""
import ast
import json
import os
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT, "runs", "2026-11-05-gate1-baseline"))
from gen import load_prompts  # noqa: E402

out_dir = sys.argv[1]

# --- gate 2 labels: copied from runs/2026-11-06-gate2-diagnosis/step1_behaviour.py:19-21,26-30,64-75 ---
NAME = dict(ar="Arabic", de="German", es="Spanish", fr="French", hi="Hindi", id="Indonesian",
            it="Italian", ja="Japanese", ko="Korean", pt="Portuguese", ru="Russian",
            tr="Turkish", vi="Vietnamese", zh="Chinese")
TEMPLATES = [
    ("answer_in", r"\bAnswer in {n}\b"), ("respond_in", r"\b[Rr]espond in {n}\b"),
    ("reply_in", r"\bReply in {n}\b"), ("write_in", r"\b[Ww]rite in {n}\b"),
    ("use_X", r"\b[Uu]se {n}\b"), ("using_X", r"\busing {n}\b"), ("in_X_inline", r"\bin {n}\b"),
]


def gate2_features(prompt, lang):
    n = NAME[lang]
    pos = prompt.find(n)
    templ = "other"
    for t, pat in TEMPLATES:
        if re.search(pat.format(n=n), prompt):
            templ = t
            break
    where = "start" if pos < 40 else ("end" if len(prompt) - (pos + len(n)) < 40 else "middle")
    return {"lang_name_char": pos, "lang_name_where": where, "template": templ}


# --- instruction at the end (ours, fixed before any result) ---
# a sentence that is only a language instruction is moved verbatim to the end.
SENTENCE = re.compile(
    r"^(please |make sure to |you should )?"
    r"(reply|respond|answer|anwser|write|use)"
    r"( your (answer|response))?( all of this)?( (in|using))? X"
    r"( please| only| for your summary)?[.!]*$"
    r"|^your output should be written in X[.!]*$", re.I)
# otherwise the language phrase is cut out of the task sentence and a fixed sentence is appended.
INLINE = [" written in X only", " written in X", " using X", " in X only", " in X"]
APPEND = "Respond in X."
SEP = {"complex_prompts": "\n", "okapi": " ", "sharegpt": " "}  # as in each set's own end rows


def find_name(prompt, n):
    """the instruction's language name: whole word, not part of a compound (e.g. Italian-American)."""
    for m in re.finditer(r"\b%s\b" % re.escape(n), prompt):
        if prompt[m.end():m.end() + 1] != "-":
            return m.start()
    raise ValueError("no language name")


def sentence_span(p, pos, end):
    left = 0
    for b in ("\n", ". ", "? ", "! ", ": "):
        k = p.rfind(b, 0, pos)
        if k != -1:
            left = max(left, k + len(b))
    right = len(p)
    for b in (".", "!", "?", "\n"):
        k = p.find(b, end)
        if k != -1:
            right = min(right, k + (0 if b == "\n" else 1))
    while right < len(p) and p[right] in ".!":
        right += 1
    return left, right


def join_cut(before, after):
    """join the text around a removed span. only whitespace at the cut changes."""
    lines = before.split("\n")
    if re.fullmatch(r"\s*\d+\.\s*", lines[-1]):  # a numbered list item left empty
        before = "\n".join(lines[:-1])
    if not before.strip():
        return after.lstrip()
    if after[:1] in ("\n", ""):
        return before.rstrip(" \t") + after
    if before[-1:] in (" ", "\t", "\n"):
        return before + after.lstrip(" \t")
    return before + after


def finish(rest, source, instr):
    """rest + separator + instruction. on one-line joins, end the task with a period first
    if it ends in a letter or digit (as LCB's own end rows do, e.g. okapi row 98)."""
    rest = rest.rstrip()
    if SEP[source] == " " and re.search(r"\w$", rest):
        rest += "."
    return rest + SEP[source] + instr


def move_to_end(prompt, lang, source, where):
    n = NAME[lang]
    if where == "end":
        return prompt, "unchanged_end", None
    pos = find_name(prompt, n)
    left, right = sentence_span(prompt, pos, pos + len(n))
    sent = prompt[left:right].strip()
    if SENTENCE.match(sent.replace(n, "X")):
        rest = join_cut(prompt[:left], prompt[right:])
        return finish(rest, source, sent), "move_sentence", sent
    for pat in INLINE:
        phrase = pat.replace("X", n)
        k = prompt.find(phrase, max(0, pos - len(phrase)))
        if k != -1 and k <= pos < k + len(phrase):
            rest = prompt[:k] + prompt[k + len(phrase):]
            return finish(rest, source, APPEND.replace("X", n)), "cut_inline", phrase.strip()
    return prompt, "no_rule", None


def norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w]+", " ", s)
    return " ".join(s.split())


def task_text(prompt, removed):
    """prompt with the instruction removed, for the task-text check."""
    return norm(prompt.replace(removed, " ", 1)) if removed else norm(prompt)


# --- few-shot: LCB repo few_shot_prompting.py, parsed with ast (no code run) ---
def load_fewshot():
    path = os.path.join(PROJECT, "external", "language-confusion", "few_shot_prompting.py")
    tree = ast.parse(open(path).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "few_shot_examples_crosslingual":
            return ast.literal_eval(node.value), path
    raise KeyError


def main():
    rows = [r for r in load_prompts() if r["task"] == "crosslingual"]
    fs, fs_path = load_fewshot()
    role = {"User": "user", "Chatbot": "assistant"}

    ie, check, bad = [], [], []
    for r in rows:
        g2 = gate2_features(r["prompt"], r["language"])
        new, rule, removed = move_to_end(r["prompt"], r["language"], r["source"], g2["lang_name_where"])
        appended = None
        if rule == "move_sentence":
            appended = removed
        elif rule == "cut_inline":
            appended = APPEND.replace("X", NAME[r["language"]])
        rec = {"id": r["id"], "language": r["language"], "source": r["source"], **g2,
               "rule": rule, "changed": new != r["prompt"], "removed": removed,
               "appended": appended, "prompt_original": r["prompt"], "prompt": new}
        ie.append(rec)
        if rule in ("move_sentence", "cut_inline"):
            a = task_text(r["prompt"], removed if rule == "cut_inline" else removed)
            b = norm(new[: len(new) - len(appended)])
            ok = a == b and new.endswith(appended)
            check.append({"id": r["id"], "ok": ok})
            if not ok:
                bad.append({"id": r["id"], "a": a[:300], "b": b[:300]})
    with open(os.path.join(out_dir, "instr_end.jsonl"), "w") as f:
        for rec in ie:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    summary = {}
    for rec in ie:
        k = f'{rec["source"]}/{rec["lang_name_where"]}/{rec["rule"]}'
        summary[k] = summary.get(k, 0) + 1
    json.dump({"rule_counts": summary, "n_checked": len(check),
               "n_task_text_equal": sum(c["ok"] for c in check), "not_equal": bad},
              open(os.path.join(out_dir, "instr_end_check.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1), "checked", len(check), "bad", len(bad))

    # few-shot rows: first example (2 turns) of the target language, as user/assistant turns
    fsr = []
    for r in rows:
        turns = fs[r["language"]][:2]
        assert [t["role"] for t in turns] == ["User", "Chatbot"]
        fsr.append({"id": r["id"], "language": r["language"], "prompt": r["prompt"],
                    "fewshot_turns": [{"role": role[t["role"]], "content": t["message"]} for t in turns]})
    with open(os.path.join(out_dir, "fewshot.jsonl"), "w") as f:
        for rec in fsr:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # overlap: any 30-char string of any few-shot example (all 5 per language) inside any LCB prompt
    allp = [norm(r["prompt"]) for r in load_prompts()]
    ids = [r["id"] for r in load_prompts()]
    hits = []
    for lang, turns in fs.items():
        for j, t in enumerate(turns):
            s = norm(t["message"])
            grams = {s[i:i + 30] for i in range(0, max(1, len(s) - 29))}
            for pid, p in zip(ids, allp):
                shared = [g for g in grams if g in p]
                if shared:
                    hits.append({"lang": lang, "turn": j, "role": t["role"], "lcb_id": pid,
                                 "n_shared": len(shared), "example": shared[:3]})
    used = [h for h in hits if h["turn"] < 2]
    json.dump({"fewshot_file": fs_path, "n_hits_any_turn": len(hits), "n_hits_used_turns": len(used),
               "hits": hits}, open(os.path.join(out_dir, "fewshot_overlap.json"), "w"), indent=1,
              ensure_ascii=False)
    print("fewshot overlap hits (all 5 examples):", len(hits), "in the used 1-shot turns:", len(used))


if __name__ == "__main__":
    main()
