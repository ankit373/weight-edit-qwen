"""per-line fastText labels for every row of one outputs file, with gate 1's scoring rule.

usage: label_lines.py <rows.jsonl> <out.jsonl> <task> [<lang>]
imports the benchmark module unchanged (cwd = gate 1 scoring_workdir, as score.py / wrong_lang.py do).
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
inp, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
task = sys.argv[3]
only_lang = sys.argv[4] if len(sys.argv) > 4 else None
os.chdir(os.path.join(ROOT, "runs", "2026-11-05-gate1-baseline", "scoring_workdir"))
sys.path.insert(0, os.path.join(ROOT, "external", "language-confusion"))
import compute_metrics as cm  # noqa: E402

with open(out, "w") as f:
    for l in open(inp):
        r = json.loads(l)
        if r["task"] != task or (only_lang and r["language"] != only_lang):
            continue
        if task == "crosslingual" and r["source"] != "complex_prompts":
            continue
        lang = r["language"]
        lines = cm.normalize(r["completion"]).split("\n")
        toks = [cm.tokenize(x, lang) for x in lines]
        kept = [i for i, t in enumerate(toks) if len(t) >= 5]
        labels = [cm.langid(lines[i]) for i in kept]
        n_bad = sum(lab != lang for lab in labels)
        if not kept:
            status = "unscored"
        elif n_bad == 0:
            status = "pass"
        elif n_bad == len(kept):
            status = "full"
        else:
            status = "partial"
        # cm.compute_metrics word rule: passing line set with any dictionary english word (> 3 chars)
        en_word = status == "pass" and any(t.strip() in cm.en_words for i in kept for t in toks[i])
        f.write(json.dumps({
            "id": r["id"], "language": lang, "status": status,
            "line_idx": kept, "line_labels": labels, "en_word": en_word,
        }, ensure_ascii=False) + "\n")
