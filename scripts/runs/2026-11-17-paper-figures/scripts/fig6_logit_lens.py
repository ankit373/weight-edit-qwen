"""fig 6: logit lens, 0.8B and 2B side by side. target vs english probability mass per layer, passed vs full failures.

redraws the pooled non-latin rows of the gate 2 and B2 lens tables (the per-language svgs there stay as they are).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, lin, read_lines, write_text  # noqa: E402

SRC = {
    "Qwen3.5-0.8B (gate 2)": "runs/2026-11-06-gate2-diagnosis/scores/step2_layers_nonlatin.tsv",
    "Qwen3.5-2B (B2)": "runs/2026-11-13-gate5b-diagnosis/scores/step2_layers_nonlatin.tsv",
}
LANGSET, MEASURE = "nonlatin6", "mass"


def collect(vals):
    out = {}
    for title, rel in SRC.items():
        lines = read_lines(rel)
        head = lines[0].split("\t")
        cols = [c for c in head if c.startswith("L")]
        series = {}
        for ln in lines[1:]:
            f = dict(zip(head, ln.split("\t")))
            if f["langs"] != LANGSET or f["measure"] != MEASURE:
                continue
            ys = [float(f[c]) for c in cols]
            key = (f["group"], f["series"])
            series[key] = (int(f["n"]), ys)
            for c, y in zip(cols, ys):
                vals.add(f"{title} {f['group']} {f['series']}", c, y, rel, f"{LANGSET}/{MEASURE}/{f['group']}/{f['series']}/{c}")
            vals.add(f"{title} {f['group']} n", "n", int(f["n"]), rel, "n")
        out[title] = ([int(c[1:]) for c in cols], series)
    return out


STYLE = {("ok", "target"): (None, True), ("ok", "english"): ("5,3", True),
         ("full", "target"): (None, False), ("full", "english"): ("5,3", False)}


def panel(s, title, layers, series, x0, x1):
    y0, y1 = 400, 90
    s.text((x0 + x1) / 2, 76, title, 13, anchor="middle", weight="bold")
    s.rect(x0, y1, x1 - x0, y0 - y1, stroke="#888", width=0.8)
    for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        y = lin(t, 0, 1, y0, y1)
        s.line(x0 - 4, y, x0, y)
        s.text(x0 - 7, y + 4, f"{t:g}", 10, anchor="end")
        s.line(x0, y, x1, y, stroke="#e2e2e2", width=0.6)
    for L in (1, 4, 8, 12, 16, 20, 24):
        x = lin(L, 1, 24, x0, x1)
        s.line(x, y0, x, y0 + 4)
        s.text(x, y0 + 16, str(L), 10, anchor="middle")
    s.text((x0 + x1) / 2, y0 + 32, "layer (lens applied after each decoder layer)", 11, anchor="middle")
    s.text(x0 - 38, (y0 + y1) / 2, "probability mass", 11, anchor="middle", rotate=-90)
    for key, (dash, filled) in STYLE.items():
        if key not in series:
            continue
        n, ys = series[key]
        pts = [(lin(L, 1, 24, x0, x1), lin(y, 0, 1, y0, y1)) for L, y in zip(layers, ys)]
        s.polyline(pts, width=1.3, dash=dash)
        for x, y in pts:
            s.marker(x, y, "circle", filled=filled, r=2.8)
    n_ok, n_full = series[("ok", "target")][0], series[("full", "target")][0]
    s.text(x0 + 8, y1 + 16, f"passed n={n_ok}, full failures n={n_full}", 10.5)


def main():
    vals = Values()
    data = collect(vals)
    s = Svg(1000, 520)
    s.text(12, 22, "Logit lens at the first content token, non-Latin targets (ar, hi, ja, ko, ru, zh), dev", 14, weight="bold")
    s.text(12, 40, "mass on target-script tokens (solid) and on Latin-script tokens (dashed), passed answers (filled) "
                   "vs full failures (open)", 11)
    (t1, d1), (t2, d2) = list(data.items())
    panel(s, t1, d1[0], d1[1], 80, 470)
    panel(s, t2, d2[0], d2[1], 580, 970)
    items = [(None, True, "target script, passed"), ("5,3", True, "Latin script, passed"),
             (None, False, "target script, full failure"), ("5,3", False, "Latin script, full failure")]
    for i, (dash, filled, lab) in enumerate(items):
        x, y = 30 + (i % 2) * 300, 470 + (i // 2) * 20
        s.line(x - 12, y, x + 12, y, width=1.3, dash=dash)
        s.marker(x, y, "circle", filled=filled, r=3)
        s.text(x + 20, y + 4, lab, 10.5)
    path = os.path.join(FIG, "fig6_logit_lens.svg")
    s.save(path)
    vals.write("fig6_logit_lens")
    write_text(os.path.join(FIG, "fig6_logit_lens.txt"), CAPTION.format(
        n08=d1[1][("ok", "target")][0], f08=d1[1][("full", "target")][0],
        n2=d2[1][("ok", "target")][0], f2=d2[1][("full", "target")][0], s08=SRC[t1], s2=SRC[t2]))
    print("wrote", path)


CAPTION = """Figure 6. Logit lens on the unedited models, teacher-forced on their own baseline dev answers (gate 1 for 0.8B, B1 for 2B), at the position that predicts the first content token of the answer (the first answer token with letters). Dev prompts with a non-Latin target language (ar, hi, ja, ko, ru, zh), pooled. For layers 1 to 23 the residual after the layer goes through the final norm and the tied output head; layer 24 is the model's own output. The plot shows the mean probability mass on tokens of the target script (solid) and on Latin-script tokens (dashed), which for these targets stands for English. Filled markers: passed answers (0.8B n={n08}, 2B n={n2}); open markers: answers fully in the wrong language (0.8B n={f08}, 2B n={f2}). In 0.8B the two groups split at layer 20, where the failures move to more Latin mass; in 2B the failures already carry more Latin mass from about layer 17 and the gap widens at layer 20. In both models the target script gets most of its mass only in the last two to three layers of passed answers and never comes up in failures. Sources: {s08}, {s2} (rows nonlatin6, mass). Per-language plots: lens_mass_content_token.svg in the same two folders."""

if __name__ == "__main__":
    main()
