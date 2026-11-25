"""fig 1: 0.8B test cross-lingual complex LPR per method, unscored dropped (left) and counted as fail (right)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, f1, lin, load, score_row, write_text  # noqa: E402

SUM = "runs/2026-11-13-gate5a-summary/out/results.json"
A1 = "runs/2026-11-06-gate3-run/scores/recover_a1_on_test.json"

# (key in results.json point, label, group); None key = read from the gate 3 score file
ROWS = [
    ("baseline", "baseline (gate 1)", "reference"),
    ("instr_end", "instruction at end", "reference"),
    ("recover", "ReCoVeR, tuned (alpha 0.03, restore on)", "ReCoVeR"),
    (None, "ReCoVeR, paper default (alpha 1)", "ReCoVeR"),
    ("ed0", "editor 0 (gate 4, c02)", "blind editors"),
    ("ed1", "editor 1", "blind editors"),
    ("ed2", "editor 2", "blind editors"),
    ("ed3", "editor 3", "blind editors"),
    ("ed0_rand1001", "random, editor 0, seed 1001", "random-edit controls"),
    ("ed0_rand1002", "random, editor 0, seed 1002", "random-edit controls"),
    ("ed0_rand1003", "random, editor 0, seed 1003", "random-edit controls"),
    ("ed1_rand1001", "random, editor 1, seed 1001", "random-edit controls"),
    ("ed2_rand1002", "random, editor 2, seed 1002", "random-edit controls"),
    ("ed3_rand1003", "random, editor 3, seed 1003", "random-edit controls"),
]
SHAPE = {"reference": "circle", "ReCoVeR": "square", "blind editors": "triangle", "random-edit controls": "diamond"}


def collect(vals):
    res = load(SUM)["point"]
    data = []
    for key, label, grp in ROWS:
        if key is None:
            r = score_row(A1, "complex_prompts")
            drop = vals.add("drop", label, r["lpr"], A1, "complex_prompts/all lpr")
            fail = vals.add("fail", label, None, "not computed", "no per-prompt rows for alpha 1")
            n = vals.add("n_scored", label, r["n_scored"], A1, "complex_prompts/all n_scored")
        else:
            pt = res[key]
            drop = vals.add("drop", label, pt["drop"]["complex_lpr"], SUM, f"point.{key}.drop.complex_lpr")
            fail = vals.add("fail", label, pt["fail"]["complex_lpr"], SUM, f"point.{key}.fail.complex_lpr")
            n = vals.add("n_scored", label, pt["scored"]["complex"], SUM, f"point.{key}.scored.complex")
        data.append((label, grp, drop, fail, n))
    return data


def draw(data, path):
    W, top, rowh = 1000, 92, 24
    groups = []
    for d in data:
        if not groups or groups[-1][0] != d[1]:
            groups.append((d[1], []))
        groups[-1][1].append(d)
    H = top + sum(len(g[1]) * rowh + 22 for g in groups) + 60
    s = Svg(W, H)
    s.text(12, 22, "Qwen3.5-0.8B, test split, cross-lingual complex prompts (714 prompts, seed 1)", 14, weight="bold")
    s.text(12, 40, "dot = complex LPR (%), mean over the 14 language cells. n = answers the scorer could check, of 714.", 11)
    s.text(12, 56, "no per-method confidence interval was computed; paired differences with 95% CIs are in figure 2.", 11)
    lab_x = 12
    panels = [("unscored answers left out (as reported)", 330, 640, 2),
              ("unscored answers counted as fail", 680, 990, 3)]
    lo, hi = 50, 100
    for title, x0, x1, _ in panels:
        s.text((x0 + x1) / 2, top - 14, title, 12, anchor="middle", weight="bold")
    y = top
    for gname, rows in groups:
        y += 16
        s.text(lab_x, y, gname, 11, weight="bold")
        y += 6
        for label, grp, drop, fail, n in rows:
            yc = y + rowh / 2
            s.text(lab_x + 8, yc + 4, label, 11)
            s.text(318, yc + 4, f"n={n}", 10, anchor="end", fill="#444")
            for (title, x0, x1, idx), v in zip(panels, (drop, fail)):
                s.line(x0, yc, x1, yc, stroke="#ddd", width=1)
                if v is None:
                    s.text((x0 + x1) / 2, yc + 4, "not computed", 10, anchor="middle", fill="#444", italic=True)
                    continue
                x = lin(v, lo, hi, x0, x1)
                s.marker(x, yc, SHAPE[grp], filled=grp != "random-edit controls")
                s.text(x + 9, yc + 4, f1(v), 10)
            y += rowh
    bottom = y + 6
    for title, x0, x1, _ in panels:
        s.line(x0, bottom, x1, bottom)
        for t in range(lo, hi + 1, 10):
            xt = lin(t, lo, hi, x0, x1)
            s.line(xt, top - 4, xt, bottom, stroke="#bbb", width=0.6, dash="2,3")
            s.line(xt, bottom, xt, bottom + 4)
            s.text(xt, bottom + 16, str(t), 10, anchor="middle")
        s.text((x0 + x1) / 2, bottom + 32, "complex LPR, % (axis starts at 50)", 11, anchor="middle")
    s.save(path)


def main():
    vals = Values()
    data = collect(vals)
    path = os.path.join(FIG, "fig1_main_08b.svg")
    draw(data, path)
    vals.write("fig1_main_08b")
    a1_n = [d[4] for d in data if d[2] is not None and d[3] is None][0]
    write_text(os.path.join(FIG, "fig1_main_08b.txt"), CAPTION.format(a1_n=a1_n))
    print("wrote", path)


CAPTION = """Figure 1. Test cross-lingual complex LPR on Qwen3.5-0.8B, sampling seed 1, 714 prompts (51 per language). Left: answers with no line the scorer can check are left out, as in the reported numbers. Right: those answers count as fails. n is the number of scored answers. Editor 0 is the gate 4 edit (c02); editors 1 to 3 are the part A runs. Each random-edit control changes the same tensors with the same number of entries and the same Frobenius norm as its editor's edit. The ReCoVeR paper default (alpha 1) produces mostly looping text, so only {a1_n} of 714 answers are scored and its LPR is not a meaningful number; it has no fail-rule value because no per-prompt rows were made for it. No per-method interval was computed; the 95% cluster-bootstrap intervals of the paired differences are in figure 2. Sources: runs/2026-11-13-gate5a-summary/out/results.json (point.*), runs/2026-11-06-gate3-run/scores/recover_a1_on_test.json."""

if __name__ == "__main__":
    main()
