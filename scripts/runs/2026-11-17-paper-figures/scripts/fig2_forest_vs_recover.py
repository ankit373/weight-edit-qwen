"""fig 2: each editor minus tuned ReCoVeR, test complex LPR, 95% cluster-bootstrap ci, both unscored rules."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, lin, load, write_text  # noqa: E402

SUM = "runs/2026-11-13-gate5a-summary/out/results.json"
ROWS = [
    ("ed0", "recover", "editor 0 (gate 4, c02)"),
    ("ed1", "recover", "editor 1"),
    ("ed2", "recover", "editor 2"),
    ("ed3", "recover", "editor 3"),
    ("mean_editor", "recover", "mean of the 4 editors"),
    ("ed0_s2", "recover_s2", "editor 0, seed 2 (vs ReCoVeR seed 2)"),
]
RULES = [("drop", "unscored left out", "circle", True), ("fail", "unscored counted as fail", "square", False)]


def collect(vals):
    d = load(SUM)
    comp = {(c["a"], c["b"], c["fill"]): c for c in d["comparisons"]}
    boot = d["bootstrap"]
    data = []
    for a, b, label in ROWS:
        row = [label]
        for rule, *_ in RULES:
            diff, lo, hi = comp[(a, b, rule)]["complex_lpr"]
            fld = f"comparisons[a={a}, b={b}, fill={rule}].complex_lpr"
            vals.add(rule + " diff", label, diff, SUM, fld + "[0]")
            vals.add(rule + " lo", label, lo, SUM, fld + "[1]")
            vals.add(rule + " hi", label, hi, SUM, fld + "[2]")
            row.append((diff, lo, hi))
        data.append(row)
    return data, boot


def draw(data, boot, path):
    W, H = 900, 80 + len(data) * 52 + 10 + 72
    s = Svg(W, H)
    s.text(12, 22, "Editor minus tuned ReCoVeR (alpha 0.03), test complex LPR, Qwen3.5-0.8B", 14, weight="bold")
    s.text(12, 40, f"point = paired difference in points; bar = 95% cluster-bootstrap CI ({boot['B']} draws over "
                   f"split groups, 17 complex groups, seed {boot['seed']}). 714 prompts.", 11)
    x0, x1, lo_ax, hi_ax = 330, 870, -25, 5
    top = 80
    bottom = top + len(data) * 52 + 10
    for t in range(lo_ax, hi_ax + 1, 5):
        xt = lin(t, lo_ax, hi_ax, x0, x1)
        s.line(xt, top - 6, xt, bottom, stroke="#ccc", width=0.6, dash="2,3")
        s.line(xt, bottom, xt, bottom + 4)
        s.text(xt, bottom + 17, f"{t:+d}" if t else "0", 10, anchor="middle")
    xz = lin(0, lo_ax, hi_ax, x0, x1)
    s.line(xz, top - 10, xz, bottom, width=1.4)
    s.line(x0, bottom, x1, bottom)
    s.text((x0 + x1) / 2, bottom + 34, "editor minus ReCoVeR, complex LPR points (left of 0 = editor lower)", 11,
           anchor="middle")
    for i, row in enumerate(data):
        yc = top + i * 52 + 22
        if i == 4:
            s.line(12, yc - 26, x1, yc - 26, stroke="#999", width=0.6)
        s.text(12, yc + 4, row[0], 11)
        for j, ((rule, rname, shape, filled), (d, lo, hi)) in enumerate(zip(RULES, row[1:])):
            y = yc - 8 + j * 16
            xa, xb = lin(lo, lo_ax, hi_ax, x0, x1), lin(hi, lo_ax, hi_ax, x0, x1)
            s.line(xa, y, xb, y, width=1.4, dash=None if filled else "4,2")
            s.line(xa, y - 4, xa, y + 4, width=1.2)
            s.line(xb, y - 4, xb, y + 4, width=1.2)
            s.marker(lin(d, lo_ax, hi_ax, x0, x1), y, shape, filled=filled, r=4)
            s.text(318, y + 4, f"{d:+.1f} [{lo:+.1f}, {hi:+.1f}]", 9.5, anchor="end", fill="#222")
    ly = H - 22
    s.marker(20, ly - 4, "circle", True, 4)
    s.line(10, ly - 4, 30, ly - 4, width=1.4)
    s.text(38, ly, "unscored answers left out (as reported)", 10.5)
    s.marker(320, ly - 4, "square", False, 4)
    s.line(308, ly - 4, 332, ly - 4, width=1.4, dash="4,2")
    s.text(340, ly, "unscored answers counted as fail, both sides", 10.5)
    s.save(path)


CAPTION = """Figure 2. Paired difference to the tuned ReCoVeR (alpha 0.03, restore on) on test cross-lingual complex LPR, Qwen3.5-0.8B, 714 prompts. Each row shows two rules for answers the scorer cannot check: left out (filled circle, solid bar) and counted as fail for both methods (open square, dashed bar). Bars are 95% cluster-bootstrap intervals: {B} draws, groups of the v2 split drawn with replacement within each dataset (17 complex groups), the same draw for both methods, seed {seed}. The mean row averages the four editors on each draw, so its interval covers prompt sampling only, not the spread between editors. Only editor 0 has a second sampling seed. Source: runs/2026-11-13-gate5a-summary/out/results.json (comparisons, complex_lpr)."""


def main():
    vals = Values()
    data, boot = collect(vals)
    path = os.path.join(FIG, "fig2_forest_vs_recover.svg")
    draw(data, boot, path)
    vals.write("fig2_forest_vs_recover")
    write_text(os.path.join(FIG, "fig2_forest_vs_recover.txt"), CAPTION.format(B=boot["B"], seed=boot["seed"]))
    print("wrote", path)


if __name__ == "__main__":
    main()
