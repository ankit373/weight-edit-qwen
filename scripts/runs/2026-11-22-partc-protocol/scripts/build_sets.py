"""build the part C prompt sets from downloaded files (stdlib only, files read as data).

usage (from the project root, under envs/run-sandboxed.sh, python -I):
  build_sets.py gmmlu-select   writes data/partc/global-mmlu/select.json (row_idx to fetch)
  build_sets.py all            builds every set whose raw files are present
seed 20261122, a fresh random.Random(SEED) per set. no model, no network.
"""
import collections
import csv
import glob
import hashlib
import json
import os
import random
import re
import sys
import unicodedata

SEED = 20261122
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = os.path.join(ROOT, "data", "partc")
LCB = os.path.join(ROOT, "external", "lcb_test_sets", "test_sets")
LANGS14 = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
NAME = dict(ar="Arabic", de="German", es="Spanish", fr="French", hi="Hindi", id="Indonesian",
            it="Italian", ja="Japanese", ko="Korean", pt="Portuguese", ru="Russian",
            tr="Turkish", vi="Vietnamese", zh="Chinese")


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_lines(path, lines):
    with open(path, "w") as f:
        f.write("".join(x + "\n" for x in lines))


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


# ---- dedupe keys: same rule as splits/make_split_v2.py (strip_instruction + key), plus NFKC

def strip_instruction(text, lang):
    n = NAME[lang]
    t = re.sub(rf"\bWrite your response using {n}\b\.?", " ", text)
    t = re.sub(rf"\b(Reply|Respond|Answer|Write|Make sure to respond|respond|write) in {n}\b\.?",
               " ", t)
    t = re.sub(rf"\b[Uu]s(e|ing) {n}\b(?!-)\.?", " ", t)
    t = re.sub(rf"\bin {n}\b(?!-)", " ", t)
    return t


def norm(text):
    t = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"[^\W_]+", t))


def shingles(k):
    w = k.split()
    return {" ".join(w[i:i + 3]) for i in range(max(1, len(w) - 2))}


def lcb_english():
    """every english LCB prompt: monolingual en files, cross-lingual prompts raw and stripped."""
    exact, keys, n_rows = set(), {}, 0
    for path in sorted(glob.glob(os.path.join(LCB, "*", "*", "*.csv"))):
        task, src, fname = path.split(os.sep)[-3:]
        lang = fname[:-4]
        if task == "monolingual" and lang != "en":
            continue
        with open(path, newline="") as f:
            for i, r in enumerate(csv.DictReader(f)):
                n_rows += 1
                pid = f"{task}/{src}/{lang}/{i}"
                texts = [r["prompt"]]
                if task == "crosslingual":
                    texts.append(strip_instruction(r["prompt"], lang))
                for t in texts:
                    exact.add(t.strip())
                    keys.setdefault(norm(t), pid)
    return exact, keys, n_rows


def dedupe(items, lcb):
    """items: [(item_id, english_text)]. exact or normalised match drops; 3-gram jaccard >= 0.8
    (split v2 rule) is listed for information only."""
    exact, keys, _ = lcb
    sh_lcb = [(k, shingles(k)) for k in keys]
    out = {"exact": [], "normalised": [], "near_info_only": []}
    for iid, text in items:
        k = norm(text)
        if text.strip() in exact:
            out["exact"].append([iid, keys.get(k)])
        elif k in keys:
            out["normalised"].append([iid, keys[k]])
        else:
            s = shingles(k)
            for lk, ls in sh_lcb:
                j = len(s & ls) / len(s | ls)
                if j >= 0.8:
                    out["near_info_only"].append([iid, keys[lk], round(j, 3)])
                    break
    return out


def cross_rows(source, base_ids, text_of):
    """main rows (line at the start) and instruction-at-end rows, language-major order."""
    main, end = [], []
    for lang in LANGS14:
        line = f"Answer in {NAME[lang]}."
        for b in base_ids:
            t = text_of[b].strip()
            common = {"id": f"crosslingual/{source}/{lang}/{b}", "task": "crosslingual",
                      "source": source, "language": lang, "base_id": b, "lang_line": line,
                      "prompt_english": t}
            main.append({**common, "line_position": "start", "prompt": f"{line}\n\n{t}"})
            end.append({**common, "line_position": "end", "prompt": f"{t}\n\n{line}"})
    return main, end


# ---- m-ArenaHard code rule (fixed before any part C model output exists)

CODE_TERMS = [
    "python", "javascript", "typescript", "java", r"c\+\+", "c#", "golang", "rust", "sql",
    "html", "css", "php", "ruby", "swift", "kotlin", "scala", "perl", "bash", "shell",
    "powershell", "vba", "excel", "matlab", "julia", "haskell", "lisp", "fortran", "assembly",
    "verilog", "vhdl", "lua", "gdscript", "arduino", "latex", "react", "vue", "angular",
    "django", "flask", "fastapi", r"node\.?js", "pandas", "numpy", "pytorch", "tensorflow",
    "keras", "jax", "matplotlib", "seaborn", "docker", "kubernetes", "terraform", "nginx",
    "linux", "git", "github", "regex", "json", "yaml", "xml", "api", "sdk", "code", "coding",
    "script", "scripts", "program", "programming", "function", "compile", "debug",
    "implement", "algorithm", "roblox", "unity", "godot",
]
# v2 (2026-11-22): added after reading the english text of the v1 sample (no model output
# existed). v1 let through scraping, smart contracts, a fuzzer, a cocotb testbench, sveltekit,
# GAMS, an npcap service, an array puzzle and a website slider.
CODE_TERMS_V2_ADD = [
    "scrape", "scraping", "scraper", "smart contract", "solidity", "fuzz", "fuzzer", "fuzzing",
    "testbench", "cocotb", "svelte", "sveltekit", "gams", "npcap", "array", "arrays",
    "website", "websites", "subarray",
]
# v3 (2026-11-22, final): added after reading the english text of the v2 sample. frozen here;
# no further change after this point. still a keyword rule, so some code-near prompts remain.
CODE_TERMS_V3_ADD = [
    "sklearn", "scikit", "huggingface", "jq", "awk", "sed", "grep", "streamlit", "plugin",
    "extension", "octave", "codeql", "console", "cron", "gherkin", "cucumber", "http", "https",
    "url", "tls", "sni", "browser", "query", "queries", "database", "app", "apps", "wordpress",
    "after effects", "vectordb", "snowflake", "framework", "library", "package", "software",
    "server", "dataset", "pipeline", "hardware", "keyboard", "computer", "engine", "engines",
]
TERM_RE_V1 = re.compile(r"(?<![\w+#])(" + "|".join(CODE_TERMS) + r")(?![\w+#])", re.I)
TERM_RE_V2 = re.compile(r"(?<![\w+#])(" + "|".join(CODE_TERMS + CODE_TERMS_V2_ADD) + r")(?![\w+#])",
                        re.I)
TERM_RE = re.compile(r"(?<![\w+#])(" + "|".join(CODE_TERMS + CODE_TERMS_V2_ADD + CODE_TERMS_V3_ADD)
                     + r")(?![\w+#])", re.I)
LINE_RE = re.compile(
    r"^\s*(def |class |import |from \S+ import |#include|public |private |static |function |"
    r"const |let |var |SELECT |INSERT |CREATE TABLE|for\s*\(|while\s*\(|if\s*\(|return\b)",
    re.M)
END_RE = re.compile(r"[;{}]\s*$", re.M)


def code_reasons(prompt, cluster, term_re=None):
    term_re = term_re or TERM_RE
    why = []
    if "```" in prompt:
        why.append("fence")
    m = term_re.search(prompt)
    if m:
        why.append("term:" + m.group(1).lower())
    m = term_re.search(cluster)
    if m:
        why.append("cluster_term:" + m.group(1).lower())
    if LINE_RE.search(prompt):
        why.append("code_line_start")
    if END_RE.search(prompt):
        why.append("line_ends_in_;{}")
    if "=>" in prompt or "::" in prompt:
        why.append("operator")
    return why


def build_arenahard(lcb):
    out = os.path.join(D, "m-arenahard")
    rows = []
    for p in sorted(glob.glob(os.path.join(out, "raw", "en_test_rows_*.json"))):
        with open(p) as f:
            rows += [r["row"] for r in json.load(f)["rows"]]
    assert len(rows) == 500 and len({r["question_id"] for r in rows}) == 500
    text = {r["question_id"]: r["prompt"] for r in rows}
    code = {r["question_id"]: code_reasons(r["prompt"], r["cluster"]) for r in rows}
    code_v1 = {r["question_id"]: code_reasons(r["prompt"], r["cluster"], TERM_RE_V1) for r in rows}
    code_v2 = {r["question_id"]: code_reasons(r["prompt"], r["cluster"], TERM_RE_V2) for r in rows}
    dup = dedupe([(r["question_id"], r["prompt"]) for r in rows], lcb)
    dropped = {x[0] for x in dup["exact"] + dup["normalised"]}
    empty = {q for q, t in text.items() if not t.strip()}
    pool = sorted(q for q in text if not code[q] and q not in dropped and q not in empty)
    sample = random.Random(SEED).sample(pool, 50)
    main, end = cross_rows("m-arenahard", sample, text)
    write_jsonl(os.path.join(out, "prompts.jsonl"), main)
    write_jsonl(os.path.join(out, "prompts_instr_end.jsonl"), end)
    write_lines(os.path.join(out, "ids.txt"), [r["id"] for r in main])
    write_json(os.path.join(out, "build_meta.json"), {
        "seed": SEED, "n_rows": len(rows), "n_code": sum(bool(v) for v in code.values()),
        "n_code_rule_v1": sum(bool(v) for v in code_v1.values()),
        "pool_rule_v1": sum(1 for q in text if not code_v1[q] and q not in dropped | empty),
        "n_code_rule_v2": sum(bool(v) for v in code_v2.values()),
        "pool_rule_v2": sum(1 for q in text if not code_v2[q] and q not in dropped | empty),
        "code_reason_counts": collections.Counter(w.split(":")[0] for v in code.values() for w in v),
        "dedupe": {k: len(v) for k, v in dup.items()}, "dedupe_detail": dup,
        "n_dup_dropped": len(dropped), "n_dup_dropped_and_noncode": len(dropped - {q for q in code if code[q]}),
        "n_empty": len(empty), "pool_noncode_nodup": len(pool), "sample_base_ids": sample,
        "code_flags": code})
    return len(main)


# ---- XL-AlpacaEval (added 2026-11-22 after the user cleared its licence; no code filter)

def build_xl(lcb):
    out = os.path.join(D, "xl-alpacaeval")
    with open(os.path.join(out, "raw", "english.json")) as f:
        rows = json.load(f)
    assert len({r["id"] for r in rows}) == len(rows) and all(r["id"].isdigit() for r in rows)
    text = {r["id"]: r["instruction"] for r in rows}
    sub = {r["id"]: r["dataset"] for r in rows}
    dup = dedupe([(r["id"], r["instruction"]) for r in rows], lcb)
    dropped = {x[0] for x in dup["exact"] + dup["normalised"]}
    empty = {i for i, t in text.items() if not t.strip()}
    pool = sorted((i for i in text if i not in dropped and i not in empty), key=int)
    sample = random.Random(SEED).sample(pool, 70)
    main, end = cross_rows("xl-alpacaeval", sample, text)
    for r in main + end:
        r["alpacaeval_subsource"] = sub[r["base_id"]]
    write_jsonl(os.path.join(out, "prompts.jsonl"), main)
    write_jsonl(os.path.join(out, "prompts_instr_end.jsonl"), end)
    write_lines(os.path.join(out, "ids.txt"), [r["id"] for r in main])
    by_sub = {k: {"n": n} for k, n in sorted(collections.Counter(sub.values()).items())}
    for kind, items in dup.items():
        for k in by_sub:
            by_sub[k][kind] = sum(1 for x in items if sub[x[0]] == k)
    write_json(os.path.join(out, "build_meta.json"), {
        "seed": SEED, "n_rows": len(rows), "dedupe": {k: len(v) for k, v in dup.items()},
        "dedupe_by_subsource": by_sub, "dedupe_detail": dup, "n_dup_dropped": len(dropped),
        "n_empty": len(empty), "pool": len(pool), "sample_base_ids": sample,
        "sample_by_subsource": dict(collections.Counter(sub[i] for i in sample))})
    return len(main)


# ---- Global-MMLU

def gm_en_rows():
    rows = []
    for p in sorted(glob.glob(os.path.join(D, "global-mmlu", "raw", "en", "test_rows_*.json"))):
        with open(p) as f:
            rows += [(r["row_idx"], r["row"]) for r in json.load(f)["rows"]]
    rows.sort(key=lambda x: x[0])
    assert [i for i, _ in rows] == list(range(14042)), "en test rows incomplete"
    return rows


def gm_select():
    rows = gm_en_rows()
    assert len({r["sample_id"] for _, r in rows}) == len(rows)
    by_cat = collections.defaultdict(list)
    for i, r in rows:
        by_cat[r["subject_category"]].append((r["sample_id"], i))
    total = len(rows)
    quota = {c: 100 * len(v) / total for c, v in by_cat.items()}
    alloc = {c: int(q) for c, q in quota.items()}
    rest = 100 - sum(alloc.values())  # largest remainder, ties by category name
    for c in sorted(quota, key=lambda c: (-(quota[c] - alloc[c]), c))[:rest]:
        alloc[c] += 1
    rng = random.Random(SEED)
    picked = []
    for c in sorted(by_cat):
        picked += rng.sample(sorted(by_cat[c]), alloc[c])
    picked.sort(key=lambda x: x[1])
    write_json(os.path.join(D, "global-mmlu", "select.json"), {
        "seed": SEED, "n_en_test": total, "category_counts": {c: len(v) for c, v in by_cat.items()},
        "alloc": alloc, "picked": [{"sample_id": s, "row_idx": i} for s, i in picked]})


LETTER_TEXT = ("{q}\nA. {a}\nB. {b}\nC. {c}\nD. {d}\nPlease respond with the correct letter "
               "(A, B, C or D) without any additional comments, only the correct letter:")


def build_gmmlu():
    out = os.path.join(D, "global-mmlu")
    with open(os.path.join(out, "select.json")) as f:
        sel = json.load(f)
    en = dict(gm_en_rows())
    rows, checks = [], {"sample_id_mismatch": [], "answer_differs_from_en": []}
    for lang in LANGS14:
        got = {}
        for p in sorted(glob.glob(os.path.join(out, "raw", lang, "test_rows_*.json"))):
            with open(p) as f:
                got.update({r["row_idx"]: r["row"] for r in json.load(f)["rows"]})
        for it in sel["picked"]:
            r = got[it["row_idx"]]
            if r["sample_id"] != it["sample_id"]:
                checks["sample_id_mismatch"].append([lang, it["row_idx"], r["sample_id"]])
                continue
            if r["answer"] != en[it["row_idx"]]["answer"]:
                checks["answer_differs_from_en"].append([lang, it["sample_id"]])
            subj = r["subject"]
            rows.append({
                "id": f"monolingual/global-mmlu/{lang}/{r['sample_id']}", "task": "monolingual",
                "source": "global-mmlu", "language": lang, "sample_id": r["sample_id"],
                "subject": subj, "group": r["subject_category"],
                "cultural_sensitivity_label": r["cultural_sensitivity_label"],
                "description": "The following are multiple choice questions (with answers) "
                               f"about {subj.replace('_', ' ')}.\n\n",
                "prompt": LETTER_TEXT.format(q=r["question"].strip(), a=r["option_a"],
                                             b=r["option_b"], c=r["option_c"], d=r["option_d"]),
                "target": r["answer"], "answer": "ABCD".index(r["answer"])})
    assert not checks["sample_id_mismatch"], checks["sample_id_mismatch"][:5]
    write_jsonl(os.path.join(out, "items.jsonl"), rows)
    write_lines(os.path.join(out, "ids.txt"), [r["id"] for r in rows])
    write_json(os.path.join(out, "build_meta.json"), {
        "seed": SEED, "n_items": len(rows), "per_lang": dict(collections.Counter(r["language"] for r in rows)),
        "per_group": dict(collections.Counter(r["group"] for r in rows if r["language"] == "ar")),
        "cs_ca": dict(collections.Counter(r["cultural_sensitivity_label"] for r in rows if r["language"] == "ar")),
        **checks})
    return len(rows)


# ---- MGSM (instruction text and answer prefixes copied from simple-evals mgsm_eval.py)

MGSM_LANGS = ["en", "de", "es", "fr", "ja", "ru", "zh"]
MGSM_INSTR = {
    "en": 'Solve this math problem. Give the reasoning steps before giving the final answer on the last line by itself in the format of "Answer:". Do not add anything other than the integer answer after "Answer:".\n\n{input}',
    "de": 'Löse dieses Mathematikproblem. Gib die Schritte zur Begründung an, bevor du die endgültige Antwort in der letzten Zeile alleine im Format "Antwort:" gibst. Füge nichts anderes als die ganzzahlige Antwort nach "Antwort:" hinzu.\n\n{input}',
    "es": 'Resuelve este problema matemático. Proporciona los pasos de razonamiento antes de dar la respuesta final en la última línea por sí misma en el formato de "Respuesta:". No añadas nada más que la respuesta entera después de "Respuesta:".\n\n{input}',
    "fr": 'Résolvez ce problème de mathématiques. Donnez les étapes de raisonnement avant de fournir la réponse finale sur la dernière ligne elle-même dans le format de "Réponse:". N\'ajoutez rien d\'autre que la réponse entière après "Réponse:".\n\n{input}',
    "ja": 'の数学の問題を解いてください。最終的な答えを出す前に、解答の推論過程を記述してください。そして最後の行には "答え:" の形式で答えを記述し、その後には整数の答え以外何も追加しないでください。\n\n{input}',
    "ru": 'Решите эту математическую задачу. Объясните шаги рассуждения перед тем, как дать окончательный ответ в последней строке сам по себе в формате "Ответ:". Не добавляйте ничего, кроме целочисленного ответа после "Ответ:".\n\n{input}',
    "zh": '解决这个数学问题。在最后一行给出答案前，请提供推理步骤。最后一行应该以 "答案: " 的形式独立给出答案。在 "答案：" 后不要添加除整数答案之外的任何内容。\n\n{input}',
}
MGSM_PREFIX = {"en": "Answer", "de": "Antwort", "es": "Respuesta", "fr": "Réponse",
               "ja": "答え", "ru": "Ответ", "zh": "答案"}


def check_template_copy():
    """our copied strings must appear verbatim in the saved simple-evals file."""
    with open(os.path.join(D, "mgsm", "ref", "simple_evals_mgsm_eval.py.txt")) as f:
        src = f.read()
    bad = [l for l in MGSM_LANGS if f'"""{MGSM_INSTR[l]}"""' not in src
           or f'"{l}": "{MGSM_PREFIX[l]}"' not in src]
    assert not bad, bad


def git_blob_sha1(path):
    with open(path, "rb") as f:
        b = f.read()
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def build_mgsm():
    out = os.path.join(D, "mgsm")
    check_template_copy()
    data = {}
    for lang in MGSM_LANGS:
        with open(os.path.join(out, "raw", f"mgsm_{lang}.tsv"), encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f if l.strip()]
        data[lang] = [tuple(l.split("\t")) for l in lines]
        assert len(data[lang]) == 250 and all(len(x) == 2 for x in data[lang]), lang
    targets_differ = [i for i in range(250) if len({data[l][i][1] for l in MGSM_LANGS}) > 1]
    idx = sorted(random.Random(SEED).sample(range(250), 50))
    rows = []
    for lang in MGSM_LANGS:
        for i in idx:
            q, t = data[lang][i]
            rows.append({"id": f"monolingual/mgsm/{lang}/{i}", "task": "monolingual",
                         "source": "mgsm", "language": lang, "item": i,
                         "prompt": MGSM_INSTR[lang].format(input=q), "target": t,
                         "answer_prefix": MGSM_PREFIX[lang]})
    write_jsonl(os.path.join(out, "prompts.jsonl"), rows)
    write_lines(os.path.join(out, "ids.txt"), [r["id"] for r in rows])
    write_json(os.path.join(out, "build_meta.json"), {
        "seed": SEED, "items": idx, "n_rows": len(rows), "targets_differ_across_langs": targets_differ,
        "git_blob_sha1": {l: git_blob_sha1(os.path.join(out, "raw", f"mgsm_{l}.tsv")) for l in MGSM_LANGS}})
    return len(rows)


# ---- IFEval

def build_ifeval():
    out = os.path.join(D, "ifeval")
    with open(os.path.join(out, "raw", "ifeval_input_data.jsonl")) as f:
        src = [json.loads(l) for l in f if l.strip()]
    assert len(src) == 541 and len({r["key"] for r in src}) == 541
    rows = []
    for r in src:
        kept = [i for i in r["instruction_id_list"] if not i.startswith("length_constraints:")]
        rows.append({"id": f"monolingual/ifeval/en/{r['key']}", "task": "monolingual",
                     "source": "ifeval", "language": "en", "key": r["key"], "prompt": r["prompt"],
                     "instruction_id_list": r["instruction_id_list"], "kwargs": r["kwargs"],
                     "scored_instruction_ids": kept})
    write_jsonl(os.path.join(out, "prompts.jsonl"), rows)
    write_lines(os.path.join(out, "ids.txt"), [r["id"] for r in rows])
    n_all = sum(len(r["instruction_id_list"]) for r in rows)
    n_kept = sum(len(r["scored_instruction_ids"]) for r in rows)
    write_json(os.path.join(out, "build_meta.json"), {
        "n_prompts": len(rows), "n_instructions": n_all, "n_instructions_scored": n_kept,
        "n_prompts_with_length_constraint": sum(n != k for n, k in
                                                ((len(r["instruction_id_list"]), len(r["scored_instruction_ids"])) for r in rows)),
        "n_prompts_scored": sum(bool(r["scored_instruction_ids"]) for r in rows)})
    return len(rows)


# ---- LCB stress subsets (ids only; prompts come from the LCB loader as before)

def build_lcb_stress():
    out = os.path.join(D, "lcb-stress")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(ROOT, "splits", "test.txt")) as f:
        test = [l.strip() for l in f if l.strip()]
    cx = [p for p in test if p.split("/")[1] == "complex_prompts"]
    with open(os.path.join(ROOT, "splits", "split_meta.json")) as f:
        meta = json.load(f)
    groups = [g for g in meta["groups"]["complex_prompts"]
              if meta["group_side"][f"complex_prompts/{g[0]}"] == "test"]
    rng = random.Random(SEED)
    sub = []
    for g in groups:
        for lang in LANGS14:
            r = rng.choice(sorted(g))
            sub.append(f"crosslingual/complex_prompts/{lang}/{r}")
    assert set(sub) <= set(cx)
    order = {p: i for i, p in enumerate(test)}
    sub.sort(key=order.get)
    write_lines(os.path.join(out, "greedy_test_complex_ids.txt"), cx)
    write_lines(os.path.join(out, "long400_ids.txt"), sub)
    write_json(os.path.join(out, "build_meta.json"), {
        "seed": SEED, "n_test_complex": len(cx), "n_groups": len(groups), "n_long400": len(sub)})
    return len(cx), len(sub)


def main():
    cmd = sys.argv[1]
    if cmd == "gmmlu-select":
        gm_select()
        return
    lcb = lcb_english()
    res = {"lcb_english_rows_compared": lcb[2]}
    res["m-arenahard"] = build_arenahard(lcb)
    if os.path.exists(os.path.join(D, "xl-alpacaeval", "raw", "english.json")):
        res["xl-alpacaeval"] = build_xl(lcb)
    if os.path.exists(os.path.join(D, "global-mmlu", "raw", "zh")):
        res["global-mmlu"] = build_gmmlu()
    res["mgsm"] = build_mgsm()
    res["ifeval"] = build_ifeval()
    res["lcb-stress"] = build_lcb_stress()
    print(json.dumps(res))


if __name__ == "__main__":
    main()
