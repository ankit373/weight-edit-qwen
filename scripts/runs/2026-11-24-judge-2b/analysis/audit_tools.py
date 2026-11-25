# list judge tool_use calls (name + input) from its jsonl transcript; nothing else is printed
import json, sys
calls = []
for line in open(sys.argv[1]):
    try: r = json.loads(line)
    except Exception: continue
    msg = r.get("message") or {}
    c = msg.get("content")
    if not isinstance(c, list): continue
    for b in c:
        if isinstance(b, dict) and b.get("type") == "tool_use":
            calls.append({"ts": r.get("timestamp"), "id": b.get("id"), "name": b.get("name"), "input": b.get("input")})
json.dump(calls, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(len(calls), "tool_use calls")
for i, c in enumerate(calls):
    inp = c["input"]; s = json.dumps(inp, ensure_ascii=False)
    print(i, c["ts"], c["name"], len(s), s[:300].replace("\n", "\\n"))
