"""step 1 summary: rates, failure kinds, switch position, prompt wording. dev only.

usage: step1_summary.py <step1_dev_behaviour.jsonl> <out.json>
adds the qwen token index of the first wrong-language line (re-tokenized completion, approx).
"""
import collections
import json
import statistics
import sys

from transformers import AutoTokenizer

MODEL, REVISION = "Qwen/Qwen3.5-2B", "15852e8c16360a2fea060d615a32b45270f8a8fc"  # part B: 2B pin
NONLATIN = {"ar", "hi", "ja", "ko", "ru", "zh"}
inp, out = sys.argv[1], sys.argv[2]
tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
rs = [json.loads(l) for l in open(inp)]


def rate(group):
    sc = [r for r in group if r["scored"]]
    f = sum(r["fail"] for r in sc)
    return {"n": len(group), "scored": len(sc), "fail": f,
            "fail_pct": round(100 * f / len(sc), 1) if sc else None}


def by(keyf, group):
    d = collections.defaultdict(list)
    for r in group:
        d[keyf(r)].append(r)
    return {str(k): rate(v) for k, v in sorted(d.items(), key=lambda kv: str(kv[0]))}


def bucket_tokens(n):
    for edge in (64, 128, 256, 512, 1024, 2048):
        if n < edge:
            return f"<{edge}"
    return ">=2048"


fails = [r for r in rs if r["fail"]]
for r in fails:  # token index of the first wrong-language line
    enc = tok(r["completion"], return_offsets_mapping=True, add_special_tokens=False)
    c = r["first_bad_char"]
    r["first_bad_token"] = next((i for i, (a, b) in enumerate(enc["offset_mapping"]) if b > c), None)

res = {"overall": rate(rs), "by_source": by(lambda r: r["source"], rs),
       "by_source_lang": by(lambda r: (r["source"], r["language"]), rs),
       "by_lang": by(lambda r: r["language"], rs)}

# failure kind and switched-to language
res["kind"] = dict(collections.Counter((r["source"], r["kind"]) for r in fails).most_common())
res["kind"] = {f"{k[0]}/{k[1]}": v for k, v in res["kind"].items()}
lab = collections.Counter(l for r in fails for l in r["bad_labels"])
res["bad_line_labels"] = dict(lab.most_common())
maj = collections.Counter(collections.Counter(r["bad_labels"]).most_common(1)[0][0] for r in fails)
res["majority_bad_label_per_failed_response"] = dict(maj.most_common())
res["whole_label_failed"] = dict(collections.Counter(r["whole_label"] for r in fails).most_common())
res["any_en_line_in_failed"] = sum("en" in r["bad_labels"] for r in fails)

# where the switch happens
res["first_bad_line_index"] = dict(collections.Counter(min(r["first_bad_line"], 10) for r in fails).most_common())
res["first_bad_is_first_checked_line"] = sum(r["first_bad_checked_rank"] == 0 for r in fails)
res["first_bad_is_raw_line_0"] = sum(r["first_bad_line"] == 0 for r in fails)
part = [r for r in fails if r["kind"] == "partial"]
res["partial_first_bad_checked_rank0"] = sum(r["first_bad_checked_rank"] == 0 for r in part)
res["partial_n"] = len(part)
toks = [r["first_bad_token"] for r in fails if r["first_bad_token"] is not None]
res["first_bad_token"] = {
    "n": len(toks), "median": statistics.median(toks), "eq0": sum(t == 0 for t in toks),
    "lt5": sum(t < 5 for t in toks), "lt20": sum(t < 20 for t in toks),
    "ge50": sum(t >= 50 for t in toks)}
ptoks = [r["first_bad_token"] for r in part if r["first_bad_token"] is not None]
res["first_bad_token_partial"] = {"n": len(ptoks), "median": statistics.median(ptoks) if ptoks else None,
                                  "eq0": sum(t == 0 for t in ptoks), "lt20": sum(t < 20 for t in ptoks)}
# what partial failures look like: does the response start in target and switch to english, or the other way
order = collections.Counter()
for r in part:
    ch = [x for x in r["lines"] if x["checked"]]
    seq = ["T" if x["label"] == r["language"] else "W" for x in ch]
    order["starts_wrong" if seq[0] == "W" else "starts_target"] += 1
res["partial_start"] = dict(order)

# prompt wording / position
res["by_source_where"] = by(lambda r: (r["source"], r["lang_name_where"]), rs)
res["by_source_template"] = by(lambda r: (r["source"], r["template"]), rs)
res["by_source_prompt_tokens"] = by(lambda r: (r["source"], bucket_tokens(r["n_prompt_tokens"])), rs)
cx = [r for r in rs if r["source"] == "complex_prompts"]
res["complex_where_x_len"] = by(lambda r: (r["lang_name_where"], "long" if r["n_prompt_tokens"] >= 512 else "short"), cx)
res["by_source_hitmax"] = by(lambda r: (r["source"], r["hit_max_tokens"]), rs)

# fastText vs script, non-latin targets: a wrong line that is mostly target script is a suspect detector error
susp = []
for r in fails:
    if r["language"] not in NONLATIN:
        continue
    for x in r["lines"]:
        if x["checked"] and x["label"] != r["language"] and (x["tshare"] or 0) >= 0.5:
            susp.append((r["id"], x["i"], x["label"], x["tshare"]))
nl_fail = [r for r in fails if r["language"] in NONLATIN]
res["nonlatin_failed"] = len(nl_fail)
res["nonlatin_bad_lines"] = sum(r["n_bad"] for r in nl_fail)
res["nonlatin_bad_lines_target_script_ge50"] = len(susp)
res["nonlatin_failed_all_bad_lines_target_script_ge50"] = sum(
    all((x["tshare"] or 0) >= 0.5 for x in r["lines"] if x["checked"] and x["label"] != r["language"])
    for r in nl_fail)
res["nonlatin_suspect_examples"] = susp[:40]
res["unscored_ids"] = [r["id"] for r in rs if not r["scored"]]

json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
with open(out.replace(".json", "_first_bad_token.jsonl"), "w") as f:
    for r in fails:
        f.write(json.dumps({"id": r["id"], "kind": r["kind"], "first_bad_line": r["first_bad_line"],
                            "first_bad_char": r["first_bad_char"], "first_bad_token": r["first_bad_token"]}) + "\n")
print(json.dumps({k: v for k, v in res.items() if k not in ("by_source_lang", "nonlatin_suspect_examples")}, indent=1))
