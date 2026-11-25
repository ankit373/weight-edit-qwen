"""part C figure helpers. reuses the 2026-11-17 readers and svg code; only the output folder and run folder are new."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(OUT))
_spec = importlib.util.spec_from_file_location(
    "fig1117_common", os.path.join(ROOT, "runs/2026-11-17-paper-figures/scripts/common.py"))
_old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_old)

LANGS, Svg, Values, esc, lin = _old.LANGS, _old.Svg, _old.Values, _old.esc, _old.lin
load, md_table, p, write_text = _old.load, _old.md_table, _old.p, _old.write_text

FIG = os.path.join(OUT, "figures")
TAB = os.path.join(OUT, "tables")
RUN = "runs/2026-11-22-partc-run"
JUDGE = "runs/2026-11-24-judge-2b/analysis/results.json"

EDITS_08 = [("c02_nb_L15u1047_k2", "editor 0 (c02)"), ("h5_a2_n5", "editor 1"),
            ("mix21_22b0.75_23b0.5", "editor 2"), ("combo_a14_b14", "editor 3")]
EDITS_2B = [("c06", "c06")]


def stats_rel(model, name):
    """stats.json of one part C set. XL-AlpacaEval scores live under scores/nc-sa/."""
    if name == "xl-alpacaeval":
        return f"{RUN}/scores/nc-sa/xl-alpacaeval/{model}/stats.json"
    return f"{RUN}/scores/{model}/{name}/stats.json"


def forest(path, title, subtitle, rows, lo_ax, hi_ax, step, xlabel, legend, band=None, extra_lines=()):
    """horizontal interval plot. rows: ("head", text) or ("row", label, diff, lo, hi, shape, filled, note[, signed])."""
    rh, top, x0, x1 = 19, 62, 360, 860
    n = len(rows)
    bottom = top + n * rh + 8
    s = Svg(900, bottom + 70)
    s.text(12, 22, title, 14, weight="bold")
    s.text(12, 40, subtitle, 10.5)
    if band:
        xa, xb = lin(band[0], lo_ax, hi_ax, x0, x1), lin(band[1], lo_ax, hi_ax, x0, x1)
        s.rect(xa, top - 6, xb - xa, bottom - top + 6, fill="#eeeeee", stroke="none", width=0)
    t = lo_ax
    while t <= hi_ax + 1e-9:
        xt = lin(t, lo_ax, hi_ax, x0, x1)
        s.line(xt, top - 6, xt, bottom, stroke="#ccc", width=0.6, dash="2,3")
        s.text(xt, bottom + 15, f"{t:+g}" if t else "0", 10, anchor="middle")
        t += step
    for v in extra_lines:
        xv = lin(v, lo_ax, hi_ax, x0, x1)
        s.line(xv, top - 6, xv, bottom, stroke="#555", width=0.9, dash="5,3")
    xz = lin(0, lo_ax, hi_ax, x0, x1)
    s.line(xz, top - 10, xz, bottom, width=1.4)
    s.line(x0, bottom, x1, bottom)
    s.text((x0 + x1) / 2, bottom + 31, xlabel, 11, anchor="middle")
    for i, r in enumerate(rows):
        y = top + i * rh + rh / 2
        if r[0] == "head":
            s.text(12, y + 4, r[1], 11, weight="bold")
            s.line(12, y - rh / 2 + 1, x1, y - rh / 2 + 1, stroke="#999", width=0.5)
            continue
        _, label, d, lo, hi, shape, filled, note = r[:8]
        sg = "+" if len(r) < 9 or r[8] else ""
        s.text(24, y + 4, label, 10.5)
        s.text(x0 - 8, y + 4, f"{d:{sg}.1f} [{lo:{sg}.1f}, {hi:{sg}.1f}]{note}", 9.5, anchor="end", fill="#222")
        xa, xb = lin(max(lo, lo_ax), lo_ax, hi_ax, x0, x1), lin(min(hi, hi_ax), lo_ax, hi_ax, x0, x1)
        s.line(xa, y, xb, y, width=1.4, dash=None if filled else "4,2")
        s.line(xa, y - 4, xa, y + 4, width=1.2)
        s.line(xb, y - 4, xb, y + 4, width=1.2)
        s.marker(lin(d, lo_ax, hi_ax, x0, x1), y, shape, filled=filled, r=4)
    lx, ly = 12, bottom + 54
    for shape, filled, text in legend:
        s.marker(lx + 6, ly - 4, shape, filled, 4)
        s.text(lx + 16, ly, text, 10)
        lx += 24 + 6.2 * len(text)
    s.save(path)
