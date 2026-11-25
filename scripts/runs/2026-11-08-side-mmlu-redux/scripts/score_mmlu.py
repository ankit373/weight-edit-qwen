"""score mmlu-redux outputs (cpu, stdlib only).

usage: score_mmlu.py <items.jsonl> <out prefix> base=<base.jsonl> name=<run.jsonl> ...
main rule = lm-eval mmlu-redux generative v4 (_default_template_yaml:23-29): first regex match
of ([ABCD]) in the completion, no match -> "[invalid]", exact match with the target letter.
strict rule (ours): the stripped completion is a single letter A-D, optionally with "(" ")" "." ":".
"""
import json
import math
import re
import sys
from collections import defaultdict

LMEVAL = re.compile(r"([ABCD])")
STRICT = re.compile(r"^\(?([ABCD])[).:]?$")
GROUPS = ["stem", "humanities", "social_sciences", "other"]


def lmeval_pick(text):
    m = LMEVAL.findall(text)
    return m[0].strip() if m else "[invalid]"


def strict_pick(text):
    m = STRICT.match(text.strip())
    return m.group(1) if m else "[invalid]"


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 2), round(100 * (c + h), 2)


def mcnemar_p(b, c):
    """exact two-sided binomial test on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def load(path):
    with open(path) as f:
        return {r["id"]: r for r in (json.loads(line) for line in f)}


def acc_block(rows, items, key):
    n = len(rows)
    k = sum(r[key] == items[r["id"]]["target"] for r in rows)
    lo, hi = wilson(k, n)
    return {"n": n, "correct": k, "acc": round(100 * k / n, 2) if n else None, "ci95": [lo, hi]}


def paired(base, run, ids, key):
    b = sum(base[i][key] == base[i]["target"] and run[i][key] != run[i]["target"] for i in ids)
    c = sum(base[i][key] != base[i]["target"] and run[i][key] == run[i]["target"] for i in ids)
    n = len(ids)
    d = (c - b) / n
    se = math.sqrt(max(b + c - (c - b) ** 2 / n, 0)) / n
    return {"n": n, "base_right_run_wrong": b, "base_wrong_run_right": c,
            "delta_pts": round(100 * d, 2),
            "delta_ci95": [round(100 * (d - 1.96 * se), 2), round(100 * (d + 1.96 * se), 2)],
            "mcnemar_exact_p": round(mcnemar_p(b, c), 4)}


def main():
    items_path, prefix = sys.argv[1], sys.argv[2]
    runs = dict(a.split("=", 1) for a in sys.argv[3:])
    with open(items_path) as f:
        items = {it["id"]: it for it in (json.loads(line) for line in f)}
    data = {}
    for name, path in runs.items():
        rows = load(path)
        for r in rows.values():
            assert r["target"] == items[r["id"]]["target"], r["id"]
            r["lmeval"] = lmeval_pick(r["completion"])
            r["strict"] = strict_pick(r["completion"])
        data[name] = rows
    base = data["base"]
    report = {}
    for name, rows in data.items():
        ids = sorted(rows)
        rs = [rows[i] for i in ids]
        rep = {"n": len(rs),
               "invalid_lmeval": sum(r["lmeval"] == "[invalid]" for r in rs),
               "invalid_strict": sum(r["strict"] == "[invalid]" for r in rs),
               "hit_max_tokens": sum(r["hit_max_tokens"] for r in rs),
               "mean_new_tokens": round(sum(r["n_new_tokens"] for r in rs) / len(rs), 2),
               "layer_hooks_max": max(r["layer_hooks"] for r in rs),
               "lmeval": acc_block(rs, items, "lmeval"),
               "strict": acc_block(rs, items, "strict"),
               "by_group": {g: acc_block([r for r in rs if r["group"] == g], items, "lmeval")
                            for g in GROUPS}}
        common = [i for i in ids if i in base]
        if name != "base":
            rep["vs_base_same_ids"] = {
                "base_acc_same_ids": acc_block([base[i] for i in common], items, "lmeval"),
                "lmeval": paired(base, rows, common, "lmeval"),
                "strict": paired(base, rows, common, "strict"),
                "identical_output_raw": sum(rows[i]["output_raw"] == base[i]["output_raw"]
                                            for i in common),
                "identical_chat_text": sum(rows[i]["chat_text"] == base[i]["chat_text"]
                                           for i in common),
                "by_group": {g: paired(base, rows, [i for i in common if items[i]["group"] == g],
                                       "lmeval") for g in GROUPS}}
            langs = sorted({rows[i]["language"] for i in common})
            if len(langs) > 1:
                rep["by_language"] = {
                    lg: {"run": acc_block([rows[i] for i in common if rows[i]["language"] == lg],
                                          items, "lmeval"),
                         "vs_base": paired(base, rows,
                                           [i for i in common if rows[i]["language"] == lg],
                                           "lmeval")}
                    for lg in langs}
        report[name] = rep
    with open(prefix + ".json", "w") as f:
        json.dump(report, f, indent=1)
    lines = ["| run | n | acc (lm-eval rule) [95% ci] | strict acc | invalid | stem | humanities | "
             "social sci | other | delta vs base [95% ci] | mcnemar p |", "|" + "---|" * 11]
    for name, rep in report.items():
        g = rep["by_group"]
        v = rep.get("vs_base_same_ids", {}).get("lmeval")
        lines.append(
            f"| {name} | {rep['n']} | {rep['lmeval']['acc']} {rep['lmeval']['ci95']} | "
            f"{rep['strict']['acc']} | {rep['invalid_lmeval']} | "
            + " | ".join(f"{g[x]['acc']} (n {g[x]['n']})" for x in GROUPS) + " | "
            + (f"{v['delta_pts']} {v['delta_ci95']} | {v['mcnemar_exact_p']} |" if v else "- | - |"))
    with open(prefix + ".md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
