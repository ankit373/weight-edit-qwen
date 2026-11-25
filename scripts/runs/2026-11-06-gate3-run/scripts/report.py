"""tables per method against the baseline, from score.py json + wrong_lang.py json.

usage: report.py <out.md> <title> <label>=<score_prefix> [<label>=<score_prefix> ...]
the first label is the reference (baseline); every prefix must be scored on the same ids.
full-failure rate = responses where every checked line is wrong / scored responses (wrong_lang.py "full").
"""
import json
import sys

LANGS = ["ar", "de", "es", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "tr", "vi", "zh"]
SETS = [("complex_prompts", "complex"), ("okapi", "okapi"), ("sharegpt", "sharegpt"), ("all", "all")]


def load(prefix):
    table = json.load(open(prefix + ".json"))
    cells = {(t["source"], t["language"]): t for t in table if t.get("task") == "crosslingual"}
    wl = json.load(open(prefix + "_wrong_lang.json"))
    full = {}
    for f in wl["failing_responses"]:
        if not f["id"].startswith("crosslingual/"):
            continue
        _, src, lang, _ = f["id"].split("/")
        if f["full_response_wrong"]:
            for key in ((src, lang), (src, "all"), ("all", lang), ("all", "all")):
                full[key] = full.get(key, 0) + 1
    return cells, full


def fmt(v, scale=100):
    return "" if v is None else f"{v * scale:.1f}"


def row(cells, full, key):
    c = cells.get(key)
    if c is None:
        return None
    ff = 100 * full.get(key, 0) / c["n_scored"] if c.get("n_scored") else None
    return {"n": c["n"], "scored": c.get("n_scored"), "lpr": c["lpr"], "wpr": c.get("wpr"),
            "lcpr": c.get("lcpr"), "full": ff}


def main():
    out, title = sys.argv[1], sys.argv[2]
    runs = [a.split("=", 1) for a in sys.argv[3:]]
    data = {lab: load(p) for lab, p in runs}
    ref = runs[0][0]
    lines = [f"## {title}", "",
             "LPR, WPR, LCPR in % (gate 1 score.py; dataset/all rows = mean over language cells, LCB style). "
             "full = % of scored responses fully in a wrong language. d = minus reference "
             f"({ref}). WPR/LCPR exist only for ar hi ja ko ru zh.", ""]
    for src, name in SETS:
        lines += [f"### {name}", "",
                  "| method | n | scored | LPR | d LPR | WPR | LCPR | full % | d full |",
                  "|---|---|---|---|---|---|---|---|---|"]
        base = row(*data[ref], (src, "all"))
        for lab, _ in runs:
            r = row(*data[lab], (src, "all"))
            if r is None:
                continue
            dl = "" if lab == ref else f"{100 * (r['lpr'] - base['lpr']):+.1f}"
            df = "" if lab == ref else f"{r['full'] - base['full']:+.1f}"
            lines.append(f"| {lab} | {r['n']} | {r['scored']} | {fmt(r['lpr'])} | {dl} | {fmt(r['wpr'])} | "
                         f"{fmt(r['lcpr'])} | {r['full']:.1f} | {df} |")
        lines.append("")
    for src, name in SETS:
        lines += [f"### by language, {name}: LPR (full %)", "",
                  "| method | " + " | ".join(LANGS) + " |", "|---|" + "---|" * len(LANGS)]
        for lab, _ in runs:
            vals = []
            for lang in LANGS:
                r = row(*data[lab], (src, lang))
                vals.append("" if r is None or r["full"] is None else f"{100 * r['lpr']:.1f} ({r['full']:.1f})")
            lines.append(f"| {lab} | " + " | ".join(vals) + " |")
        lines.append("")
        lines += [f"### by language, {name}: WPR / LCPR (non-latin)", "",
                  "| method | " + " | ".join(l for l in LANGS if l in "ar hi ja ko ru zh".split()) + " |",
                  "|---|" + "---|" * 6]
        for lab, _ in runs:
            vals = []
            for lang in "ar hi ja ko ru zh".split():
                r = row(*data[lab], (src, lang))
                vals.append("" if r is None or r["wpr"] is None else f"{fmt(r['wpr'])} / {fmt(r['lcpr'])}")
            lines.append(f"| {lab} | " + " | ".join(vals) + " |")
        lines.append("")
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
