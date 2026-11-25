"""results table for this run, every number read from a score file. stdlib only.
usage (project root): table.py > runs/2026-11-22-partc-08b-side/scores/table.md"""
import csv
import json

R = "runs/2026-11-22-partc-08b-side"
MONO = {
    "base (gate 1)": "runs/2026-11-06-gate3-run/scores/baseline_mono.tsv",
    "c02_nb_L15u1047_k2": "runs/2026-11-10-gate4-eval/scores/final_mono.tsv",
    "h5_a2_n5": f"{R}/scores/h5_a2_n5_mono.tsv",
    "mix21_22b0.75_23b0.5": f"{R}/scores/mix21_22b0.75_23b0.5_mono.tsv",
    "combo_a14_b14": f"{R}/scores/combo_a14_b14_mono.tsv",
}
MKEY = {"base (gate 1)": "base"}
LKEY = {"base (gate 1)": "base", "c02_nb_L15u1047_k2": "c02"}


def mono_row(path, lang):
    with open(path) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["task"] == "monolingual" and r["source"] == "all" and r["language"] == lang:
                return r
    raise SystemExit(f"no {lang} row in {path}")


loops = {}
with open(f"{R}/scores/mono_loops.txt") as f:
    for line in f:
        k, js = line.split(" ", 1)
        loops[k] = json.loads(js)
mm = json.load(open(f"{R}/scores/mmlu.json"))

print("| run | mono LPR all (n) | mono LPR en (n) | mono loops | MMLU acc [95% ci] | delta vs base [95% ci] | mcnemar p | right->wrong / wrong->right |")
print("|---|---|---|---|---|---|---|---|")
for name, tsv in MONO.items():
    a, e = mono_row(tsv, "all"), mono_row(tsv, "en")
    lp = loops[LKEY.get(name, name)]
    m = mm[MKEY.get(name, name)]
    acc = f"{m['lmeval']['acc']} {m['lmeval']['ci95']}"
    v = m.get("vs_base_same_ids")
    if v:
        d = v["lmeval"]
        delta = f"{d['delta_pts']:+} {d['delta_ci95']}"
        p, flips = d["mcnemar_exact_p"], f"{d['base_right_run_wrong']} / {d['base_wrong_run_right']}"
    else:
        delta, p, flips = "-", "-", "-"
    print(f"| {name} | {a['lpr']} ({a['n_scored']}) | {e['lpr']} ({e['n_scored']}) | {lp['loop']} of {lp['n']} | {acc} | {delta} | {p} | {flips} |")
