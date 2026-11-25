# formats results.json as markdown tables. no new numbers.
# usage: python3 -I -B make_tables.py results.json tables.md
import json
import sys

R = json.load(open(sys.argv[1]))
NAME = {"cross|baseline": "baseline", "cross|c06": "c06", "cross|recover_a0.03": "ReCoVeR 0.03",
        "cross|instr_end": "instr_end", "mono|baseline": "mono-base", "mono|c06": "mono-c06"}
o = []


def f(x):
    v, c = x
    return f"{v} [{c[0]}, {c[1]}]"


def h(x):
    k, v, c = x
    return f"{k} ({v}) [{c[0]}, {c[1]}]"


for sub in ("all", "high"):
    S = R[sub]
    o.append(f"\n# subset: {S['subset']} (n {S['n_items']})\n")
    o.append("## judge label shares by fastText half (count (%) [wilson 95%])\n")
    o.append("| method | half | n | full_lang | mixed | wrong | garbage | not full_lang |")
    o.append("|---|---|---|---|---|---|---|---|")
    for k, e in S["methods"].items():
        for hn, hv in e["halves"].items():
            o.append(f"| {NAME[k]} | {hn} | {hv['n']} | {h(hv['F'])} | {h(hv['M'])} | {h(hv['W'])} | "
                     f"{h(hv['G'])} | {h(hv['fail'])} |")
    o.append("\n## weighted to the full set (714 complex / 200 en), % [cluster bootstrap 95%]\n")
    o.append("| method | full_lang | mixed | wrong | garbage | not full_lang | wrong+garbage | not full_lang, ft-scored only | coverage |")
    o.append("|---|---|---|---|---|---|---|---|---|")
    for k, e in S["methods"].items():
        w = e["weighted"]
        o.append(f"| {NAME[k]} | {f(w['F'])} | {f(w['M'])} | {f(w['W'])} | {f(w['G'])} | {f(w['fail'])} | "
                 f"{f(w['whole'])} | {f(w['fail_scored'])} | {round(100 * e['coverage'], 1)}% |")
    o.append("\n## weights (stratum: size / n kept = weight)\n")
    for k, e in S["methods"].items():
        o.append(f"- {NAME[k]}: " + "; ".join(f"{s} {v['size']}/{v['n_kept']}={v['weight']}"
                                               for s, v in e["strata"].items()))
    o.append("\n## agreement with fastText (rows fastText, cols judge F/M/W/G)\n")
    o.append("| method | pass | partial | full | unscored | kappa 3-class [ci] | kappa pass/fail [ci] | ft flagged, judge full_lang | ft pass, judge not full_lang |")
    o.append("|---|---|---|---|---|---|---|---|---|")
    for k, e in S["methods"].items():
        cm = e["confusion"]
        cell = lambda ft: "/".join(str(cm[ft][x]) for x in "FMWG")
        a, b = e["ft_flag_judge_full"], e["ft_pass_judge_fail"]
        o.append(f"| {NAME[k]} | {cell('pass')} | {cell('partial')} | {cell('full')} | {cell('unscored')} | "
                 f"{f(e['kappa3'])} | {f(e['kappa2'])} | {a[0]}/{a[1]} ({a[2]}) [{a[3][0]}, {a[3][1]}] | "
                 f"{b[0]}/{b[1]} ({b[2]}) [{b[3][0]}, {b[3][1]}] |")
    o.append("\n## by target language (n / judge not full_lang / low confidence)\n")
    for k, e in S["methods"].items():
        o.append(f"- {NAME[k]}: " + ", ".join(f"{l} {v[0]}/{v[1]}/{v[2]}"
                                               for l, v in e["by_language_n_notfull_low"].items()))
    o.append("\n## differences of weighted judge rates (points [cluster bootstrap 95%], same draws)\n")
    for k, v in S["diffs"].items():
        o.append(f"- {k}: {f(v)}")
    for nm in ("paired_c06_recover", "paired_mono"):
        p = S[nm]
        o.append(f"\n## {nm} (n {p['n']})\n")
        o.append("- table (first/second): " + ", ".join(f"{k} {v}" for k, v in p["table"].items()))
        o.append("- " + "; ".join(f"{k}: {v}" for k, v in p.items() if k not in ("table", "rows", "n")))
    o.append("\n## mono by source (weighted judge not-full_lang %)\n")
    for k, v in S["mono_by_source"].items():
        o.append(f"- {k}: n {v['n']}, judge {v['fail_w']}%, fastText flagged in sample {v['ft_fail_in_sample']}")
o.append(f"\nlow-confidence items by method: {R['low_by_method']}")
o.append(f"\nduplicate-answer groups: {R['dup_groups']}, same label in {R['dup_groups_same_label']}")
open(sys.argv[2], "w").write("\n".join(o) + "\n")
