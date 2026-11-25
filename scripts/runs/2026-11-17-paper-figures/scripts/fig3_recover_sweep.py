"""fig 3: ReCoVeR alpha sweep on dev, both models. dev complex LPR and loop rate vs alpha, restore on / off."""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, f1, lin, load, read_lines, score_row, write_text  # noqa: E402

MODELS = {
    "0.8B": {
        "title": "Qwen3.5-0.8B (gate 3)",
        "run": "runs/2026-11-06-gate3-run",
        "grid672": ["0.02", "0.03", "0.05"],
        "base_lpr": "runs/2026-11-06-gate3-run/scores/baseline_devcx.json",
        "screen": ("queue", "runs/2026-11-06-gate3-run/logs/queue.log"),
        "winner": ("0.03", "on"),
    },
    "2B": {
        "title": "Qwen3.5-2B (part B, B4)",
        "run": "runs/2026-11-14-gate5b-recover",
        "grid672": ["0.01", "0.02", "0.03", "0.05", "0.1"],
        "base_lpr": "runs/2026-11-11-gate5b-baseline/scores/baseline_dev.json",
        "screen": ("manual", "runs/2026-11-14-gate5b-recover/logs/screen_loops_manual.txt"),
        "threshold_log": "runs/2026-11-14-gate5b-recover/logs/steps.log",
        "winner": ("0.03", "off"),
    },
}
SCREEN_N = 98
ALPHA_MIN, ALPHA_MAX = 0.007, 5.0


def screen_counts(m):
    kind, rel = m["screen"]
    out, thr = {}, None
    if kind == "queue":
        for ln in read_lines(rel):
            g = re.match(r"SCREEN recover_a([\d.]+)_(on|off)_devcx loops=(\d+) \(certain fail at >= (\d+)\)", ln)
            if g:
                out[(g[1], g[2])] = int(g[3])
                thr = int(g[4])
    else:
        for ln in read_lines(rel):
            g = re.match(r"recover_a([\d.]+)_(on|off)_devcx rows=(\d+) loops=(\d+)", ln)
            if g:
                assert int(g[3]) == SCREEN_N
                out[(g[1], g[2])] = int(g[4])
        for ln in read_lines(m["threshold_log"]):
            g = re.search(r"certain fail at >= (\d+)", ln)
            if g:
                thr = int(g[1])
    return out, thr, rel


def collect(name, m, vals):
    run = m["run"]
    pts672, screen, fulldev = [], [], []
    base_loop = None
    for a in m["grid672"]:
        for r in ("on", "off"):
            sc = f"{run}/scores/recover_a{a}_{r}_devcx.json"
            gd = f"{run}/guard/recover_a{a}_{r}_devcx.guard.json"
            row = score_row(sc, "complex_prompts")
            g = load(gd)
            lab = f"alpha {a} restore {r}"
            vals.add(f"{name} 672 lpr", lab, row["lpr"], sc, "complex_prompts/all lpr")
            vals.add(f"{name} 672 n_scored", lab, row["n_scored"], sc, "complex_prompts/all n_scored")
            vals.add(f"{name} 672 loop_pct", lab, g["new"]["loop_pct"], gd, "new.loop_pct")
            vals.add(f"{name} 672 pass", lab, g["pass_1_to_3"], gd, "pass_1_to_3")
            pts672.append((float(a), r, row["lpr"], g["new"]["loop_pct"], g["pass_1_to_3"], row["n_scored"]))
            base_loop = vals.add(f"{name} base 672", "baseline loop_pct", g["baseline"]["loop_pct"], gd,
                                 "baseline.loop_pct")
    counts, thr, src = screen_counts(m)
    for (a, r), n in sorted(counts.items(), key=lambda kv: (float(kv[0][0]), kv[0][1])):
        if a in m["grid672"]:
            continue
        pct = 100.0 * n / SCREEN_N
        vals.add(f"{name} screen loops", f"alpha {a} restore {r}", n, src, f"loops of {SCREEN_N}")
        screen.append((float(a), r, pct, n >= thr))
    sc = f"{run}/scores/recover_a1_on_dev.json"
    gd = f"{run}/guard/recover_a1_on_dev.guard.json"
    row = score_row(sc, "complex_prompts")
    if name == "0.8B":
        sc = f"{run}/scores/recover_a1_on_devcx.json"
        row = score_row(sc, "complex_prompts")
    g = load(gd)
    vals.add(f"{name} paper default lpr", "alpha 1 restore on", row["lpr"], sc, "complex_prompts/all lpr")
    vals.add(f"{name} paper default n_scored", "alpha 1 restore on", row["n_scored"], sc, "complex_prompts/all n_scored")
    vals.add(f"{name} paper default loop_pct (all dev)", "alpha 1 restore on", g["new"]["loop_pct"], gd, "new.loop_pct")
    vals.add(f"{name} paper default pass", "alpha 1 restore on", g["pass_1_to_3"], gd, "pass_1_to_3")
    fulldev.append((1.0, "on", row["lpr"], g["new"]["loop_pct"], g["pass_1_to_3"], row["n_scored"], row["n"]))
    base = score_row(m["base_lpr"], "complex_prompts")
    vals.add(f"{name} base lpr", "baseline dev complex", base["lpr"], m["base_lpr"], "complex_prompts/all lpr")
    vals.add(f"{name} screen threshold", "certain fail at >=", thr, src if name == "0.8B" else m["threshold_log"],
             "SCREEN line")
    return dict(p672=pts672, screen=screen, full=fulldev, base_loop=base_loop, base_lpr=base["lpr"], thr=thr)


def xa(alpha, x0, x1):
    return lin(math.log10(alpha), math.log10(ALPHA_MIN), math.log10(ALPHA_MAX), x0, x1)


def ysq(v, y0, y1):
    return lin(math.sqrt(max(v, 0.0)), 0.0, 10.0, y0, y1)


def x_axis(s, x0, x1, y):
    s.line(x0, y, x1, y)
    for a in (0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1, 2, 4):
        x = xa(a, x0, x1)
        s.line(x, y, x, y + 4)
        s.text(x, y + 16, f"{a:g}", 10, anchor="middle")
    s.text((x0 + x1) / 2, y + 32, "steering strength alpha (log scale)", 11, anchor="middle")


def fail_mark(s, x, y):
    s.marker(x, y, "cross", r=7, color="#555")


def panel(s, name, m, d, x0, x1):
    s.text((x0 + x1) / 2, 74, m["title"], 13, anchor="middle", weight="bold")
    # top: dev complex LPR
    yt0, yt1, lo, hi = 330, 100, 60, 100
    s.rect(x0, yt1, x1 - x0, yt0 - yt1, stroke="#888", width=0.8)
    for t in range(lo, hi + 1, 10):
        y = lin(t, lo, hi, yt0, yt1)
        s.line(x0 - 4, y, x0, y)
        s.text(x0 - 7, y + 4, str(t), 10, anchor="end")
        s.line(x0, y, x1, y, stroke="#e2e2e2", width=0.6)
    s.text(x0 - 36, (yt0 + yt1) / 2, "dev complex LPR, %", 11, anchor="middle", rotate=-90)
    yb = lin(d["base_lpr"], lo, hi, yt0, yt1)
    s.line(x0, yb, x1, yb, dash="6,3", width=1)
    s.text(x1 - 4, yb - 5, f"baseline {f1(d['base_lpr'])}", 10, anchor="end")
    for r, dash in (("on", None), ("off", "5,3")):
        pts = sorted(p for p in d["p672"] if p[1] == r)
        s.polyline([(xa(p[0], x0, x1), lin(p[2], lo, hi, yt0, yt1)) for p in pts], width=1.2, dash=dash)
    for a, r, lpr, loop, ok, n in d["p672"]:
        x, y = xa(a, x0, x1), lin(lpr, lo, hi, yt0, yt1)
        s.marker(x, y, "circle", filled=(r == "on"))
        if not ok:
            fail_mark(s, x, y)
        if (f"{a:g}", r) == (f"{float(m['winner'][0]):g}", m["winner"][1]):
            s.text(x, y - 12 if r == "on" else y + 20, "winner", 10, anchor="middle", weight="bold")
    for a, r, lpr, loop, ok, n, ntot in d["full"]:
        x, y = xa(a, x0, x1), lin(lpr, lo, hi, yt0, yt1)
        s.marker(x, y, "diamond", filled=True)
        if not ok:
            fail_mark(s, x, y)
        s.text(x - 10, y + 22, f"paper default: {n} of {ntot} scored", 9.5, anchor="middle")
    s.text(x1 - 4, yt1 + 14, "alpha 0.1 and up stopped at the screen" if name == "0.8B"
           else "alpha 0.25 and up stopped at the screen", 9.5, anchor="end", fill="#333")
    # bottom: loops
    yl0, yl1 = 610, 380
    s.rect(x0, yl1, x1 - x0, yl0 - yl1, stroke="#888", width=0.8)
    for t in (0, 1, 2, 5, 10, 25, 50, 100):
        y = ysq(t, yl0, yl1)
        s.line(x0 - 4, y, x0, y)
        s.text(x0 - 7, y + 4, str(t), 10, anchor="end")
        s.line(x0, y, x1, y, stroke="#e2e2e2", width=0.6)
    s.text(x0 - 36, (yl0 + yl1) / 2, "looping answers, % (sqrt scale)", 11, anchor="middle", rotate=-90)
    lim = d["base_loop"] + 2.0
    y = ysq(lim, yl0, yl1)
    s.line(x0, y, x1, y, dash="6,3", width=1.1)
    s.text(x1 - 4, y - 4, f"guard limit, 672 prompts: base {d['base_loop']:.2f}% + 2 pts", 9.5, anchor="end")
    thr_pct = 100.0 * d["thr"] / SCREEN_N
    y = ysq(thr_pct, yl0, yl1)
    s.line(x0, y, x1, y, dash="1,3", width=1.3)
    s.text(x0 + 4, y - 4, f"screen stop: {d['thr']} or more of {SCREEN_N} loop", 9.5)
    for r, dash in (("on", None), ("off", "5,3")):
        pts = sorted(p for p in d["p672"] if p[1] == r)
        s.polyline([(xa(p[0], x0, x1), ysq(p[3], yl0, yl1)) for p in pts], width=1.2, dash=dash)
    for a, r, lpr, loop, ok, n in d["p672"]:
        x, y = xa(a, x0, x1), ysq(loop, yl0, yl1)
        s.marker(x, y, "circle", filled=(r == "on"))
        if not ok:
            fail_mark(s, x, y)
    for a, r, pct, failed in d["screen"]:
        x, y = xa(a, x0, x1), ysq(pct, yl0, yl1)
        s.marker(x + (-4 if r == "on" else 4), y, "triangle", filled=(r == "on"))
        if failed:
            fail_mark(s, x + (-4 if r == "on" else 4), y)
    for a, r, lpr, loop, ok, n, ntot in d["full"]:
        x, y = xa(a, x0, x1), ysq(loop, yl0, yl1)
        s.marker(x, y, "diamond", filled=True)
        if not ok:
            fail_mark(s, x, y)
    x_axis(s, x0, x1, yl0)


def legend(s, y):
    items = [("circle", True, "restore on, 672 dev complex prompts"),
             ("circle", False, "restore off, 672 dev complex prompts"),
             ("triangle", True, "98-prompt loop screen (filled on, open off)"),
             ("diamond", True, "paper default alpha 1, restore on, all-dev run"),
             ("cross", True, "fails the guard (loops; on 2B alpha 1 also NLL)")]
    x = 20
    for i, (shape, filled, text) in enumerate(items):
        xx = x + (i % 3) * 330
        yy = y + (i // 3) * 18
        s.marker(xx, yy - 4, shape, filled=filled, r=4.5 if shape != "cross" else 5)
        s.text(xx + 12, yy, text, 10.5)


CAPTION = """Figure 3. ReCoVeR steering strength sweep on the dev split, both models, one sampling seed. Top: dev cross-lingual complex LPR (672 prompts, unscored answers left out). Bottom: share of answers that loop (distinct 4-gram ratio below 0.5), on a square-root scale. Circles are settings run on all 672 dev complex prompts (filled: norm restore on, open: off); triangles are the 98-prompt screen that stops a setting once it has too many loops to pass on the 672 ({thr08} of 98 on 0.8B, {thr2} of 98 on 2B); diamonds are the paper default (alpha 1, restore on) run on all of dev, whose loop rate is over all 2086 dev prompts. A cross marks a setting that fails the guard. The dashed line in the bottom panels is the loop limit on the 672 prompts (baseline plus 2 points). The paper default has few scored answers ({n08} of 672 on 0.8B, {n2} of 672 on 2B) because most answers are loops of short tokens, so its LPR point is not a meaningful number. The 0.8B grid was extended down to 0.02 after the first grid failed; the 2B grid was fixed in advance from 0.01 to 2. The 2B screen loop counts were recounted by hand after a queue bug (runs/2026-11-13-gate5-chain/README.md). Winner by the tie rule: 0.8B alpha 0.03 restore on, 2B alpha 0.03 restore off. Sources: score and guard files of runs/2026-11-06-gate3-run and runs/2026-11-14-gate5b-recover, listed in fig3_recover_sweep.values.tsv."""


def main():
    vals = Values()
    data = {k: collect(k, m, vals) for k, m in MODELS.items()}
    s = Svg(1060, 720)
    s.text(12, 22, "ReCoVeR alpha sweep on dev: language fix vs looping", 14, weight="bold")
    s.text(12, 40, "one seed. top: dev complex LPR, 672 prompts. bottom: looping answers. cross = fails the guard.", 11)
    panel(s, "0.8B", MODELS["0.8B"], data["0.8B"], 90, 510)
    panel(s, "2B", MODELS["2B"], data["2B"], 610, 1030)
    legend(s, 680)
    path = os.path.join(FIG, "fig3_recover_sweep.svg")
    s.save(path)
    vals.write("fig3_recover_sweep")
    write_text(os.path.join(FIG, "fig3_recover_sweep.txt"), CAPTION.format(
        thr08=data["0.8B"]["thr"], thr2=data["2B"]["thr"],
        n08=data["0.8B"]["full"][0][5], n2=data["2B"]["full"][0][5]))
    print("wrote", path)


if __name__ == "__main__":
    main()
