"""build the mmlu-redux item file from the downloaded json rows and lm-eval task yamls (cpu).

usage: prepare_items.py <redux2 dir> <redux2-ok dir> <lmeval tasks dir> <out items.jsonl> <out check.json>
prompt = lm-eval mmlu-redux generative _default_template_yaml:8 (doc_to_text), description and
group tag from each mmlu_<subject>.yaml. subset = error_type "ok" (lm-eval README version 4).
"""
import json
import os
import sys
from collections import Counter

import yaml

REDUX, OK, TASKS, OUT, CHECK = sys.argv[1:6]
LETTERS = "ABCD"


def load_rows(d, subject):
    with open(os.path.join(d, "rows", f"{subject}.json")) as f:
        page = json.load(f)
    rows = page["rows"]
    assert page["num_rows_total"] == len(rows), (d, subject)
    assert not page.get("partial"), (d, subject)
    assert all(not r["truncated_cells"] for r in rows), (d, subject)
    assert [r["row_idx"] for r in rows] == list(range(len(rows))), (d, subject)
    return [r["row"] for r in rows]


def doc_to_text(q, c):
    # _default_template_yaml:8, jinja rendered by hand
    return (f"{q.strip()}\nA. {c[0]}\nB. {c[1]}\nC. {c[2]}\nD. {c[3]}\n"
            "Please respond with the correct letter (A, B, C or D) without any additional "
            "comments, only the correct letter:")


def main():
    with open(os.path.join(REDUX, "splits.json")) as f:
        subjects = sorted(s["config"] for s in json.load(f)["splits"])
    items, error_types, ok_keys = [], Counter(), Counter()
    for subj in subjects:
        with open(os.path.join(TASKS, f"mmlu_{subj}.yaml")) as f:
            cfg = yaml.safe_load(f)
        assert cfg["dataset_name"] == subj and cfg["include"] == "_default_template_yaml"
        group = cfg["tag"].removeprefix("mmlu_redux_").removesuffix("_generative")
        for i, r in enumerate(load_rows(REDUX, subj)):
            error_types[r["error_type"]] += 1
            assert len(r["choices"]) == 4 and r["answer"] in (0, 1, 2, 3), (subj, i)
            if r["error_type"] != "ok":
                continue
            ok_keys[(subj, r["question"], tuple(r["choices"]), r["answer"])] += 1
            items.append({"id": f"{subj}/{i}", "subject": subj, "group": group,
                          "description": cfg["description"],
                          "prompt": doc_to_text(r["question"], r["choices"]),
                          "target": LETTERS[r["answer"]], "answer": r["answer"]})
    ref = Counter()
    for subj in subjects:
        for r in load_rows(OK, subj):
            ref[(subj, r["question"], tuple(r["choices"]), r["answer"])] += 1
    with open(OUT, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    check = {"subjects": len(subjects), "rows_total": sum(error_types.values()),
             "error_types": dict(error_types), "ok_items": len(items),
             "groups": dict(Counter(it["group"] for it in items)),
             "targets": dict(Counter(it["target"] for it in items)),
             "lmeval_ok_copy_items": sum(ref.values()),
             "same_as_lmeval_ok_copy": ok_keys == ref,
             "only_in_ours": sum((ok_keys - ref).values()),
             "only_in_lmeval_copy": sum((ref - ok_keys).values())}
    with open(CHECK, "w") as f:
        json.dump(check, f, indent=1)
    print(json.dumps(check))


if __name__ == "__main__":
    main()
