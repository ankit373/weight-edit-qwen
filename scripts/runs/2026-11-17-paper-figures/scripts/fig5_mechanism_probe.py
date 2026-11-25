"""fig 5: what part A editors 2 and 3 measured at the last prompt position, per layer (0.8B, dev complex).

reads the editors' own analysis files (read only). editor 1 recorded a margin probe with no per-layer numbers,
so it is not in the figure; its prose numbers are quoted in the caption with file and line.
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, Svg, Values, lin, load, p, read_lines, write_text  # noqa: E402

ED2 = "gate5-workspace-2/work/acts/analyze_dir_base.json"
ED2_MD = "gate5-workspace-2/EDITOR.md"
ED3 = "gate5-workspace-3/work/p1/analysis.json"
ED3_META = "gate5-workspace-3/work/p1/meta.jsonl"
ED3_MD = "gate5-workspace-3/EDITOR.md"
ED1_MD = "gate5-workspace-1/FINAL.md"


def grep(rel, pattern):
    for i, ln in enumerate(read_lines(rel), 1):
        g = re.search(pattern, ln)
        if g:
            return i, g
    raise KeyError((rel, pattern))


def collect(vals):
    e2 = load(ED2)["layers"]
    e3 = load(ED3)["layers"]
    layers = sorted(int(k) for k in e2)
    ln2, g2 = grep(ED2_MD, r"\((\d+) full, (\d+) pass\)")
    ln3, g3 = grep(ED3_MD, r"(\d+) pass / (\d+) fail")
    n_acc3 = 0
    with open(p(ED3_META), encoding="utf-8") as f:
        for line in f:
            if json.loads(line)["source"] == "complex_prompts":
                n_acc3 += 1
    vals.add("n", "editor 2 full failures", int(g2[1]), ED2_MD, f"line {ln2}")
    vals.add("n", "editor 2 passes", int(g2[2]), ED2_MD, f"line {ln2}")
    vals.add("n", "editor 3 passes", int(g3[1]), ED3_MD, f"line {ln3}")
    vals.add("n", "editor 3 fails", int(g3[2]), ED3_MD, f"line {ln3}")
    vals.add("n", "editor 3 accuracy rows (complex)", n_acc3, ED3_META, "rows with source complex_prompts")
    rows = []
    for L in layers:
        a = e2[str(L)]
        b = e3[str(L)]
        acc_p = vals.add("ed2 acc pass", f"L{L}", a["lang_probe_acc_pass"], ED2, f"layers.{L}.lang_probe_acc_pass")
        acc_f = vals.add("ed2 acc full", f"L{L}", a["lang_probe_acc_full"], ED2, f"layers.{L}.lang_probe_acc_full")
        acc3 = vals.add("ed3 acc", f"L{L}", b["acc"], ED3, f"layers.{L}.acc")
        pp, pf = b["proj_pass"], b["proj_fail"]
        ratio = None
        if isinstance(pp, float) and isinstance(pf, float) and not (math.isnan(pp) or math.isnan(pf)) and pp:
            vals.add("ed3 proj pass", f"L{L}", pp, ED3, f"layers.{L}.proj_pass")
            vals.add("ed3 proj fail", f"L{L}", pf, ED3, f"layers.{L}.proj_fail")
            ratio = vals.add("ed3 fail/pass ratio (derived)", f"L{L}", pf / pp, ED3, "proj_fail / proj_pass")
        rows.append((L, acc_p, acc_f, acc3, ratio))
    ns = dict(e2_full=int(g2[1]), e2_pass=int(g2[2]), e3_pass=int(g3[1]), e3_fail=int(g3[2]), e3_acc=n_acc3)
    return rows, ns


def frame(s, x0, x1, y0, y1, ylab, yticks):
    s.rect(x0, y1, x1 - x0, y0 - y1, stroke="#888", width=0.8)
    for t in yticks:
        y = lin(t, yticks[0], yticks[-1], y0, y1)
        s.line(x0 - 4, y, x0, y)
        s.text(x0 - 7, y + 4, f"{t:g}", 10, anchor="end")
        s.line(x0, y, x1, y, stroke="#e2e2e2", width=0.6)
    for L in range(0, 25, 4):
        x = lin(L, 0, 24, x0, x1)
        s.line(x, y0, x, y0 + 4)
        s.text(x, y0 + 16, str(L), 10, anchor="middle")
    s.text((x0 + x1) / 2, y0 + 32, "layer (hidden_states index; 0 = embeddings)", 11, anchor="middle")
    s.text(x0 - 38, (y0 + y1) / 2, ylab, 11, anchor="middle", rotate=-90)


def draw(rows, ns, path):
    s = Svg(1000, 540)
    s.text(12, 22, "Is the asked-for language present at the answer position? (Qwen3.5-0.8B, dev complex, gate 1 answers)", 14,
           weight="bold")
    s.text(12, 40, "numbers recorded by part A editors 2 and 3 in their workspaces; the two probes are built differently "
                   "(see caption).", 11)
    x0, x1, y0, y1 = 80, 470, 420, 90
    frame(s, x0, x1, y0, y1, "nearest-centroid accuracy", [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    s.text((x0 + x1) / 2, 78, "language-ID accuracy at the last prompt position", 12, anchor="middle", weight="bold")
    series = [(1, True, None, "circle", f"editor 2, passed answers (n={ns['e2_pass']})"),
              (2, False, "5,3", "circle", f"editor 2, full failures (n={ns['e2_full']})"),
              (3, True, "1,3", "triangle", f"editor 3, all complex rows (n={ns['e3_acc']})")]
    for idx, filled, dash, shape, _ in series:
        pts = [(lin(r[0], 0, 24, x0, x1), lin(r[idx], 0, 1, y0, y1)) for r in rows]
        s.polyline(pts, width=1.2, dash=dash)
        for x, y in pts:
            s.marker(x, y, shape, filled=filled, r=3.2)
    for i, (_, filled, dash, shape, lab) in enumerate(series):
        xx, yy = 30, 476 + i * 18
        s.line(xx - 10, yy, xx + 10, yy, width=1.2, dash=dash)
        s.marker(xx, yy, shape, filled=filled, r=3.5)
        s.text(xx + 16, yy + 4, lab, 10.5)
    # right: editor 3 strength ratio
    X0, X1 = 580, 970
    frame(s, X0, X1, y0, y1, "fail / pass projection", [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
    s.text((X0 + X1) / 2, 78, "editor 3: own-language signal, failures vs passes", 12, anchor="middle", weight="bold")
    y_one = lin(1.0, 0, 1.2, y0, y1)
    s.line(X0, y_one, X1, y_one, dash="6,3")
    s.text(X1 - 4, y_one - 5, "equal strength", 10, anchor="end")
    pts = [(lin(r[0], 0, 24, X0, X1), lin(r[4], 0, 1.2, y0, y1)) for r in rows if r[4] is not None]
    s.polyline(pts, width=1.2)
    for x, y in pts:
        s.marker(x, y, "square", filled=True, r=3)
    s.text(X0 + 8, y0 - 10, f"ratio of mean projections, {ns['e3_fail']} failures / {ns['e3_pass']} passes", 10)
    s.save(path)


CAPTION = """Figure 5. Two blind editors measured, on their own, whether the requested language is present in the residual stream at the last prompt position of Qwen3.5-0.8B (dev complex prompts, unedited model, labels from the gate 1 answers). Left: accuracy of a nearest-centroid language probe per layer. Editor 2 (circles) used the raw residual, 14 target languages, centroids from passed answers of the other task fold, and split the result by passed answers ({e2_pass}) and full failures ({e2_full}); the target language becomes readable from layer 17 on, in failures too. Editor 3 (triangles) first subtracted the mean over the languages of the same task, used leave-one-row-out centroids over {e3_acc} complex rows (including English variants), and reports one accuracy over all rows; with that centring the language is readable from layer 1 on. Right: editor 3's mean projection on the own-language centroid direction in failures divided by the same in passes ({e3_fail} failures, {e3_pass} passes; failure here means an English answer). Per layer the failures carry {rmin:.2f} to {rmax:.2f} of the pass value (layers {lmin} and {lmax}); the signal is weaker in failures at every layer from 1 to 24. The ratio is computed here from editor 3's two recorded means; the editors did not compute confidence intervals. Editor 1 used a different probe, the log-probability margin of target-language over English tokens at the answer position, and recorded no per-layer numbers: median margin -1.3 nats on failed complex prompts, and the instruction moves the margin by about 15 nats ({ed1_ref}). Sources: {ed2}, {ed3}, {ed3_meta}, {ed2_md} line {ed2_line}, {ed3_md} line {ed3_line}."""


def main():
    vals = Values()
    rows, ns = collect(vals)
    path = os.path.join(FIG, "fig5_mechanism_probe.svg")
    draw(rows, ns, path)
    vals.write("fig5_mechanism_probe")
    rat = [(r[4], r[0]) for r in rows if r[4] is not None]
    rmin, rmax = min(rat), max(rat)
    assert rmax[0] < 1.0
    l1, _ = grep(ED1_MD, r"median margin -1\.3 nats")
    l2, _ = grep(ED1_MD, r"~15 nats")
    ln2, _ = grep(ED2_MD, r"\((\d+) full, (\d+) pass\)")
    ln3, _ = grep(ED3_MD, r"(\d+) pass / (\d+) fail")
    write_text(os.path.join(FIG, "fig5_mechanism_probe.txt"), CAPTION.format(
        ed1_ref=f"{ED1_MD} lines {l1}-{l2}", ed2=ED2, ed3=ED3, ed3_meta=ED3_META, ed2_md=ED2_MD, ed2_line=ln2,
        ed3_md=ED3_MD, ed3_line=ln3, rmin=rmin[0], rmax=rmax[0], lmin=rmin[1], lmax=rmax[1], **ns))
    print("wrote", path)


if __name__ == "__main__":
    main()
