"""fig C2: damage checks. each edit minus its model's baseline on Global-MMLU, MGSM and IFEval, 95% cluster CI."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import EDITS_08, EDITS_2B, FIG, Values, forest, load, stats_rel, write_text  # noqa: E402

NAME = "figc2_damage"
BENCH = [("global-mmlu", "acc", "Global-MMLU accuracy, 1400 items (100 x 14 languages)"),
         ("mgsm", "acc", "MGSM accuracy, 350 items (50 x 7 languages)"),
         ("ifeval", "prompt_strict", "IFEval prompt-level strict, 495 scored prompts")]
SHAPE = {"damage": ("square", True), "possible damage": ("square", False), "no damage shown": ("circle", False)}


def collect(vals):
    rows = []
    for bench, metric, bname in BENCH:
        rows.append(("head", bname))
        for model, mname, edits in (("08", "0.8B", EDITS_08), ("2b", "2B", EDITS_2B)):
            rel = stats_rel(model, bench)
            comp = load(rel)["comparisons"]
            for key, label in edits:
                c = comp[f"{key}_vs_baseline"]
                m = c["all"][metric]
                lab = c["damage"]["label"]
                fld = f"comparisons.{key}_vs_baseline.all.{metric}"
                panel = f"{model} {bench}"
                vals.add(panel, label + " diff", m["diff"], rel, fld + ".diff")
                vals.add(panel, label + " lo", m["ci"][0], rel, fld + ".ci[0]")
                vals.add(panel, label + " hi", m["ci"][1], rel, fld + ".ci[1]")
                vals.add(panel, label + " label", lab, rel, f"comparisons.{key}_vs_baseline.damage.label")
                shape, filled = SHAPE[lab]
                rows.append(("row", f"{mname} {label}", m["diff"], m["ci"][0], m["ci"][1], shape, filled,
                             f"  {lab}"))
    return rows


CAPTION = ("Figure C2. Part C damage checks: each blind edit minus the same model's unedited baseline, in points, "
           "with 95% paired cluster-bootstrap intervals (10000 draws, seed 20261111; clusters: Global-MMLU "
           "sample_id (100), MGSM item (50), IFEval prompt). Labels follow the preregistered rule: damage = interval "
           "below 0 and estimate below -1 point (filled square); possible damage = estimate below -1 point with an "
           "interval that includes 0 (open square); otherwise no damage shown (open circle). The grey band is "
           "[-2, +2] points and the dashed line is -1 point. Global-MMLU is scored from the logits of A to D; MGSM "
           "and IFEval are sampled, seed 1, with 384 and 256 new tokens. ReCoVeR and instruction at end do not "
           "touch these prompts (checked on 20 rows per set and model) and are not shown. Source: "
           "runs/2026-11-22-partc-run/scores/{08,2b}/{global-mmlu,mgsm,ifeval}/stats.json.")


def main():
    vals = Values()
    rows = collect(vals)
    path = os.path.join(FIG, NAME + ".svg")
    forest(path, "Damage checks: blind edit minus baseline, points",
           "point = edit minus baseline; bar = 95% paired cluster-bootstrap CI; grey band = [-2, +2]; "
           "dashed = -1 point",
           rows, -12, 12, 2, "edit minus baseline, points (left of 0 = edit worse)",
           [("square", True, "damage"), ("square", False, "possible damage"),
            ("circle", False, "no damage shown")],
           band=(-2, 2), extra_lines=(-1,))
    vals.write(NAME, FIG)
    write_text(os.path.join(FIG, NAME + ".txt"), CAPTION)
    print("wrote", path)


if __name__ == "__main__":
    main()
