"""fig C1: each method minus its model's baseline, cross-lingual LPR, four part C sets, both models, 95% cluster CI."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EDITS_08, EDITS_2B, FIG, Values, forest, load, stats_rel, write_text  # noqa: E402

NAME = "figc1_crossling_gain"
SETS = [("m-arenahard", "m-ArenaHard, 700 prompts"), ("xl-alpacaeval", "XL-AlpacaEval, 980 prompts"),
        ("lcb-greedy", "LCB test complex, greedy, 714 prompts"),
        ("lcb-long", "LCB test complex, 400 tokens, 238 prompts")]
FIXES = [("recover", "ReCoVeR alpha 0.03", "diamond"), ("instr_end", "instruction at end", "triangle")]


def collect(vals):
    rows = []
    for model, mname, edits in (("08", "Qwen3.5-0.8B", EDITS_08), ("2b", "Qwen3.5-2B", EDITS_2B)):
        for name, sname in SETS:
            rel = stats_rel(model, name)
            comp = load(rel)["comparisons"]
            rows.append(("head", f"{mname}: {sname}"))
            meths = [(k, lab, shp) for k, lab, shp in FIXES] + [(k, lab, "circle") for k, lab in edits]
            for key, label, shape in meths:
                c = comp[f"{key}_vs_baseline"]["unscored_drop"]["lpr"]
                fld = f"comparisons.{key}_vs_baseline.unscored_drop.lpr"
                panel = f"{model} {name}"
                vals.add(panel, label + " diff", c["diff"], rel, fld + ".diff")
                vals.add(panel, label + " lo", c["ci"][0], rel, fld + ".ci[0]")
                vals.add(panel, label + " hi", c["ci"][1], rel, fld + ".ci[1]")
                filled = c["ci"][0] > 0
                rows.append(("row", label, c["diff"], c["ci"][0], c["ci"][1], shape, filled, ""))
    return rows


CAPTION = ("Figure C1. Part C cross-lingual check: each method minus the same model's baseline in LPR points "
           "(unscored answers left out, as LCB does), with 95% paired cluster-bootstrap intervals (10000 draws, "
           "seed 20261111; clusters are the base prompt across its 14 languages for m-ArenaHard (50) and "
           "XL-AlpacaEval (70), and the split v2 task group for the two LCB stress sets (17)). Filled marks have "
           "an interval above 0. The language line comes before the prompt in m-ArenaHard and XL-AlpacaEval. "
           "Seed 1 for sampled sets. Source: runs/2026-11-22-partc-run/scores/{08,2b}/{m-arenahard,lcb-greedy,"
           "lcb-long}/stats.json and scores/nc-sa/xl-alpacaeval/{08,2b}/stats.json (comparisons.*_vs_baseline).")


def main():
    vals = Values()
    rows = collect(vals)
    path = os.path.join(FIG, NAME + ".svg")
    forest(path, "Gain over the baseline on part C cross-lingual sets, LPR points",
           "point = method minus baseline (unscored left out); bar = 95% paired cluster-bootstrap CI; "
           "filled = CI above 0",
           rows, -15, 45, 5, "method minus baseline, LPR points (right of 0 = method higher)",
           [("diamond", True, "ReCoVeR"), ("triangle", True, "instruction at end"),
            ("circle", True, "blind edit"), ("circle", False, "open = CI includes 0")])
    vals.write(NAME, FIG)
    write_text(os.path.join(FIG, NAME + ".txt"), CAPTION)
    print("wrote", path)


if __name__ == "__main__":
    main()
