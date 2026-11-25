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

L += ["## q1: c02 minus other method, test (points). ci = 95% cluster bootstrap (split v2 groups; row-index clusters in brackets col).", "",
      "| comparison | seed | metric | c02 | other | diff | ci group | ci row | p perm prompt | p perm group |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for comp, by_seed in res["comparisons"].items():
    for tag, r in by_seed.items():
        for k in NAMES:
            e = r[k]
            L.append(f"| {comp} | {tag} | {NAMES[k]} | {e['a']:.1f} | {e['b']:.1f} | {f1(e['diff'])} | {ci(e['ci_group'])} | "
                     f"{ci(e['ci_row'])} | {pv(e['p_perm_prompt'])} | {pv(e['p_perm_group'])} |")
L += ["", "### mcnemar (exact, prompt level; a = c02, b = other; 'a better' = c02 passes and other fails)", "",
      "| comparison | seed | set / outcome | pairs | c02 better | other better | p |", "|---|---|---|---|---|---|---|"]
for comp, by_seed in res["comparisons"].items():
    for tag, r in by_seed.items():
        for k in ("mcnemar_complex_fail", "mcnemar_complex_full", "mcnemar_all_fail", "mcnemar_all_full"):
            if k in r:
                m = r[k]
                L.append(f"| {comp} | {tag} | {k[8:]} | {m['n_pairs']} | {m['a_better']} | {m['b_better']} | {pv(m['p_exact'])} |")

L += ["", "## q2: c02 minus ReCoVeR 0.03 with unscored answers filled in (group ci)", "",
      "| seed | fill (c02 / ReCoVeR) | complex LPR diff [ci] | all LPR diff [ci] | full % all diff [ci] | full % complex diff [ci] |",
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
L += ["", f"overlap of complex unscored ids: { {k: v for k, v in rs['_overlap_complex'].items() if k != 'c02_s1_ids'} }",
      "", "c02 s1 complex unscored, max tokens on any line: " + str(rs["c02_s1"]["complex_unscored_max_line_tokens_hist"]),
      "", "c02 s1 complex unscored, non-empty lines: " + str(rs["c02_s1"]["complex_unscored_nonempty_lines_hist"]),
      "", "c02 s1 complex unscored by group: " + str(rs["c02_s1"]["complex_unscored_by_group"]),
      "", "baseline s1 complex unscored by group: " + str(rs["baseline_s1"]["complex_unscored_by_group"])]

L += ["", "## q3: complex LPR by target language (test). diffs = c02 minus other, pooled over seeds, 95% group ci", "",
      "| lang | c02 s1 / s2 | ReCoVeR s1 / s2 | baseline s1 / s2 | c02 - ReCoVeR pooled [ci] | c02 - baseline pooled [ci] | flag |",
      "|---|---|---|---|---|---|---|"]
for lang, e in res["q3_lang"].items():
    rv, bl = e["c02_vs_recover_pooled"], e["c02_vs_baseline_pooled"]
    flags = []
    for b in ("recover", "baseline"):
        for tag in ("s1", "s2", "pooled"):
            x = e[f"c02_vs_{b}_{tag}"]
            if x["worse"]:
                flags.append(f"worse vs {b} {tag}")
    L.append(f"| {lang} | {e['c02_s1']:.1f} / {e['c02_s2']:.1f} | {e['recover_s1']:.1f} / {e['recover_s2']:.1f} | "
             f"{e['baseline_s1']:.1f} / {e['baseline_s2']:.1f} | {f1(rv['diff'])} {ci(rv['ci_group'])} | "
             f"{f1(bl['diff'])} {ci(bl['ci_group'])} | {', '.join(flags) or '-'} |")
L += ["", "### per seed, c02 - ReCoVeR by language [group ci]", "", "| lang | s1 | s2 |", "|---|---|---|"]
for lang, e in res["q3_lang"].items():
    L.append(f"| {lang} | " + " | ".join(f"{f1(e[f'c02_vs_recover_{t}']['diff'])} {ci(e[f'c02_vs_recover_{t}']['ci_group'])}" for t in ("s1", "s2")) + " |")
open(sys.argv[2], "w").write("\n".join(L) + "\n")
print("\n".join(L))
