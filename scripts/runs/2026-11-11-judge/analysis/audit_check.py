# audit: paths touched, banned tools, labels = literal per-item lines in tool inputs
import json, re, sys, collections
C = json.load(open(sys.argv[1]))
T = sys.argv[2]  # transcript
print("tool names:", collections.Counter(c["name"] for c in C))
blob = json.dumps([c["input"] for c in C], ensure_ascii=False).lower()
for w in ["fasttext", "langdetect", "langid", "lingua", "cld", "polyglot", "webfetch", "websearch",
          "curl", "wget", "http://", "https://", "key.jsonl", "key/", "labels/baseline", "labels/c02",
          "recover", "instr_end", "mono_en", "check.json", "logs/", "scripts/", "gate", "stats"]:
    print(f"  {w!r}: {blob.count(w)}")
paths = sorted(set(re.findall(r"/(?:users|private)/[^\s'\"\;|&<>)]+", blob)))
print("paths in tool inputs:"); [print("  ", p) for p in paths]
# rebuild labels from the literal lines typed in tool inputs
lab = re.compile(r"([0-9a-f]{8})\|(full_lang|mixed|wrong|empty_or_garbage)\|([^|\n]*)\|(high|low)\|([^\n']*)")
typed = []
for c in C:
    cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
    for l in cmd.split("\n"):
        m = lab.search(l.strip())
        if m and "32fa91f1_dummy" not in l: typed.append(m.groups())
L = [json.loads(l) for l in open("labels/labels.jsonl")]
rebuilt = [{"item_id": a, "label": b, "other_langs": [x.strip() for x in c.split(",") if x.strip()],
            "confidence": d, "note": e.strip()} for a, b, c, d, e in typed]
print("typed label lines:", len(typed), "file lines:", len(L), "identical:", rebuilt == L)
# tool results: does 41a819a7 appear in a shown-items result before its label call
res = {}
for line in open(T):
    r = json.loads(line); c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                res[b["tool_use_id"]] = json.dumps(b.get("content"), ensure_ascii=False)
for i, c in enumerate(C):
    if "41a819a7" in res.get(c["id"], ""): print("41a819a7 shown in result of call", i)
# was every answer shown to the judge in full (bash results, plus the Read of its persisted output)
items = [json.loads(l) for l in open("packet/items.jsonl")]
norm = lambda s: "\n".join(l.rstrip() for l in s.strip().split("\n"))
def txt(b):
    s = b["content"]
    return s if isinstance(s, str) else "".join(x.get("text", "") for x in s if isinstance(x, dict))
resb = {}
for line in open(T):
    r = json.loads(line); c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result": resb[b["tool_use_id"]] = b
shown = set()
for c in C:
    if c["id"] not in resb: continue
    t = txt(resb[c["id"]])
    if c["name"] == "Read":
        t = "\n".join(re.sub(r"^\s*\d+\t", "", l) for l in t.split("\n"))
    t = norm(t)
    shown |= {d["item_id"] for d in items if f"{d['item_id']} |" in t and norm(d["answer"]) in t}
print("items whose full answer was shown to the judge:", len(shown), "of", len(items))
