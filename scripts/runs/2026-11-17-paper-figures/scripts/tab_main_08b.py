"""table: main results on 0.8B test (seed 1, seed 2 rows apart), both unscored rules, plus paired cis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAB, Values, full_pct, load, md_table, score_row, write_text  # noqa: E402

SUM = "runs/2026-11-13-gate5a-summary/out/results.json"
A1 = "runs/2026-11-06-gate3-run/scores/recover_a1_on_test.json"
POINT_ROWS = [
    ("baseline", "baseline (gate 1)"),
    ("instr_end", "instruction at end"),
    ("recover", "ReCoVeR, tuned (alpha 0.03, restore on)"),
    ("ed0", "editor 0 (gate 4, c02)"),
    ("ed1", "editor 1 (h5_a2_n5)"),
    ("ed2", "editor 2 (mix21_22b0.75_23b0.5)"),
    ("ed3", "editor 3 (combo_a14_b14)"),
    ("ed0_rand1001", "random control, editor 0, seed 1001"),
    ("ed0_rand1002", "random control, editor 0, seed 1002"),
    ("ed0_rand1003", "random control, editor 0, seed 1003"),
    ("ed1_rand1001", "random control, editor 1, seed 1001"),
    ("ed2_rand1002", "random control, editor 2, seed 1002"),
    ("ed3_rand1003", "random control, editor 3, seed 1003"),
]
S2_ROWS = [("baseline_s2", "baseline, seed 2"), ("recover_s2", "ReCoVeR, tuned, seed 2"), ("ed0_s2", "editor 0, seed 2")]
METRICS = [("complex_lpr", "complex LPR"), ("all_lpr", "all LPR"), ("full_all", "full % all"),
           ("full_complex", "full % complex")]
NAMES = {"baseline": "baseline (gate 1)", "recover": "ReCoVeR tuned", "own_rand": "own random control",
         "instr_end": "instruction at end", "baseline_s2": "baseline, seed 2", "recover_s2": "ReCoVeR tuned, seed 2"}
A_NAMES = {"ed0": "editor 0", "ed1": "editor 1", "ed2": "editor 2", "ed3": "editor 3",
           "mean_editor": "mean of 4 editors", "ed0_s2": "editor 0, seed 2", "instr_end": "instruction at end"}


def point_table(vals, d, rows):
    out = []
    for key, label in rows:
        pt = d["point"][key]
        cells = [label]
        for m, mname in METRICS:
            a = vals.add(f"{mname} drop", label, pt["drop"][m], SUM, f"point.{key}.drop.{m}")
            b = vals.add(f"{mname} fail", label, pt["fail"][m], SUM, f"point.{key}.fail.{m}")
            cells.append(f"{a:.1f} / {b:.1f}")
        sc = pt["scored"]
        vals.add("scored complex", label, sc["complex"], SUM, f"point.{key}.scored.complex")
        vals.add("scored all", label, sc["all"], SUM, f"point.{key}.scored.all")
        cells.append(f"{sc['complex']} / {sc['all']}")
        out.append(cells)
    return out


def fmt_ci(t):
    return f"{t[0]:+.1f} [{t[1]:+.1f}, {t[2]:+.1f}]"


def main():
    vals = Values()
    d = load(SUM)
    head = ["method"] + [f"{n} drop / fail" for _, n in METRICS] + ["scored complex / all"]
    t1 = point_table(vals, d, POINT_ROWS)
    a1c, a1a = score_row(A1, "complex_prompts"), score_row(A1, "all")
    vals.add("complex LPR drop", "ReCoVeR paper default", a1c["lpr"], A1, "complex_prompts/all lpr")
    vals.add("all LPR drop", "ReCoVeR paper default", a1a["lpr"], A1, "all/all lpr")
    a1w = A1.replace(".json", "_wrong_lang.json")
    fa = vals.add("full % all drop", "ReCoVeR paper default", full_pct(A1, a1w, "all")[0], a1w, "FP rule, all")
    fc = vals.add("full % complex drop", "ReCoVeR paper default", full_pct(A1, a1w, "complex_prompts")[0], a1w,
                  "FP rule, complex_prompts")
    t1.insert(3, ["ReCoVeR, paper default (alpha 1, restore on) *", f"{a1c['lpr']:.1f} / n.c.", f"{a1a['lpr']:.1f} / n.c.",
                  f"{fa:.1f} / n.c.", f"{fc:.1f} / n.c.", f"{a1c['n_scored']} / {a1a['n_scored']}"])
    t2 = point_table(vals, d, S2_ROWS)
    comp = d["comparisons"]
    t3 = []
    for c in comp:
        row = [A_NAMES[c["a"]], NAMES[c["b"]], c["fill"]]
        for m, mname in METRICS:
            vals.add(f"diff {mname}", f"{c['a']} - {c['b']} ({c['fill']})", c[m][0], SUM,
                     f"comparisons[{c['a']},{c['b']},{c['fill']}].{m}")
            row.append(fmt_ci(c[m]))
        t3.append(row)
    t3.sort(key=lambda r: (r[2] != "drop",))
    boot = d["bootstrap"]
    text = (
        "# main results, Qwen3.5-0.8B, test (2100 cross-lingual prompts, 714 complex)\n\n"
        "made by `scripts/tab_main_08b.py` from `" + SUM + "` (all cells except the paper-default row) and `" + A1 +
        "` (paper-default row). drop = unscored answers left out (as reported), fail = unscored answers counted as fail "
        "and as full failure. full % = share of scored answers fully in a wrong language.\n\n"
        "## seed 1\n\n" + md_table(head, t1) +
        "\n\\* ReCoVeR paper default: most answers loop and are not scored, so its LPR is not a meaningful number. "
        "full % of this row: full_response_wrong rows of the scorer's wrong_lang file over scored answers. "
        "n.c. = not computed (no per-prompt rows for this run).\n\n"
        "## seed 2 (only these three methods were run twice)\n\n" + md_table(head, t2) +
        f"\n## paired differences, 95% cluster-bootstrap CI ({boot['B']} draws, {boot['cluster']}, seed {boot['seed']})\n\n"
        "a minus b, in points. own random control = same tensors, entry count and Frobenius norm as the edit; editor 0 "
        "has three, its row uses their mean on each draw. the mean-of-4 CI covers prompt sampling only.\n\n" +
        md_table(["a", "b", "unscored"] + [n for _, n in METRICS], t3))
    write_text(os.path.join(TAB, "main_08b.md"), text)
    vals.write("main_08b", TAB)
    print("wrote", os.path.join(TAB, "main_08b.md"))


if __name__ == "__main__":
    main()
