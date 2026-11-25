"""table: part B on Qwen3.5-2B (B1 baseline, B3 instruction at end, B4 ReCoVeR, blind edit c06), dev and test."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAB, Values, full_pct, load, md_table, score_row, write_text  # noqa: E402

B1 = "runs/2026-11-11-gate5b-baseline"
B3 = "runs/2026-11-13-gate5b-instr-end"
B4 = "runs/2026-11-14-gate5b-recover"
EV = "runs/2026-11-17-gate5b-eval"
WS = "gate5b-workspace/work/c06"
B1T = f"{B1}/scores/table_b1.json"
EVT = f"{EV}/scores/table_eval.json"
STATS = "runs/2026-11-20-stats-2b/out/results.json"
MMLU = f"{EV}/scores/mmlu.json"
C06 = "blind edit c06"

# label, score prefix per split, dev guard file (None = baseline itself)
METHODS = [
    ("baseline (B1)", {"dev": f"{B1}/scores/baseline_dev", "test": f"{B1}/scores/baseline_test"}, None),
    ("instruction at end (B3)", {"dev": f"{B3}/scores/instr_end_dev", "test": f"{B3}/scores/instr_end_test"},
     f"{B3}/guard/instr_end_dev.guard.json"),
    ("ReCoVeR, tuned (alpha 0.03, restore off)",
     {"dev": f"{B4}/scores/recover_a0.03_off_dev", "test": f"{B4}/scores/recover_a0.03_off_test"},
     f"{B4}/guard/recover_a0.03_off_dev.guard.json"),
    ("ReCoVeR, runner-up (alpha 0.1, restore on), dev only", {"dev": f"{B4}/scores/recover_a0.1_on_dev"},
     f"{B4}/guard/recover_a0.1_on_dev.guard.json"),
    ("ReCoVeR, paper default (alpha 1, restore on) *",
     {"dev": f"{B4}/scores/recover_a1_on_dev", "test": f"{B4}/scores/recover_a1_on_test"},
     f"{B4}/guard/recover_a1_on_dev.guard.json"),
    (C06 + " **", {"dev": f"{WS}/dev_scores", "test": f"{EV}/scores/final_test"}, f"{WS}/dev.guard.json"),
    ("random control, seed 1001, test only", {"test": f"{EV}/scores/rand_s1001_test"}, None),
    ("random control, seed 1002, test only", {"test": f"{EV}/scores/rand_s1002_test"}, None),
    ("random control, seed 1003, test only", {"test": f"{EV}/scores/rand_s1003_test"}, None),
]
S2 = [("baseline (B1), seed 2", f"{EV}/scores/base_test_s2"),
      ("instruction at end (B3), seed 2", f"{EV}/scores/instr_end_test_s2"),
      ("ReCoVeR, tuned, seed 2", f"{EV}/scores/recover_a0.03_off_test_s2"),
      (C06 + ", seed 2", f"{EV}/scores/final_test_s2")]
C06_TEST_GUARD = f"{EV}/guard/final_test.guard.json"
# comparisons in the stats run: key, a, b
COMPS = [("c06_vs_recover", "c06", "ReCoVeR tuned"), ("c06_vs_baseline", "c06", "baseline"),
         ("c06_vs_instr_end", "c06", "instruction at end"), ("c06_vs_rand1001", "c06", "random 1001"),
         ("c06_vs_rand1002", "c06", "random 1002"), ("c06_vs_rand1003", "c06", "random 1003"),
         ("recover_vs_baseline", "ReCoVeR tuned", "baseline"),
         ("recover_a1_vs_baseline", "ReCoVeR paper default", "baseline"),
         ("randmean_vs_baseline", "mean of 3 random", "baseline")]
METRICS = [("complex_lpr", "complex LPR"), ("all_lpr", "all LPR"), ("full_complex", "full % complex"),
           ("full_all", "full % all")]


def ws_full_pct(prefix, source):
    """full % from the editor workspace's own `.fullfail.json` (its scorer wrote that, not `_wrong_lang.json`)."""
    rel = prefix + ".fullfail.json"
    r = load(rel)[f"{source}/all"]
    assert r["scored"] == score_row(prefix + ".json", source)["n_scored"], (rel, source)
    return 100.0 * r["full"] / r["scored"], r["full"], r["scored"], rel


def cells(vals, label, prefix):
    sc = prefix + ".json"
    c, a = score_row(sc, "complex_prompts"), score_row(sc, "all")
    if prefix.startswith(WS):
        fc, fa = ws_full_pct(prefix, "complex_prompts"), ws_full_pct(prefix, "all")
        wl = fc[3]
    else:
        wl = prefix + "_wrong_lang.json"
        fc, fa = full_pct(sc, wl, "complex_prompts"), full_pct(sc, wl, "all")
    vals.add("complex lpr", label, c["lpr"], sc, "complex_prompts/all lpr")
    vals.add("all lpr", label, a["lpr"], sc, "all/all lpr")
    vals.add("full % complex", label, fc[0], wl, f"FP: {fc[1]} full / {fc[2]} scored")
    vals.add("full % all", label, fa[0], wl, f"FP: {fa[1]} full / {fa[2]} scored")
    return [f"{c['lpr']:.1f}", f"{a['lpr']:.1f}", f"{fc[0]:.1f}", f"{fa[0]:.1f}",
            f"{c['n_scored']} / {a['n_scored']}"]


def check_eval(evt, prefix, row):
    """test rows must match table_eval.json of the eval run wherever it has the same score file."""
    hit = [v for v in evt.values() if v["score_prefix"] == prefix]
    if not hit:
        return 0
    e = hit[0]
    want = [f"{e['complex']['lpr']:.1f}", f"{e['all']['lpr']:.1f}", f"{e['complex']['full_pct']:.1f}",
            f"{e['all']['full_pct']:.1f}", f"{e['complex']['scored']} / {e['all']['scored']}"]
    assert row[1:] == want, (prefix, row[1:], want)
    return 1


def ci(t):
    return f"{t['diff']:+.1f} [{t['ci_group'][0]:+.1f}, {t['ci_group'][1]:+.1f}]"


def guard_row(vals, label, rel):
    g = load(rel)
    n, b, dl = g["new"], g["baseline"], g["delta"]
    for k in ("empty_pts", "loop_pts", "nll_nats"):
        vals.add("guard delta", f"{label} {k}", dl[k], rel, f"delta.{k}")
    row = [label, f"{n['empty_pct']:.2f} ({dl['empty_pts']:+.2f})", f"{n['loop_pct']:.2f} ({dl['loop_pts']:+.2f})",
           f"{n['nll_mean']:.3f} ({dl['nll_nats']:+.3f})",
           "pass" if g["pass_1_to_3"] else "fail: " + ", ".join(g["failed_checks"])]
    base = (b["n"], f"{b['empty_pct']:.2f}", f"{b['loop_pct']:.2f}", f"{b['nll_mean']:.3f}")
    return row, base


def main():
    vals = Values()
    b1t, evt, st, mm = load(B1T), load(EVT), load(STATS), load(MMLU)
    dev_rows, test_rows, guard_rows, bases = [], [], [], set()
    n_checked = 0
    for label, pref, gd in METHODS:
        if "dev" in pref:
            dev_rows.append([label] + cells(vals, label + " dev", pref["dev"]))
        if "test" in pref:
            tl = label.replace(" **", "")
            test_rows.append([tl] + cells(vals, tl + " test", pref["test"]))
            n_checked += check_eval(evt, pref["test"], test_rows[-1])
        if gd:
            row, base = guard_row(vals, label, gd)
            guard_rows.append(row)
            bases.add(base)
    assert len(bases) == 1, bases  # every dev guard file compares to the same B1 rows
    base = next(iter(bases))
    guard_rows.insert(0, ["baseline (B1)"] + list(base[1:]) + [""])
    s2_rows = []
    for label, pref in S2:
        s2_rows.append([label] + cells(vals, label, pref))
        n_checked += check_eval(evt, pref, s2_rows[-1])
    assert n_checked == len(evt), (n_checked, len(evt))  # every table_eval method is in a table and agrees
    tg_row, tg_base = guard_row(vals, C06 + " test", C06_TEST_GUARD)
    tg_rows = [["baseline (B1)"] + list(tg_base[1:]) + [""], [C06] + tg_row[1:]]
    # check the FP rule against the B1 table, as numbers.md did
    for split in ("dev", "test"):
        for src, key in (("complex", "complex_prompts"), ("all", "all")):
            pref = f"{B1}/scores/baseline_{split}"
            got = round(full_pct(pref + ".json", pref + "_wrong_lang.json", key)[0], 1)
            assert got == b1t[split][src]["full_pct"], (split, src, got)
    assert f"{b1t['test']['loops_pct']:.2f}" == tg_base[2], (b1t["test"]["loops_pct"], tg_base)
    t_loop = b1t["test"]["loops_pct"]
    vals.add("test loops %", "baseline (B1)", t_loop, B1T, "test.loops_pct")
    # paired differences from the stats run
    comp_rows = []
    for key, a, b in COMPS:
        for seed, c in st["comparisons"][key].items():
            row = [a, b, seed]
            for m, mname in METRICS:
                vals.add(f"diff {mname}", f"{key} {seed}", c[m]["diff"], STATS, f"comparisons.{key}.{seed}.{m}")
                vals.add(f"ci lo {mname}", f"{key} {seed}", c[m]["ci_group"][0], STATS,
                         f"comparisons.{key}.{seed}.{m}.ci_group[0]")
                vals.add(f"ci hi {mname}", f"{key} {seed}", c[m]["ci_group"][1], STATS,
                         f"comparisons.{key}.{seed}.{m}.ci_group[1]")
                row.append(ci(c[m]))
            uf = c["complex_lpr"]["unscored_fail"]
            vals.add("diff complex lpr, unscored = fail", f"{key} {seed}", uf["diff"], STATS,
                     f"comparisons.{key}.{seed}.complex_lpr.unscored_fail")
            row.append(ci(uf))
            comp_rows.append(row)
    # side effects: monolingual LPR and MMLU
    mo = st["mono"]
    for k in ("c06", "baseline", "diff"):
        vals.add("mono lpr", k, mo[k], STATS, f"mono.{k}")
    side = [["monolingual LPR, all (2400 prompts, seed 1)", f"{mo['baseline']:.1f}", f"{mo['c06']:.1f}",
             f"{mo['diff']:+.1f} [{mo['ci_source_row'][0]:+.1f}, {mo['ci_source_row'][1]:+.1f}]",
             f"{mo['mcnemar_fail']['p_exact']:.2f}"]]
    vals.add("mono ci lo", "c06 - baseline", mo["ci_source_row"][0], STATS, "mono.ci_source_row[0]")
    vals.add("mono ci hi", "c06 - baseline", mo["ci_source_row"][1], STATS, "mono.ci_source_row[1]")
    for run, label in (("final", "c06"), ("rand_s1001", "random 1001"), ("rand_s1002", "random 1002"),
                       ("rand_s1003", "random 1003")):
        r = mm[run]
        v = r["vs_base_same_ids"]["lmeval"]
        vals.add("mmlu acc", label, r["lmeval"]["acc"], MMLU, f"{run}.lmeval.acc")
        vals.add("mmlu delta", label, v["delta_pts"], MMLU, f"{run}.vs_base_same_ids.lmeval.delta_pts")
        side.append([f"MMLU-Redux accuracy, {label} ({r['n']} questions)", f"{mm['base']['lmeval']['acc']:.2f}",
                     f"{r['lmeval']['acc']:.2f}",
                     f"{v['delta_pts']:+.2f} [{v['delta_ci95'][0]:+.2f}, {v['delta_ci95'][1]:+.2f}]",
                     f"{v['mcnemar_exact_p']:.2f}"])
    vals.add("mmlu acc", "base", mm["base"]["lmeval"]["acc"], MMLU, "base.lmeval.acc")
    head = ["method", "complex LPR", "all LPR", "full % complex", "full % all", "scored complex / all"]
    text = (
        "# part B, Qwen3.5-2B\n\n"
        "made by `scripts/tab_partb_2b.py`. LPR from the score.py json of each run (mean over language cells, "
        "unscored left out). full % = answers with `full_response_wrong` in the run's `_wrong_lang.json` over scored "
        "answers (the numbers.md FP rule; the script checks it reproduces the four B1 values in "
        "`" + B1T + "`). every test row also matches `" + EVT + "`, which the script checks.\n\n"
        "## dev (2086 prompts, 672 complex)\n\n" + md_table(head, dev_rows) +
        "\n\\*\\* c06 dev is the editor's own full-dev scoring (`" + WS + "/dev_scores.json`; full % from its "
        "`.fullfail.json`), not a rescore by the eval run. c06 was picked on these numbers, so they are not a "
        "fair estimate.\n\n"
        "## test (2100 prompts, 714 complex), seed 1, each method scored once\n\n" + md_table(head, test_rows) +
        "\n\\* the paper default loops on most answers, so few are scored and its LPR is not a meaningful number. "
        "random control = a random change to the same entries of the same tensors as c06, scaled to the same "
        "Frobenius norm (`" + EV + "/diffs/random_controls.json`).\n\n"
        "## test, seed 2 (only these four methods were run twice)\n\n" + md_table(head, s2_rows) +
        f"\n## paired differences on test, 95% cluster-bootstrap CI ({st['B']} draws, split v2 groups, "
        f"seed {st['seed_boot']})\n\n"
        "a minus b, in points, from `" + STATS + "`. unscored answers left out, except the last column, where "
        "they count as fail for both methods. pooled = both seeds together.\n\n" +
        md_table(["a", "b", "seed"] + [n for _, n in METRICS] + ["complex LPR, unscored = fail"], comp_rows) +
        "\n## dev guard (vs B1 rows, all 2086 dev prompts)\n\n" +
        md_table(["method", "empty % (d)", "loop % (d)", "mean NLL, nats (d)", "checks 1-3"], guard_rows) +
        "\n## test guard (vs B1 rows, all 2100 test prompts)\n\n" +
        md_table(["method", "empty % (d)", "loop % (d)", "mean NLL, nats (d)", "checks 1-3"], tg_rows) +
        f"\nlimits: empty +1 pt, loops +2 pts, NLL +1.0 nat. on test, guard files exist for c06 and the random "
        f"controls only (`{EV}/guard/`); the random ones are in tables/guard.md. B1 test loops "
        f"{t_loop:.2f}% (`{B1T}`). no guard was run on test for B3 or B4.\n\n"
        "## side effects (seed 1)\n\n"
        "monolingual: score.py LPR on the 2400 monolingual prompts, c06 minus baseline, 95% CI over source rows, "
        "p = exact mcnemar on fail (`" + STATS + "`, `mono`). MMLU-Redux: the questions kept in "
        "`runs/2026-11-08-side-mmlu-redux/ids/all_ok.txt`, greedy answer, accuracy by the lm-eval answer rule, "
        "delta vs the unedited model on the same questions with its 95% CI, p = exact mcnemar (`" + MMLU + "`).\n\n" +
        md_table(["check", "baseline", "edited", "diff [95% CI]", "p"], side))
    write_text(os.path.join(TAB, "partb_2b.md"), text)
    vals.write("partb_2b", TAB)
    print("wrote", os.path.join(TAB, "partb_2b.md"))


if __name__ == "__main__":
    main()
