"""reformat the part C stats, guard and per-row files into one markdown table file. no new statistics:
every value is copied from a stats.json / guard.json, or is a plain count of per-row flags. stdlib only."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RUN, TAB, load, p, write_text  # noqa: E402

LPR_SETS = [("m-arenahard", "scores/{m}/m-arenahard"), ("xl-alpacaeval", "scores/nc-sa/xl-alpacaeval/{m}"),
            ("lcb-greedy", "scores/{m}/lcb-greedy"), ("lcb-long", "scores/{m}/lcb-long")]
SIDE_SETS = [("global-mmlu", "scores/{m}/global-mmlu"), ("mgsm", "scores/{m}/mgsm"), ("ifeval", "scores/{m}/ifeval")]
MODELS = ["08", "2b"]


def ci(c):
    return f"{c['diff']:+.1f} [{c['ci'][0]:+.1f}, {c['ci'][1]:+.1f}] p {c['p_perm_group']:.4f}"


def count_rows(rel, key, val):
    n = k = 0
    with open(p(rel), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            k += int(r.get(key) == val)
    return k, n


def lpr_block(name, folder, m):
    rel = f"{RUN}/{folder.format(m=m)}/stats.json"
    d = load(rel)
    out = [f"## {m} {name} (`{rel}`, rows {d['n_rows']}, clusters {d['n_clusters']})", ""]
    out.append("| method | lpr drop | lpr fail | lpr pass | full % drop | wpr | late switch % | loop % | cap % "
               "| unscored (count of scored=0 in perrow) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for meth, o in d["observed"].items():
        perrow = d["inputs"][meth].split(",")[0]
        uns, n = count_rows(perrow, "scored", 0)
        dr = o["drop"]
        out.append(f"| {meth} | {dr['lpr']:.1f} | {o['fail']['lpr']:.1f} | {o['pass']['lpr']:.1f} "
                   f"| {dr['full_pct']:.2f} | {dr['wpr']:.1f} | {dr['late_switch_pct']:.1f} | {dr['loop_pct']:.2f} "
                   f"| {dr['cap_pct']:.1f} | {uns} of {n} |")
    out += ["", "| a vs b | lpr drop | lpr fail | lpr pass | full % drop | loop % drop | mcnemar a better / b better, p |",
            "|---|---|---|---|---|---|---|"]
    for k, c in d["comparisons"].items():
        mc = c.get("mcnemar", {})
        mcs = f"{mc.get('a_better')} / {mc.get('b_better')}, {mc.get('p_exact', float('nan')):.4f}" if mc else ""
        out.append(f"| {k} | {ci(c['unscored_drop']['lpr'])} | {ci(c['unscored_fail']['lpr'])} "
                   f"| {ci(c['unscored_pass']['lpr'])} | {ci(c['unscored_drop']['full_pct'])} "
                   f"| {ci(c['unscored_drop']['loop_pct'])} | {mcs} |")
    langs = []
    for k, c in d["comparisons"].items():
        for lk, lv in c["unscored_drop"].items():
            if lk.startswith("lpr_") and (lv["ci"][0] > 0 or lv["ci"][1] < 0):
                langs.append(f"{k} {lk[4:]} {lv['diff']:+.1f} [{lv['ci'][0]:+.1f}, {lv['ci'][1]:+.1f}]")
    out += ["", "per-language cells with a CI that excludes 0 (drop rule): " + ("; ".join(langs) or "none"), ""]
    if name == "lcb-long":
        loops_dir = os.path.dirname(rel)
        parts = []
        for meth in d["observed"]:
            f = f"{loops_dir}/{meth}.loops.jsonl"
            k, n = count_rows(f, "starts_with_old", 1)
            parts.append(f"{meth} {k} of {n}")
        out += ["long400 answers that start with the 100-token row (`starts_with_old`): " + "; ".join(parts), ""]
    gs = sys_guard(folder.format(m=m), list(d["observed"]))
    if gs:
        out += gs
    return out


def sys_guard(folder, methods):
    out = []
    for meth in methods:
        rel = f"{RUN}/{folder}/{meth}.guard.json"
        if os.path.exists(p(rel)):
            g = load(rel)
            dl = g["delta"]
            out.append(f"| {meth} | {g['new']['loop_pct']:.2f} ({dl['loop_pts']:+.2f}) | {g['new']['nll_mean']:.3f} "
                       f"({dl['nll_nats']:+.3f}) | {g['new']['empty_pct']:.1f} | "
                       f"{'pass' if g['pass_1_to_3'] else 'fail ' + ','.join(g['failed_checks'])} | `{rel}` |")
    if not out:
        return []
    base = load(f"{RUN}/{folder}/{methods[1]}.guard.json")["baseline"]
    head = ["guard vs baseline (baseline loop % {:.2f}, mean NLL {:.3f}):".format(base["loop_pct"], base["nll_mean"]),
            "", "| method | loop % (change) | mean NLL (change) | empty % | guard | source |", "|---|---|---|---|---|---|"]
    return head + out + [""]


def side_block(name, folder, m):
    rel = f"{RUN}/{folder.format(m=m)}/stats.json"
    d = load(rel)
    out = [f"## {m} {name} (`{rel}`, rows {d['n_rows']}, clusters {d['n_clusters']})", ""]
    for meth, o in d["observed"].items():
        out.append(f"- observed {meth}: " + ", ".join(f"{k} {v:.2f}" for k, v in o["drop"].items()))
    out.append("")
    for k, c in d["comparisons"].items():
        al = c["all"]
        mc = c["mcnemar"]
        dm = c["damage"]
        out.append(f"### {k}: {dm['label']}, more than 2 points ruled out: {dm['ruled_out_over_2pts']}")
        out.append(f"- mcnemar: a better {mc['a_better']}, b better {mc['b_better']}, p {mc['p_exact']:.4f}, "
                   f"pairs {mc['n_pairs']}")
        out.append("- language leads: " + json.dumps(c.get("language_leads", [])))
        for mk, mv in al.items():
            out.append(f"- {mk}: a {mv['a']:.2f}, b {mv['b']:.2f}, {ci(mv)}")
        out.append("")
    return out


def main():
    lines = ["# part C numbers, reformatted from the run files", "",
             "made by `runs/2026-11-24-partc-figures/scripts/extract.py`. values are copied from each stats.json "
             "(`observed`, `comparisons`) and guard.json; the only new arithmetic is counting per-row flags "
             "(`scored` = 0 in `*.perrow.jsonl`, `starts_with_old` = 1 in `*.loops.jsonl`). CIs are 95% paired "
             "cluster bootstrap, p is the group-swap permutation p, both from stats_c.py.", ""]
    for m in MODELS:
        for name, folder in LPR_SETS:
            lines += lpr_block(name, folder, m)
        gvs = f"{RUN}/scores/{m}/lcb-greedy/stats_greedy_vs_s1.json"
        d = load(gvs)
        lines += [f"## {m} greedy minus seed 1 sampled (`{gvs}`)", "", "| comparison | lpr drop | full % drop |",
                  "|---|---|---|"]
        for k, c in d["comparisons"].items():
            lines.append(f"| {k} | {ci(c['unscored_drop']['lpr'])} | {ci(c['unscored_drop']['full_pct'])} |")
        lines.append("")
        for name, folder in SIDE_SETS:
            lines += side_block(name, folder, m)
    write_text(os.path.join(TAB, "partc_numbers.md"), "\n".join(lines))
    print("wrote", os.path.join(TAB, "partc_numbers.md"))


if __name__ == "__main__":
    main()
