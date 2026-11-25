"""table: real failure -> fixed answer pairs, same prompt id, taken from the by-eye samples. truncated text.

rule (fixed before looking at the picks): the failing answer's id must be in a by-eye file and be a full failure
in the scorer's wrong_lang file of that baseline run. the fixed answer must not be in the method's wrong_lang list,
must have a line of 5 or more words, and the target must not be zh or ja (whitespace words only work for the others).
pairs whose fixed side is also in a by-eye file come first. text comes from the run's output rows; where a by-eye
file holds the same answer, the script checks that the by-eye text is a prefix of it.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAB, Values, load, md_table, p, write_text  # noqa: E402

G2E = ["runs/2026-11-06-gate2-diagnosis/logs/eyeball_sample1.txt", "runs/2026-11-06-gate2-diagnosis/logs/eyeball_sample2.txt"]
B2E = ["runs/2026-11-13-gate5b-diagnosis/logs/eyeball_sample1.txt", "runs/2026-11-13-gate5b-diagnosis/logs/eyeball_sample2.txt"]
G3 = "runs/2026-11-06-gate3-run"
E4 = "runs/2026-11-10-gate4-eval"
WS2 = "runs/2026-11-12-gate5a-eval-ws2"
B1 = "runs/2026-11-11-gate5b-baseline"
B3 = "runs/2026-11-13-gate5b-instr-end"
B4 = "runs/2026-11-14-gate5b-recover"
TRUNC = 150

# (model, split, method, baseline rows, baseline wrong_lang, baseline by-eye files,
#  method rows, method wrong_lang, method by-eye file or None, how many pairs)
PLANS = [
    ("0.8B", "test", "editor 0 (c02)", f"{G3}/outputs/baseline_test.jsonl", f"{G3}/scores/baseline_test_wrong_lang.json",
     [f"{E4}/evidence/eyeball20_gate1_test_same_ids.txt"], f"{E4}/outputs/final_test.jsonl",
     f"{E4}/scores/final_test_wrong_lang.json", f"{E4}/evidence/eyeball20_final_test.txt", 1),
    ("0.8B", "test", "editor 2", f"{G3}/outputs/baseline_test.jsonl", f"{G3}/scores/baseline_test_wrong_lang.json",
     [f"{E4}/evidence/eyeball20_gate1_test_same_ids.txt"], f"{WS2}/outputs/final_test.jsonl",
     f"{WS2}/scores/final_test_wrong_lang.json", f"{WS2}/evidence/eyeball20_final_test.txt", 1),
    ("2B", "dev", "ReCoVeR, tuned (alpha 0.03, restore off)", f"{B1}/outputs/baseline_dev.jsonl",
     f"{B1}/scores/baseline_dev_wrong_lang.json", B2E, f"{B4}/outputs/recover_a0.03_off_dev.jsonl",
     f"{B4}/scores/recover_a0.03_off_dev_wrong_lang.json", f"{B4}/eyeball/recover_a0.03_off_devcx.txt", 1),
    ("0.8B", "dev", "ReCoVeR, tuned (alpha 0.03, restore on)", f"{G3}/outputs/baseline_dev.jsonl",
     f"{G3}/scores/baseline_dev_wrong_lang.json", G2E, f"{G3}/outputs/recover_a0.03_on_dev.jsonl",
     f"{G3}/scores/recover_a0.03_on_dev_wrong_lang.json", None, 2),
    ("2B", "dev", "instruction at end (B3)", f"{B1}/outputs/baseline_dev.jsonl", f"{B1}/scores/baseline_dev_wrong_lang.json",
     B2E, f"{B3}/outputs/instr_end_dev.jsonl", f"{B3}/scores/instr_end_dev_wrong_lang.json", None, 1),
]


def rows_by_id(rel, ids):
    out = {}
    with open(p(rel), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["id"] in ids:
                out[r["id"]] = r
    return out


def eye_ids(rel):
    """ids in a by-eye file, in file order, with the quoted answer text when the file has one."""
    out = []
    with open(p(rel), encoding="utf-8") as f:
        for ln in f:
            g = re.match(r"\[\d+\] (crosslingual/\S+) \(\d+ tok\): (.*)$", ln.rstrip("\n"))
            if g:
                out.append((g[1], ast.literal_eval(g[2])))
                continue
            g = re.match(r"===\s+(crosslingual/\S+) ", ln)
            if g:
                out.append((g[1], None))
    return out


def failing(rel):
    return {r["id"]: r for r in load(rel)["failing_responses"]}


def one_line(s, n=TRUNC):
    s = " ".join(s.split())
    s = s if len(s) <= n else s[:n].rstrip() + " ..."
    return s.replace("|", "\\|")


def has_long_line(text):
    return any(len(ln.split()) >= 5 for ln in text.split("\n"))


def main():
    vals = Values()
    used, table = set(), []
    for model, split, method, b_rows, b_wl, b_eye, m_rows, m_wl, m_eye, k in PLANS:
        cand = []
        for rel in b_eye:
            cand += [(i, t, rel) for i, t in eye_ids(rel)]
        m_eye_map = dict(eye_ids(m_eye)) if m_eye else {}
        bfail, mfail = failing(b_wl), failing(m_wl)
        ids = {c[0] for c in cand}
        brows, mrows = rows_by_id(b_rows, ids), rows_by_id(m_rows, ids)
        picked, langs = [], set()
        order = sorted(cand, key=lambda c: c[0] not in m_eye_map)
        for i, t, rel in order:
            src, lang = i.split("/")[1], i.split("/")[2]
            if (model, i, method) in used or lang in ("zh", "ja") or lang in langs or src != "complex_prompts":
                continue
            if not (i in bfail and bfail[i]["full_response_wrong"]) or i in mfail or i not in mrows:
                continue
            base_txt, fix_txt = brows[i]["completion"], mrows[i]["completion"]
            if not has_long_line(fix_txt):
                continue
            if t is not None:
                assert base_txt.startswith(t.rstrip()[:200]), ("by-eye text differs", i, rel)
            if i in m_eye_map:
                assert fix_txt.startswith(m_eye_map[i].rstrip()[:200]), ("by-eye text differs", i, m_eye)
            picked.append(i)
            langs.add(lang)
            used.add((model, i, method))
            prompt = brows[i]["prompt"]
            table.append([model, split, i.replace("crosslingual/", ""), lang, one_line(prompt, 90),
                          one_line(base_txt), method, one_line(fix_txt),
                          f"{rel}" + (f"; {m_eye}" if i in m_eye_map else f"; fixed side: {m_rows} (not in a by-eye file)")])
            vals.add("pair", f"{model} {split} {i} {method}", 1, f"{b_rows}; {m_rows}", "completion")
            if len(picked) == k:
                break
        if len(picked) < k:
            print("only", len(picked), "pairs for", model, split, method)
    head = ["model", "split", "id", "lang", "prompt (start)", "baseline answer (full failure)", "method",
            "method answer, same id", "by-eye file(s)"]
    text = (
        "# failure -> fixed examples (same prompt id, one seed)\n\n"
        "made by `scripts/tab_examples.py`. selection rule is in the script docstring and was fixed before looking at "
        f"the picks; texts are the first {TRUNC} characters of `completion` from the runs' output rows, whitespace "
        "collapsed. the baseline answer is a full failure in the scorer's wrong_lang file; the method answer is not "
        "in its wrong_lang list. these show what a fix looks like, not how often fixes happen.\n\n" +
        md_table(head, table))
    write_text(os.path.join(TAB, "examples.md"), text)
    vals.write("examples", TAB)
    print("wrote", os.path.join(TAB, "examples.md"), len(table), "rows")


if __name__ == "__main__":
    main()
