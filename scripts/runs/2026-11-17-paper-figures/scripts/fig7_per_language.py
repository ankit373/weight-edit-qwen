"""fig 7: test complex LPR per target language, 0.8B: baseline, tuned ReCoVeR, editors 0 to 3 (seed 1)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, LANGS, Svg, Values, lin, score_row, write_text  # noqa: E402

METHODS = [
    ("baseline (gate 1)", "runs/2026-11-06-gate3-run/scores/baseline_test.json", "circle", False),
    ("ReCoVeR, tuned", "runs/2026-11-06-gate3-run/scores/recover_a0.03_on_test.json", "square", True),
    ("editor 0 (c02)", "runs/2026-11-10-gate4-eval/scores/final_test.json", "triangle", True),
    ("editor 1", "runs/2026-11-11-gate5a-eval-ws1/scores/final_test.json", "triangle_down", False),
    ("editor 2", "runs/2026-11-12-gate5a-eval-ws2/scores/final_test.json", "diamond", False),
    ("editor 3", "runs/2026-11-13-gate5a-eval-ws3/scores/final_test.json", "plus", True),
]


def collect(vals):
    data = {}
    for label, rel, *_ in METHODS:
        for lang in LANGS:
            r = score_row(rel, "complex_prompts", lang)
            vals.add("lpr", f"{label} {lang}", r["lpr"], rel, f"complex_prompts/{lang} lpr")
            vals.add("n_scored", f"{label} {lang}", r["n_scored"], rel, f"complex_prompts/{lang} n_scored")
            data[(label, lang)] = r
    return data


def draw(data, path):
    top, rowh = 80, 48
    W, H = 900, top + len(LANGS) * rowh + 110
    s = Svg(W, H)
    s.text(12, 22, "Test complex LPR per target language, Qwen3.5-0.8B (seed 1)", 14, weight="bold")
    s.text(12, 40, "51 complex test prompts per language; n scored per language and method in the values file. "
                   "no per-language CI is drawn.", 11)
    x0, x1, lo, hi = 110, 870, 40, 100
    bottom = top + len(LANGS) * rowh
    for t in range(lo, hi + 1, 10):
        x = lin(t, lo, hi, x0, x1)
        s.line(x, top - 6, x, bottom, stroke="#ccc", width=0.6, dash="2,3")
        s.line(x, bottom, x, bottom + 4)
        s.text(x, bottom + 16, str(t), 10, anchor="middle")
    s.line(x0, bottom, x1, bottom)
    s.text((x0 + x1) / 2, bottom + 32, "complex LPR, % (axis starts at 40)", 11, anchor="middle")
    for i, lang in enumerate(LANGS):
        yc = top + i * rowh + rowh / 2
        if i % 2 == 0:
            s.rect(x0, yc - rowh / 2, x1 - x0, rowh, fill="#f4f4f4", stroke="none")
        s.text(x0 - 12, yc + 4, lang, 12, anchor="end", weight="bold")
        for j, (label, _, shape, filled) in enumerate(METHODS):
            r = data[(label, lang)]
            y = yc - 17.5 + j * 7
            s.marker(lin(r["lpr"], lo, hi, x0, x1), y, shape, filled=filled, r=4)
    for j, (label, _, shape, filled) in enumerate(METHODS):
        x, y = 30 + (j % 3) * 290, bottom + 58 + (j // 3) * 20
        s.marker(x, y - 4, shape, filled=filled, r=4.5)
        s.text(x + 12, y, label, 11)
    s.save(path)


CAPTION = """Figure 7. Test cross-lingual complex LPR by target language on Qwen3.5-0.8B, sampling seed 1, 51 prompts per language with unscored answers left out (the scored count per cell is in fig7_per_language.values.tsv; the lowest is {nmin}). Markers within a row are offset a little in height so they do not hide each other. Every editor is above the baseline in every language except where noted in the values file. No interval is drawn: with 51 prompts from 17 task groups per language the per-language numbers are noisy; the cluster-bootstrap check of editor 0 against ReCoVeR by language is in runs/2026-11-11-stats-gate4/README.md (q3). Sources: the complex_prompts rows of runs/2026-11-06-gate3-run/scores/{{baseline,recover_a0.03_on}}_test.json, runs/2026-11-10-gate4-eval/scores/final_test.json and runs/2026-11-1*-gate5a-eval-ws{{1,2,3}}/scores/final_test.json."""


def main():
    vals = Values()
    data = collect(vals)
    path = os.path.join(FIG, "fig7_per_language.svg")
    draw(data, path)
    vals.write("fig7_per_language")
    nmin = min(r["n_scored"] for r in data.values())
    below = [(m[0], lang) for m in METHODS[2:] for lang in LANGS
             if data[(m[0], lang)]["lpr"] <= data[(METHODS[0][0], lang)]["lpr"]]
    cap = CAPTION.format(nmin=nmin)
    if below:
        cap = cap.replace("Every editor is above the baseline in every language except where noted in the values file.",
                          "Editor cells at or below the baseline: " + ", ".join(f"{m} {l}" for m, l in below) + ".")
    else:
        cap = cap.replace(" except where noted in the values file", "")
    write_text(os.path.join(FIG, "fig7_per_language.txt"), cap)
    print("wrote", path, "below baseline:", below)


if __name__ == "__main__":
    main()
