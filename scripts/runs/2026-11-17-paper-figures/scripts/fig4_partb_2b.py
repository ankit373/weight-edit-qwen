"""fig 4: Qwen3.5-2B part B. complex and all LPR on dev and test for baseline, instruction at end, ReCoVeR, blind edit c06."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, f1, lin, read_lines, score_row, write_text  # noqa: E402

B1 = "runs/2026-11-11-gate5b-baseline/scores"
B3 = "runs/2026-11-13-gate5b-instr-end/scores"
B4 = "runs/2026-11-14-gate5b-recover/scores"
C06_DEV = "gate5b-workspace/work/c06/dev_scores.json"  # the editor's own full-dev scoring; no eval rescore exists
C06_TEST = "runs/2026-11-17-gate5b-eval/scores/final_test.json"
FINAL = "gate5b-workspace/FINAL.md"

METHODS = [
    ("baseline (B1)", f"{B1}/baseline_dev.json", f"{B1}/baseline_test.json"),
    ("instruction at end (B3)", f"{B3}/instr_end_dev.json", f"{B3}/instr_end_test.json"),
    ("ReCoVeR, tuned (alpha 0.03, restore off)", f"{B4}/recover_a0.03_off_dev.json", f"{B4}/recover_a0.03_off_test.json"),
    ("ReCoVeR, paper default (alpha 1)", f"{B4}/recover_a1_on_dev.json", f"{B4}/recover_a1_on_test.json"),
    ("blind edit, 2B (c06)", C06_DEV, C06_TEST),
]
PANELS = [("complex_prompts", "cross-lingual complex LPR, %"), ("all", "all cross-lingual LPR, %")]


def check_final(vals, data):
    """the c06 dev LPRs must match the bold numbers in the editor's FINAL.md table."""
    want = {"complex LPR (main)": data[-1][1]["dev"]["lpr"], "all LPR": data[-1][2]["dev"]["lpr"]}
    for i, ln in enumerate(read_lines(FINAL), 1):
        g = re.match(r"\| (complex LPR \(main\)|all LPR) \| [\d.]+ \| \*\*([\d.]+)\*\* \|", ln)
        if g:
            assert f1(want.pop(g[1])) == g[2], (g[1], g[2])
            vals.add("FINAL.md check", f"c06 dev {g[1]}", float(g[2]), FINAL, f"line {i}")
    assert not want, want


def collect(vals):
    data = []
    for label, dev, test in METHODS:
        row = [label]
        for src, _ in PANELS:
            cell = {}
            for split, rel in (("dev", dev), ("test", test)):
                r = score_row(rel, src)
                vals.add(f"{src} {split} lpr", label, r["lpr"], rel, f"{src}/all lpr")
                vals.add(f"{src} {split} n_scored", label, r["n_scored"], rel, f"{src}/all n_scored")
                vals.add(f"{src} {split} n", label, r["n"], rel, f"{src}/all n")
                cell[split] = r
            row.append(cell)
        data.append(row)
    return data


def draw(data, path):
    W, top, rowh = 1000, 96, 54
    H = top + len(data) * rowh + 90
    s = Svg(W, H)
    s.text(12, 22, "Qwen3.5-2B, part B: dev and test", 14, weight="bold")
    s.text(12, 40, "open circle = dev (2086 prompts, 672 complex), filled circle = test (2100, 714 complex). one seed.", 11)
    s.text(12, 56, "n = scored answers. c06 dev is the editor's own full-dev scoring; its test run was done once after the edit was frozen.", 11)
    lo, hi = 60, 100
    xs = [(330, 640), (680, 990)]
    for (src, title), (x0, x1) in zip(PANELS, xs):
        s.text((x0 + x1) / 2, top - 12, title, 12, anchor="middle", weight="bold")
    bottom = top + len(data) * rowh + 6
    for i, row in enumerate(data):
        yc = top + i * rowh + rowh / 2
        s.text(12, yc + 4, row[0], 11)
        for (src, _), (x0, x1), cell in zip(PANELS, xs, row[1:]):
            for j, split in enumerate(("dev", "test")):
                y = yc - 9 + j * 18
                r = cell[split]
                s.line(x0, y, x1, y, stroke="#e4e4e4", width=0.8)
                x = lin(r["lpr"], lo, hi, x0, x1)
                s.marker(x, y, "circle", filled=(split == "test"), r=4.5)
                lab = f"{f1(r['lpr'])}  ({split}, n={r['n_scored']}/{r['n']})"
                if r["lpr"] > 85:
                    s.text(x - 9, y + 4, lab, 9.5, anchor="end")
                else:
                    s.text(x + 9, y + 4, lab, 9.5)
    for x0, x1 in xs:
        s.line(x0, bottom, x1, bottom)
        for t in range(lo, hi + 1, 10):
            xt = lin(t, lo, hi, x0, x1)
            s.line(xt, top - 4, xt, bottom, stroke="#c8c8c8", width=0.6, dash="2,3")
            s.line(xt, bottom, xt, bottom + 4)
            s.text(xt, bottom + 16, str(t), 10, anchor="middle")
        s.text((x0 + x1) / 2, bottom + 32, "LPR, % (axis starts at 60)", 11, anchor="middle")
    s.save(path)


CAPTION = """Figure 4. Part B on Qwen3.5-2B: LPR on dev (open) and test (filled), one sampling seed. Left: cross-lingual complex prompts; right: all cross-lingual prompts. Unscored answers are left out; n is scored answers out of the prompts in that set. The tuned ReCoVeR setting (alpha 0.03, restore off) was picked on dev by the gate 3 rule and scored on test once. The paper default (alpha 1, restore on) loops on most answers, so only {a1_dev} of 672 dev and {a1_test} of 714 test complex answers are scored and its LPR is not a meaningful number. c06 is the blind 2B weight edit (a rank-1 change to the outputs of linear-attention layers 12 to 14). Its dev points are the editor's own full-dev scoring, the same numbers as its FINAL.md; its test points come from one run after the edit was frozen. On complex prompts c06 goes from {c_dev} on dev to {c_test} on test; every method is lower on test, where the baseline itself is {b_test} (dev {b_dev}). No single-method CI exists; paired CIs (c06 minus ReCoVeR, baseline, instruction at end and the random controls) and the seed 2 rows are in tables/partb_2b.md. Sources: runs/2026-11-11-gate5b-baseline/scores/baseline_{{dev,test}}.json, runs/2026-11-13-gate5b-instr-end/scores/instr_end_{{dev,test}}.json, runs/2026-11-14-gate5b-recover/scores/recover_{{a0.03_off,a1_on}}_{{dev,test}}.json, gate5b-workspace/work/c06/dev_scores.json, runs/2026-11-17-gate5b-eval/scores/final_test.json."""


def main():
    vals = Values()
    data = collect(vals)
    check_final(vals, data)
    path = os.path.join(FIG, "fig4_partb_2b.svg")
    draw(data, path)
    vals.write("fig4_partb_2b")
    a1 = data[3][1]
    write_text(os.path.join(FIG, "fig4_partb_2b.txt"),
               CAPTION.format(a1_dev=a1["dev"]["n_scored"], a1_test=a1["test"]["n_scored"],
                              c_dev=f1(data[-1][1]["dev"]["lpr"]), c_test=f1(data[-1][1]["test"]["lpr"]),
                              b_dev=f1(data[0][1]["dev"]["lpr"]), b_test=f1(data[0][1]["test"]["lpr"])))
    print("wrote", path)


if __name__ == "__main__":
    main()
