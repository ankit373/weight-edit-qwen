"""formatting only: out/results.json + guard files -> out/tables.md. no new numbers.

usage: make_tables.py <results.json> <tables.md>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
R = json.load(open(sys.argv[1]))
P = R["point"]
NAME = {"baseline": "baseline (gate 1)", "instr_end": "instruction at end", "recover": "ReCoVeR 0.03",
        "ed0": "editor 0 (c02, gate 4)", "ed1": "editor 1 (h5_a2_n5)", "ed2": "editor 2 (mix21_22b0.75_23b0.5)",
        "ed3": "editor 3 (combo_a14_b14)", "mean_editor": "mean of 4 editors", "ed0_s2": "editor 0, seed 2",
        "baseline_s2": "baseline, seed 2", "recover_s2": "ReCoVeR 0.03, seed 2"}
GUARD = {  # test guard json (gate 3 guard.py, vs gate 1 test rows)
    "ed0": "runs/2026-11-10-gate4-eval/guard/final_test.guard.json",
    "ed1": "runs/2026-11-11-gate5a-eval-ws1/guard/final_test.guard.json",
    "ed2": "runs/2026-11-12-gate5a-eval-ws2/guard/final_test.guard.json",
    "ed3": "runs/2026-11-13-gate5a-eval-ws3/guard/final_test.guard.json",
}
CITED = json.load(open(os.path.join(ROOT, "runs/2026-11-10-gate4-eval/scores/table_cited.json")))
L = []


def f1(x):
    return f"{x:.1f}"


def ci(v):
    return f"{v[0]:+.1f} [{v[1]:+.1f}, {v[2]:+.1f}]"


L.append("## main table (test, seed 1; drop = unscored left out, fail = unscored counted as fail)\n")
L.append("| method | complex LPR drop / fail | all LPR drop / fail | full % all drop / fail | full % complex drop / fail | scored complex / all |")
L.append("|---|---|---|---|---|---|")
rows = ["baseline", "instr_end", "recover", "ed0", "ed1", "ed2", "ed3"]
for lab in rows:
    p = P[lab]
    L.append(f"| {NAME[lab]} | " + " | ".join(f"{f1(p['drop'][k])} / {f1(p['fail'][k])}"
             for k in ("complex_lpr", "all_lpr", "full_all", "full_complex"))
             + f" | {p['scored']['complex']} / {p['scored']['all']} |")
eds = ["ed0", "ed1", "ed2", "ed3"]
mean = {f: {k: sum(P[e][f][k] for e in eds) / 4 for k in ("complex_lpr", "all_lpr", "full_all", "full_complex")}
        for f in ("drop", "fail")}
rng = {f: {k: (min(P[e][f][k] for e in eds), max(P[e][f][k] for e in eds)) for k in mean[f]} for f in mean}
L.append("| mean of 4 editors (range) | " + " | ".join(
    f"{f1(mean['drop'][k])} ({f1(rng['drop'][k][0])} - {f1(rng['drop'][k][1])}) / {f1(mean['fail'][k])} ({f1(rng['fail'][k][0])} - {f1(rng['fail'][k][1])})"
    for k in ("complex_lpr", "all_lpr", "full_all", "full_complex"))
    + f" | {sum(P[e]['scored']['complex'] for e in eds) / 4:.1f} / {sum(P[e]['scored']['all'] for e in eds) / 4:.1f} |")
for lab in ("ed0_s2", "baseline_s2", "recover_s2"):
    p = P[lab]
    L.append(f"| {NAME[lab]} | " + " | ".join(f"{f1(p['drop'][k])} / {f1(p['fail'][k])}"
             for k in ("complex_lpr", "all_lpr", "full_all", "full_complex"))
             + f" | {p['scored']['complex']} / {p['scored']['all']} |")

L.append("\n## guard (test, vs gate 1 test rows; gate 3 guard.py)\n")
L.append("| method | empty % (d) | loop % (d) | mean NLL (d) | pass 1-3 | source |")
L.append("|---|---|---|---|---|---|")
g = json.load(open(os.path.join(ROOT, GUARD["ed0"])))["baseline"]
L.append(f"| baseline (gate 1) | {g['empty_pct']:.1f} | {g['loop_pct']:.2f} | {g['nll_mean']:.3f} | | {GUARD['ed0']} \"baseline\" |")
for lab, key in (("instr_end", "instr_end"), ("recover", "recover_a0.03_on")):
    t = CITED[key]
    L.append(f"| {NAME[lab]} | {t['empty_pct']:.1f} ({t['empty_pct'] - g['empty_pct']:+.1f}) | {t['loops_pct']:.2f} "
             f"({t['loops_pct'] - g['loop_pct']:+.2f}) | not run on test | | runs/2026-11-10-gate4-eval/scores/table_cited.json [{key}] |")
for e in eds:
    d = json.load(open(os.path.join(ROOT, GUARD[e])))
    L.append(f"| {NAME[e]} | {d['new']['empty_pct']:.1f} ({d['delta']['empty_pts']:+.1f}) | {d['new']['loop_pct']:.2f} "
             f"({d['delta']['loop_pts']:+.2f}) | {d['new']['nll_mean']:.3f} ({d['delta']['nll_nats']:+.3f}) | "
             f"{'pass' if d['pass_1_to_3'] else 'FAIL'} | {GUARD[e]} |")

L.append("\n## paired differences, 95% cluster bootstrap ci (split v2 groups, 10000 draws, seed 20261111)\n")
L.append("own random = the editor's own random control(s), same tensors, entry count and frobenius norm. editor 0 has three (s1001-1003); its row uses their mean on each draw.\n")
for f in ("drop", "fail"):
    L.append(f"### unscored {'left out (as reported)' if f == 'drop' else 'counted as fail, both sides'}\n")
    L.append("| a | minus b | complex LPR | all LPR | full % all | full % complex |")
    L.append("|---|---|---|---|---|---|")
    for c in R["comparisons"]:
        if c["fill"] != f:
            continue
        b = {"own_rand": "own random"}.get(c["b"], NAME.get(c["b"], c["b"]))
        L.append(f"| {NAME.get(c['a'], c['a'])} | {b} | " + " | ".join(ci(c[k]) for k in
                 ("complex_lpr", "all_lpr", "full_all", "full_complex")) + " |")
    L.append("")
open(sys.argv[2], "w").write("\n".join(L) + "\n")
