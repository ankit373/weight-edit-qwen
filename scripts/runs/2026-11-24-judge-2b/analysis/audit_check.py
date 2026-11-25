# audit: paths touched, banned tools, labels = literal per-item lines in tool inputs
import json, re, sys, collections
C = json.load(open(sys.argv[1]))
T = sys.argv[2]  # transcript
print("tool names:", collections.Counter(c["name"] for c in C))
blob = json.dumps([c["input"] for c in C], ensure_ascii=False).lower()
for w in ["fasttext", "langdetect", "langid", "lingua", "cld", "polyglot", "webfetch", "websearch",
          "curl", "wget", "http://", "https://", "key.jsonl", "key/", "labels/baseline", "labels/c06",
          "labels/", "recover", "instr_end", "mono_en", "check.json", "logs/", "scripts/", "gate", "stats",
          " ls", "find ", "grep", "glob", "pip ", "install"]:
    print(f"  {w!r}: {blob.count(w)}")
paths = sorted(set(re.findall(r"/(?:users|private)/[^\s'\"\;|&<>)]+", blob)))
print("paths in tool inputs:"); [print("  ", p) for p in paths]
# rebuild labels from the literal json lines typed in add.py heredocs, in call order
typed, label_call = [], {}
for i, c in enumerate(C):
    cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
    m = re.search(r"python3 -I \S+/add\.py <<'EOF'\n(.*?)\nEOF", cmd, re.S)
    if not m:
        continue
    body = m.group(1)
    n = 0
    for l in body.split("\n"):
        if l.strip():
            typed.append(json.loads(l)); label_call[typed[-1]["item_id"]] = i; n += 1
    print(f"  call {i}: {n} typed label lines")
# the one in-place edit (call that rewrites labels.jsonl): apply its literal values
for i, c in enumerate(C):
    cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
    if "open(p,'w')" in cmd and "labels.jsonl" in cmd:
        iid = re.search(r"r\['item_id'\]=='([0-9a-f]{8})'", cmd).group(1)
        conf = re.search(r"r\['confidence'\]='(\w+)'", cmd).group(1)
        note = re.search(r'r\[\'notes\'\]="([^"]*)"', cmd).group(1)
        print(f"  call {i}: in-place edit of {iid}: confidence -> {conf}, notes rewritten; label not touched:",
              "'label'" not in cmd)
        for r in typed:
            if r["item_id"] == iid:
                print("    before:", r["label"], r["confidence"]); r["confidence"] = conf; r["notes"] = note
L = [json.loads(l) for l in open("judge/labels.jsonl")]
print("typed label lines:", len(typed), "file lines:", len(L), "identical:", typed == L)
# helper scripts written by heredoc vs what is left in the scratchpad
for i, c in enumerate(C):
    cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
    for m in re.finditer(r"cat > (\S+) <<'EOF'\n(.*?)\nEOF", cmd, re.S):
        try:
            same = open(m.group(1)).read() == m.group(2) + "\n"
        except OSError:
            same = "file gone"
        print(f"  call {i}: wrote {m.group(1).rsplit('/', 1)[1]}, scratch file equal now: {same}")
# was every prompt and answer shown to the judge in full, before the call that typed its label
items = [json.loads(l) for l in open("packet/items.jsonl")]
def txt(b):
    s = b["content"]
    return s if isinstance(s, str) else "".join(x.get("text", "") for x in s if isinstance(x, dict))
resb = {}
for line in open(T):
    r = json.loads(line); c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result": resb[b["tool_use_id"]] = b
print("results with overflow marker (persisted / too large):",
      sum(("persisted" in txt(b).lower() or "too large" in txt(b).lower()) for b in resb.values()))
first_shown, prompt_seen, answer_seen, end_trimmed = {}, set(), set(), set()
for i, c in enumerate(C):
    if c["id"] not in resb: continue
    t = txt(resb[c["id"]])
    for n, d in enumerate(items):
        head = f"=== #{n} {d['item_id']} [{d['target_language']}]\n"
        if head not in t: continue
        if head + "PROMPT: " + d["prompt"] + "\nANSWER: " in t: prompt_seen.add(d["item_id"])
        block = head + "PROMPT: " + d["prompt"] + "\nANSWER: " + d["answer"] + "\n"
        # the harness trims trailing whitespace of a tool result, so the last item of a call
        # is matched with its trailing whitespace removed
        at_end = t.rstrip().endswith(block.rstrip())
        if block in t or at_end:
            answer_seen.add(d["item_id"]); first_shown.setdefault(d["item_id"], i)
            if at_end and block not in t: end_trimmed.add(d["item_id"])
long = [d for d in items if len(d["prompt"]) > 120]
print("items whose full prompt was shown:", len(prompt_seen), "of", len(items),
      f"(prompts over 120 chars: {len(long)}, of them shown in full: {sum(d['item_id'] in prompt_seen for d in long)})")
print("items whose full answer was shown:", len(answer_seen), "of", len(items),
      f"(last item of a call, trailing whitespace trimmed by the harness: {len(end_trimmed)})")
print("items with full prompt+answer block shown:", len(first_shown))
before = [i for i in label_call if i in first_shown and first_shown[i] < label_call[i]]
print("items shown in an earlier call than the call that typed their label:", len(before), "of", len(label_call))
print("longest prompt shown in full:", max(len(d["prompt"]) for d in items if d["item_id"] in prompt_seen))
# duplicates: same answer text -> same label
g = collections.defaultdict(list)
for d in items: g[d["answer"]].append(d["item_id"])
lab = {r["item_id"]: r for r in L}
grp = [v for v in g.values() if len(v) > 1]
print("same-answer groups:", len(grp), "same label:", sum(len({lab[x]["label"] for x in v}) == 1 for v in grp))
print("non-full_lang labels with a note:", sum(bool(r["notes"].strip()) for r in L if r["label"] != "full_lang"),
      "of", sum(r["label"] != "full_lang" for r in L), "; distinct notes:", len({r["notes"] for r in L if r["label"] != "full_lang"}))
print("label calls span:", C[min(label_call.values())]["ts"], "to", C[max(label_call.values())]["ts"])
