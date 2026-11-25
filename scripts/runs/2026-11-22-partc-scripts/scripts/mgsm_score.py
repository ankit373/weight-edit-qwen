"""MGSM answer rule and accuracy (PROTOCOL.md section 3). stdlib only.

usage: mgsm_score.py <rows.jsonl> <prompts.jsonl> <out_prefix>
writes <out_prefix>.rows.jsonl (per row: answer, correct, has_prefix, hit_max_tokens) and
<out_prefix>.json (accuracy over all, per language, en vs the other six; cap-hit and no-prefix shares).
parse_answer and score_mgsm: simple-evals mgsm_eval.py (data/partc/mgsm/ref/simple_evals_mgsm_eval.py.txt),
ported line for line. the response text is the row's `completion` (special tokens skipped).
"""
import json
import re
import sys

LANGS = ["en", "de", "es", "fr", "ja", "ru", "zh"]
# simple-evals LANG_TO_ANSWER_PREFIX, the 7 languages used here
LANG_TO_ANSWER_PREFIX = {"en": "Answer", "de": "Antwort", "es": "Respuesta", "fr": "Réponse",
                         "ja": "答え", "ru": "Ответ", "zh": "答案"}


def parse_answer(answer: str, answer_prefix: str) -> str:
    if answer_prefix not in answer:
        return ""

    answer_text = answer.split(answer_prefix)[-1].strip()

    # find all the numbers (including decimals) in the string
    numbers = re.findall(r"\d+\.?\d*", answer_text.replace(",", ""))

    # return the first number (removing trailing decimal point if present),
    # or an empty string if there were no numbers
    return numbers[-1].rstrip(".") if numbers else ""


def score_mgsm(target: str, prediction: str) -> bool:
    if "." in prediction:
        prediction = prediction.rstrip("0").rstrip(".")

    target = target.replace(",", "")
    prediction = prediction.replace(",", "")

    return target == prediction


def score_row(r, item):
    lang = item["language"]
    prefix = LANG_TO_ANSWER_PREFIX[lang]
    assert item["answer_prefix"] == prefix, (item["id"], item["answer_prefix"])
    text = r["completion"]
    ans = parse_answer(text, prefix)
    return {"id": r["id"], "language": lang, "item": item["item"], "target": item["target"],
            "answer": ans, "correct": int(score_mgsm(item["target"], ans)),
            "has_prefix": int(prefix in text), "hit_max_tokens": int(bool(r.get("hit_max_tokens")))}


def share(rs, k):
    return round(100 * sum(r[k] for r in rs) / len(rs), 2) if rs else None


def main():
    rows_path, prompts_path, prefix = sys.argv[1:4]
    items = {it["id"]: it for it in map(json.loads, open(prompts_path, encoding="utf-8"))}
    rows = [json.loads(line) for line in open(rows_path, encoding="utf-8")]
    out = [score_row(r, items[r["id"]]) for r in rows]
    with open(prefix + ".rows.jsonl", "w") as f:
        for d in out:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    rep = {"rows": rows_path, "n": len(out), "n_expected": len(items),
           "acc": share(out, "correct"), "hit_max_tokens_pct": share(out, "hit_max_tokens"),
           "no_prefix_pct": round(100 - share(out, "has_prefix"), 2) if out else None,
           "by_language": {lg: {"n": len(s), "acc": share(s, "correct"),
                                "hit_max_tokens_pct": share(s, "hit_max_tokens")}
                           for lg in LANGS for s in [[d for d in out if d["language"] == lg]]},
           "en": share([d for d in out if d["language"] == "en"], "correct"),
           "non_en": share([d for d in out if d["language"] != "en"], "correct")}
    with open(prefix + ".json", "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("n", "acc", "en", "non_en", "hit_max_tokens_pct", "no_prefix_pct")}))


if __name__ == "__main__":
    main()
