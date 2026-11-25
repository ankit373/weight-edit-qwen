"""table (fig 8): guard numbers (empty, loops, NLL; deltas vs baseline rows) for every method, both models."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAB, Values, load, md_table, write_text  # noqa: E402

G3 = "runs/2026-11-06-gate3-run/guard"
E4 = "runs/2026-11-10-gate4-eval"
WS = {1: "runs/2026-11-11-gate5a-eval-ws1", 2: "runs/2026-11-12-gate5a-eval-ws2", 3: "runs/2026-11-13-gate5a-eval-ws3"}
CITED = f"{E4}/scores/table_cited.json"
B3 = "runs/2026-11-13-gate5b-instr-end/guard"
B4 = "runs/2026-11-14-gate5b-recover/guard"
B1T = "runs/2026-11-11-gate5b-baseline/scores/table_b1.json"
EV = "runs/2026-11-17-gate5b-eval/guard"
C06D = "gate5b-workspace/work/c06/dev.guard.json"  # the editor's own dev guard; the eval run has no dev guard for c06

GUARD_ROWS = [
    ("0.8B", "dev", "ReCoVeR, tuned (alpha 0.03, restore on)", f"{G3}/recover_a0.03_on_dev.guard.json"),
    ("0.8B", "dev", "ReCoVeR, alpha 0.03, restore off", f"{G3}/recover_a0.03_off_dev.guard.json"),
    ("0.8B", "dev", "ReCoVeR, paper default (alpha 1)", f"{G3}/recover_a1_on_dev.guard.json"),
    ("0.8B", "dev", "Nie N=100 (paper default)", f"{G3}/nie_n100_dev.guard.json"),
    ("0.8B", "dev", "editor 0 (c02)", f"{E4}/guard/final_dev.guard.json"),
    ("0.8B", "dev", "editor 1", f"{WS[1]}/guard/final_dev.guard.json"),
    ("0.8B", "dev", "editor 2", f"{WS[2]}/guard/final_dev.guard.json"),
    ("0.8B", "dev", "editor 3", f"{WS[3]}/guard/final_dev.guard.json"),
    ("0.8B", "dev", "random, editor 0, seed 1001", f"{E4}/guard/rand_s1001_dev.guard.json"),
    ("0.8B", "dev", "random, editor 0, seed 1002", f"{E4}/guard/rand_s1002_dev.guard.json"),
    ("0.8B", "dev", "random, editor 0, seed 1003", f"{E4}/guard/rand_s1003_dev.guard.json"),
    ("0.8B", "test", "editor 0 (c02)", f"{E4}/guard/final_test.guard.json"),
    ("0.8B", "test", "editor 1", f"{WS[1]}/guard/final_test.guard.json"),
    ("0.8B", "test", "editor 2", f"{WS[2]}/guard/final_test.guard.json"),
    ("0.8B", "test", "editor 3", f"{WS[3]}/guard/final_test.guard.json"),
    ("0.8B", "test", "random, editor 0, seed 1001", f"{E4}/guard/rand_s1001_test.guard.json"),
    ("0.8B", "test", "random, editor 0, seed 1002", f"{E4}/guard/rand_s1002_test.guard.json"),
    ("0.8B", "test", "random, editor 0, seed 1003", f"{E4}/guard/rand_s1003_test.guard.json"),
    ("0.8B", "test", "random, editor 1, seed 1001", f"{WS[1]}/guard/rand_s1001_test.guard.json"),
    ("0.8B", "test", "random, editor 2, seed 1002", f"{WS[2]}/guard/rand_s1002_test.guard.json"),
    ("0.8B", "test", "random, editor 3, seed 1003", f"{WS[3]}/guard/rand_s1003_test.guard.json"),
    ("2B", "dev", "instruction at end (B3)", f"{B3}/instr_end_dev.guard.json"),
    ("2B", "dev", "ReCoVeR, tuned (alpha 0.03, restore off)", f"{B4}/recover_a0.03_off_dev.guard.json"),
    ("2B", "dev", "ReCoVeR, alpha 0.1, restore on", f"{B4}/recover_a0.1_on_dev.guard.json"),
    ("2B", "dev", "ReCoVeR, paper default (alpha 1)", f"{B4}/recover_a1_on_dev.guard.json"),
    ("2B", "dev", "blind edit c06", C06D),
    ("2B", "dev", "random, c06, seed 1001", f"{EV}/rand_s1001_dev.guard.json"),
    ("2B", "dev", "random, c06, seed 1002", f"{EV}/rand_s1002_dev.guard.json"),
    ("2B", "dev", "random, c06, seed 1003", f"{EV}/rand_s1003_dev.guard.json"),
    ("2B", "test", "blind edit c06", f"{EV}/final_test.guard.json"),
    ("2B", "test", "random, c06, seed 1001", f"{EV}/rand_s1001_test.guard.json"),
    ("2B", "test", "random, c06, seed 1002", f"{EV}/rand_s1002_test.guard.json"),
    ("2B", "test", "random, c06, seed 1003", f"{EV}/rand_s1003_test.guard.json"),
]
# 0.8B test rows with loops / empty only (no test NLL was run): key in table_cited.json
CITED_ROWS = [("instr_end", "instruction at end"), ("recover_a0.03_on", "ReCoVeR, tuned (alpha 0.03, restore on)"),
              ("recover_a1_on", "ReCoVeR, paper default (alpha 1)"), ("nie_n100", "Nie N=100 (paper default)"),
              ("fewshot", "few-shot, 1-shot"), ("p50c", "p50c (MIT exp8)")]


def main():
    vals = Values()
    rows, bases = [], {}
    for model, split, label, rel in GUARD_ROWS:
        g = load(rel)
        n, b, d = g["new"], g["baseline"], g["delta"]
        key = (model, split)
        bb = (b["n"], round(b["empty_pct"], 6), round(b["loop_pct"], 6), round(b["nll_mean"], 6))
        if key in bases and bases[key][0] != bb:
            raise SystemExit(f"baseline differs inside {key}: {rel}")
        bases.setdefault(key, (bb, rel))
        for k in ("empty_pts", "loop_pts", "nll_nats"):
            vals.add(f"{model} {split}", f"{label} {k}", d[k], rel, f"delta.{k}")
        rows.append([model, split, label, n["n"], f"{n['empty_pct']:.2f} ({d['empty_pts']:+.2f})",
                     f"{n['loop_pct']:.2f} ({d['loop_pts']:+.2f})", f"{n['nll_mean']:.3f} ({d['nll_nats']:+.3f})",
                     "pass" if g["pass_1_to_3"] else "fail: " + ", ".join(g["failed_checks"]), rel])
    cited = load(CITED)
    base = cited["baseline"]
    tb = bases[("0.8B", "test")][0]
    assert abs(base["loops_pct"] - round(tb[2], 2)) < 1e-9, (base["loops_pct"], tb)
    for key, label in CITED_ROWS:
        r = cited[key]
        dl = r["loops_pct"] - base["loops_pct"]
        de = r["empty_pct"] - base["empty_pct"]
        vals.add("0.8B test (cited)", f"{label} loops_pct", r["loops_pct"], CITED, f"{key}.loops_pct")
        verdict = "loops over limit" if dl > 2.0 else "loops and empty within limits; NLL not run"
        rows.append(["0.8B", "test", label, r["n_rows"], f"{r['empty_pct']:.2f} ({de:+.2f})",
                     f"{r['loops_pct']:.2f} ({dl:+.2f})", "not run", verdict, f"{CITED} [{key}]"])
    b1 = load(B1T)
    vals.add("2B test", "baseline loops_pct", b1["test"]["loops_pct"], B1T, "test.loops_pct")
    base_rows = []
    for (model, split), (bb, rel) in sorted(bases.items()):
        base_rows.append([model, split, bb[0], f"{bb[1]:.2f}", f"{bb[2]:.2f}", f"{bb[3]:.3f}", rel + " (baseline)"])
    tb2 = bases[("2B", "test")][0]
    assert f"{b1['test']['loops_pct']:.2f}" == f"{tb2[2]:.2f}", (b1["test"]["loops_pct"], tb2)
    rows.sort(key=lambda r: (r[0], r[1]))
    text = (
        "# guard summary (fig 8), both models\n\n"
        "made by `scripts/tab_guard.py`. guard = gate 3 `guard.py` against the baseline rows of the same ids: "
        "1 empty answers up by more than 1 point, 2 looping answers (distinct 4-gram ratio below 0.5) up by more "
        "than 2 points, 3 mean base-model NLL of the answers up by more than 1.0 nat per token. "
        "cell = value (change vs baseline). one seed.\n\n"
        "## baseline rows\n\n" +
        md_table(["model", "split", "n", "empty %", "loop %", "mean NLL", "source"], base_rows) +
        "\n## methods\n\n" +
        md_table(["model", "split", "method", "n", "empty % (d)", "loop % (d)", "mean NLL (d)", "checks 1-3", "source"],
                 rows) +
        "\nnot run (no guard file exists): 0.8B instruction at end and few-shot on dev, NLL on 0.8B test for the "
        "prompt and steering methods, any 2B test guard for B3 or B4. the 2B c06 dev row is the editor's own "
        "guard run (`" + C06D + "`). the 2B test baseline loop % equals `" + B1T + "`, which the script checks.\n")
    write_text(os.path.join(TAB, "guard.md"), text)
    vals.write("guard", TAB)
    print("wrote", os.path.join(TAB, "guard.md"))


if __name__ == "__main__":
    main()
