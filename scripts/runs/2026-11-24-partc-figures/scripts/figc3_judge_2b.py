"""fig C3: 2B blind judge. weighted "not full_lang" and "wrong" rates per method, and c06 minus ReCoVeR."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIG, JUDGE, Values, forest, load, write_text  # noqa: E402

NAME = "figc3_judge_2b"
METHODS = [("cross|baseline", "baseline", "circle"), ("cross|instr_end", "instruction at end", "triangle"),
           ("cross|recover_a0.03", "ReCoVeR alpha 0.03", "diamond"), ("cross|c06", "c06", "square")]
RATES = [("fail", "not full_lang"), ("whole", "wrong")]


def collect(vals):
    d = load(JUDGE)
    rows = []
    for key, rname in RATES:
        rows.append(("head", f"judge {rname}, % of 714 answers (weighted)"))
        for mkey, label, shape in METHODS:
            v, (lo, hi) = d["all"]["methods"][mkey]["weighted"][key]
            fld = f"all.methods.{mkey}.weighted.{key}"
            vals.add("rate " + key, label, v, JUDGE, fld + "[0]")
            vals.add("rate " + key, label + " lo", lo, JUDGE, fld + "[1][0]")
            vals.add("rate " + key, label + " hi", hi, JUDGE, fld + "[1][1]")
            rows.append(("row", label, v, lo, hi, shape, True, "", False))
    rows.append(("head", "c06 minus ReCoVeR, points (paired)"))
    for key, rname in RATES:
        for sub, sname, filled in (("all", "all labels", True), ("high", "high confidence only", False)):
            v, (lo, hi) = d[sub]["diffs"][f"c06-recover_a0.03|{key}"]
            fld = f"{sub}.diffs[c06-recover_a0.03|{key}]"
            lab = f"{rname}, {sname}"
            vals.add("diff", lab, v, JUDGE, fld + "[0]")
            vals.add("diff", lab + " lo", lo, JUDGE, fld + "[1][0]")
            vals.add("diff", lab + " hi", hi, JUDGE, fld + "[1][1]")
            rows.append(("row", lab, v, lo, hi, "square", filled, ""))
    return rows


CAPTION = ("Figure C3. Blind LLM judge on Qwen3.5-2B test complex answers (seed 1). A separate Claude Opus 5.5 "
           "agent labelled 60 answers per method (half fastText-flagged, half not, stratified by language) with "
           "method names hidden and prompts shown in full. Rates are weighted to all 714 answers; c06 minus "
           "ReCoVeR uses the same draws for both. Intervals: 95% cluster bootstrap over the 17 split v2 task "
           "groups, 10000 draws, seed 20261111. Open marks drop the 84 low-confidence labels. The judge gave no "
           "empty_or_garbage label, so the second rate is wrong alone. Source: "
           "runs/2026-11-24-judge-2b/analysis/results.json (all.methods.*.weighted, all.diffs, high.diffs).")


def main():
    vals = Values()
    rows = collect(vals)
    path = os.path.join(FIG, NAME + ".svg")
    forest(path, "2B blind judge: not full_lang and wrong rates, c06 vs ReCoVeR",
           "rates in %; differences in points; bar = 95% cluster-bootstrap CI over 17 task groups",
           rows, -20, 70, 10, "percent (rates) or points (differences)",
           [("circle", True, "baseline"), ("triangle", True, "instruction at end"),
            ("diamond", True, "ReCoVeR"), ("square", True, "c06 / difference, all labels"),
            ("square", False, "high confidence only")])
    vals.write(NAME, FIG)
    write_text(os.path.join(FIG, NAME + ".txt"), CAPTION)
    print("wrote", path)


if __name__ == "__main__":
    main()
