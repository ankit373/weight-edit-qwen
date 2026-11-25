"""markdown tables from results.json (no new numbers, formatting only).

usage: make_tables.py <results.json> <out.md>
"""
import json
import sys

res = json.load(open(sys.argv[1]))
L = []
f1 = lambda x: f"{x:+.1f}"
ci = lambda c: f"[{c[0]:+.1f}, {c[1]:+.1f}]"
pv = lambda p: f"{p:.4f}" if p >= 1e-4 else "<0.0001"
NAMES = {"complex_lpr": "complex LPR", "all_lpr": "all LPR", "full_all": "full % (all)", "full_complex": "full % (complex)"}

pvn = lambda p: "-" if p is None else pv(p)
L += ["## main: method a minus method b, test (points). ci = 95% cluster bootstrap over split v2 groups (row-index clusters in the 'ci row' col).",
      "unscored dropped = score.py rule. unscored = fail / pass: both methods filled the same way, group ci.", "",
      "| comparison (a vs b) | seed | metric | a | b | diff | ci group | ci row | p perm prompt | p perm group | diff, unscored = fail [ci] | diff, unscored = pass [ci] |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for comp, by_seed in res["comparisons"].items():
    for tag, r in by_seed.items():
        for k in NAMES:
            e = r[k]
            uf, up = e["unscored_fail"], e["unscored_pass"]
            L.append(f"| {comp} | {tag} | {NAMES[k]} | {e['a']:.1f} | {e['b']:.1f} | {f1(e['diff'])} | {ci(e['ci_group'])} | "
                     f"{ci(e['ci_row'])} | {pvn(e['p_perm_prompt'])} | {pvn(e['p_perm_group'])} | "
                     f"{f1(uf['diff'])} {ci(uf['ci_group'])} | {f1(up['diff'])} {ci(up['ci_group'])} |")
m = res["mono"]
L += ["", "## mono LPR (all), c06 vs baseline, seed 1", "",
      "| c06 | baseline | diff | ci (source, row) clusters | ci prompt | mcnemar fail (c06 better / baseline better, p) |",
      "|---|---|---|---|---|---|",
      f"| {m['c06']:.1f} | {m['baseline']:.1f} | {f1(m['diff'])} | {ci(m['ci_source_row'])} | {ci(m['ci_prompt'])} | "
      f"{m['mcnemar_fail']['a_better']} / {m['mcnemar_fail']['b_better']}, {pv(m['mcnemar_fail']['p_exact'])} |"]
L += ["", "### mcnemar (exact, prompt level; 'a better' = a passes and b fails)", "",
      "| comparison | seed | set / outcome | pairs | a better | b better | p |", "|---|---|---|---|---|---|---|"]
for comp, by_seed in res["comparisons"].items():
    for tag, r in by_seed.items():
        for k in ("mcnemar_complex_fail", "mcnemar_complex_full", "mcnemar_all_fail", "mcnemar_all_full"):
            if k in r:
                m = r[k]
                L.append(f"| {comp} | {tag} | {k[8:]} | {m['n_pairs']} | {m['a_better']} | {m['b_better']} | {pv(m['p_exact'])} |")

L += ["", "## q2: c06 minus ReCoVeR a0.03 off with unscored answers filled in (group ci)", "",
      "| seed | fill (c06 / ReCoVeR) | complex LPR diff [ci] | all LPR diff [ci] | full % all diff [ci] | full % complex diff [ci] |",
      "|---|---|---|---|---|---|"]
for tag, modes in res["q2_unscored_bounds"].items():
    for mode, e in modes.items():
        a, b = mode.split("__")
        L.append(f"| {tag} | {a.split('_')[-1]} / {b.split('_')[-1]} | " + " | ".join(
            f"{f1(e[k]['diff'])} {ci(e[k]['ci_group'])}" for k in NAMES) + " |")

rs = res["q2_reasons"]
L += ["", "### unscored answers by reason (test)", "",
      "| method | complex unscored | complex by reason | all unscored by reason | by dataset | complex hit 100-token cap | fails only from fastText 'unknown' lines (complex / all) |",
      "|---|---|---|---|---|---|---|"]
for lab, r in rs.items():
    if lab.startswith("_"):
        continue
    L.append(f"| {lab} | {r['complex_unscored']} | {r['complex_unscored_by_reason']} | {r['by_reason']} | {r['by_source']} | "
             f"{r['complex_unscored_hit_max_tokens']} | {r['fail_only_unknown_lines_complex']} / {r['fail_only_unknown_lines_all']} |")
LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
L += ["", "### complex unscored by language", "", "| method | " + " | ".join(LANGS) + " |", "|---|" + "---|" * 14]
for lab, r in rs.items():
    if lab.startswith("_"):
        continue
    L.append(f"| {lab} | " + " | ".join(str(r["complex_by_lang"].get(l, 0)) for l in LANGS) + " |")
L += ["", f"overlap of complex unscored ids: { {k: v for k, v in rs['_overlap_complex'].items() if k != 'c06_s1_ids'} }",
      "", "c06 s1 complex unscored, max tokens on any line: " + str(rs["c06_s1"]["complex_unscored_max_line_tokens_hist"]),
      "", "c06 s1 complex unscored, non-empty lines: " + str(rs["c06_s1"]["complex_unscored_nonempty_lines_hist"]),
      "", "c06 s1 complex unscored by group: " + str(rs["c06_s1"]["complex_unscored_by_group"]),
      "", "baseline s1 complex unscored by group: " + str(rs["baseline_s1"]["complex_unscored_by_group"])]

L += ["", "## q3: complex LPR by target language (test). diffs = c06 minus other, pooled over seeds, 95% group ci", "",
      "| lang | c06 s1 / s2 | ReCoVeR s1 / s2 | baseline s1 / s2 | c06 - ReCoVeR pooled [ci] | c06 - baseline pooled [ci] | flag |",
      "|---|---|---|---|---|---|---|"]
for lang, e in res["q3_lang"].items():
    rv, bl = e["c06_vs_recover_pooled"], e["c06_vs_baseline_pooled"]
    flags = []
    for b in ("recover", "baseline"):
        for tag in ("s1", "s2", "pooled"):
            x = e[f"c06_vs_{b}_{tag}"]
            if x["worse"]:
                flags.append(f"worse vs {b} {tag}")
    L.append(f"| {lang} | {e['c06_s1']:.1f} / {e['c06_s2']:.1f} | {e['recover_s1']:.1f} / {e['recover_s2']:.1f} | "
             f"{e['baseline_s1']:.1f} / {e['baseline_s2']:.1f} | {f1(rv['diff'])} {ci(rv['ci_group'])} | "
             f"{f1(bl['diff'])} {ci(bl['ci_group'])} | {', '.join(flags) or '-'} |")
L += ["", "### per seed, c06 - ReCoVeR by language [group ci]", "", "| lang | s1 | s2 |", "|---|---|---|"]
for lang, e in res["q3_lang"].items():
    L.append(f"| {lang} | " + " | ".join(f"{f1(e[f'c06_vs_recover_{t}']['diff'])} {ci(e[f'c06_vs_recover_{t}']['ci_group'])}" for t in ("s1", "s2")) + " |")
open(sys.argv[2], "w").write("\n".join(L) + "\n")
print("\n".join(L))
