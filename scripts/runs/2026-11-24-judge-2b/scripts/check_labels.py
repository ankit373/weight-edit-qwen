"""check labels/*.jsonl against the existing wrong_lang.py and score.py files. stdlib only.

usage: check_labels.py <out.json>   (run from the project root)
"""
import json
import sys

B1 = "runs/2026-11-11-gate5b-baseline/scores"
IE = "runs/2026-11-13-gate5b-instr-end/scores"
RC = "runs/2026-11-14-gate5b-recover/scores"
EV = "runs/2026-11-17-gate5b-eval/scores"
SETS = {
    # name: (labels file, wrong_lang json, score json, source, language filter)
    "baseline": ("baseline", f"{B1}/baseline_test_wrong_lang.json", f"{B1}/baseline_test.json", "complex_prompts", None),
    "c06": ("c06", f"{EV}/final_test_wrong_lang.json", f"{EV}/final_test.json", "complex_prompts", None),
    "recover_a0.03": ("recover_a0.03", f"{RC}/recover_a0.03_off_test_wrong_lang.json",
                      f"{RC}/recover_a0.03_off_test.json", "complex_prompts", None),
    "instr_end": ("instr_end", f"{IE}/instr_end_test_wrong_lang.json", f"{IE}/instr_end_test.json", "complex_prompts", None),
    "baseline_mono_en": ("baseline_mono_en", f"{B1}/baseline_mono_wrong_lang.json", f"{B1}/baseline_mono.json", None, "en"),
    "c06_mono_en": ("c06_mono_en", f"{EV}/final_mono_wrong_lang.json", f"{EV}/final_mono.json", None, "en"),
}

report, ok = {}, True
for name, (lab, wl, sc, src, lang) in SETS.items():
    rows = [json.loads(l) for l in open(f"runs/2026-11-24-judge-2b/labels/{lab}.jsonl")]
    ids = {r["id"] for r in rows}
    mine = {r["id"]: r for r in rows if r["status"] in ("partial", "full")}
    theirs = {}
    for e in json.load(open(wl))["failing_responses"]:
        if e["id"] in ids:
            theirs[e["id"]] = e
    same_ids = set(mine) == set(theirs)
    same_lab = same_ids and all(
        mine[i]["status"] == ("full" if theirs[i]["full_response_wrong"] else "partial")
        and [x for x in mine[i]["line_labels"] if x != mine[i]["language"]] == theirs[i]["bad_labels"]
        for i in mine)
    rec = {"n": len(rows), "flagged_mine": len(mine), "flagged_wrong_lang_json": len(theirs),
           "same_ids": same_ids, "same_status_and_bad_labels": same_lab}
    if sc:
        cells = json.load(open(sc))
        if src:
            cell = [c for c in cells if c["source"] == src and c["language"] == "all"]
        else:
            cell = [c for c in cells if c["source"] != "all" and c["language"] == lang]
        rec["n_scored_score_json"] = sum(c["n_scored"] for c in cell)
        rec["n_scored_mine"] = sum(r["status"] != "unscored" for r in rows)
        rec["same_n_scored"] = rec["n_scored_score_json"] == rec["n_scored_mine"]
        ok &= rec["same_n_scored"]
    ok &= same_ids and same_lab
    report[name] = rec

report["all_ok"] = ok
json.dump(report, open(sys.argv[1], "w"), indent=1)
print(json.dumps(report, indent=1))
