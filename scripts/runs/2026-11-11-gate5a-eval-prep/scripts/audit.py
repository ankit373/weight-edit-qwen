"""banned-read audit of a blind editor transcript (claude code subagent jsonl). stdlib only.

usage: audit.py <transcript.jsonl> <workspace_dir> <findings.json>

method (as runs/2026-11-10-gate4-audit): parse only tool_use entries of assistant messages, one per
tool_use id (the jsonl repeats some). every string in each tool input is scanned for path tokens;
relative tokens resolve against the entry's cwd, or the folder of a `cd` earlier in the same command.
bans (PROTOCOL.md "parallel runs" + "decisions after gate 4", gate 4 RULES.md):
  runs/ (all of it, so runs/*gate3*, *gate2b*, *mit-*, *gate4*, *stats*, *gate5* too), external/, splits/,
  PROTOCOL.md, ~/.claude/, gate4-workspace/ and every gate5-workspace-* other than the editor's own,
  secret dirs (~/.ssh ~/.aws ~/.config ~/.gnupg ~/.netrc). web: WebSearch, WebFetch, any mcp__ tool,
  any http(s) url.
allowed outside the workspace: the sandbox wrapper and the gen / score interpreters in ../envs/.
everything else outside the workspace is listed for review (not counted as a ban).
path hits inside text (SendMessage, SubagentHandback, Write/Edit of .md .txt .tsv .json .jsonl files)
are listed apart as mentions: text that names a path is not a read.
"""
import collections
import json
import os
import re
import sys

MSG_TOOLS = {"SendMessage", "SubagentHandback"}
WEB_TOOLS = {"WebSearch", "WebFetch"}
SYSTEM = ("/usr/", "/bin/", "/sbin/", "/dev/", "/etc/", "/tmp/", "/private/tmp/", "/private/var/",
          "/var/", "/opt/homebrew/", "/System/", "/Library/")
PATH_RE = re.compile(r"(?:~|\.\.?|/)?[A-Za-z0-9_.@+*?\[\]{}~-]*(?:/[A-Za-z0-9_.@+*?\[\]{}~-]*)+")
URL_RE = re.compile(r"https?://\S+")
CD_RE = re.compile(r"(?:^|[;&|({\s])cd\s+(['\"]?)([^\s;&|'\")]+)\1")
BARE = {"PROTOCOL.md"}
NOTE_EXT = (".md", ".txt", ".tsv", ".json", ".jsonl")


def tool_uses(path):
    seen = {}
    for line in open(path):
        d = json.loads(line)
        if d.get("type") != "assistant":
            continue
        for b in (d.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b["id"] not in seen:
                seen[b["id"]] = {"id": b["id"], "name": b["name"], "input": b.get("input") or {},
                                 "ts": d.get("timestamp"), "cwd": d.get("cwd")}
    return sorted(seen.values(), key=lambda u: u["ts"] or "")


def strings(x, key=""):
    if isinstance(x, str):
        yield key, x
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from strings(v, f"{key}.{k}" if key else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from strings(v, f"{key}[{i}]")


def tokens(text, cwd, shell):
    """(token, resolved abs path) for every path-like token, cwd updated by `cd` in the text."""
    cds = [(m.start(), m.group(2)) for m in CD_RE.finditer(text)]
    for m in PATH_RE.finditer(text):
        tok = m.group(0)
        if "/" not in tok and tok not in BARE:
            continue
        if URL_RE.match(text, max(0, m.start() - 8)) or text[max(0, m.start() - 3):m.start()] == "://":
            continue
        base = cwd
        for pos, d in cds:
            if pos < m.start() and d != tok:
                base = os.path.normpath(os.path.join(base, os.path.expanduser(d)))
        p = os.path.expanduser(tok)
        if not p.strip("/"):
            continue  # "/" or "//": division, sed, not a path
        if p.startswith("/") and not os.path.isdir("/" + p.strip("/").split("/")[0]):
            continue  # "/all", "/g": substrings in code; real absolute paths start at an existing top dir
        yield tok, os.path.normpath(p if p.startswith("/") else os.path.join(base, p))
    for tok in re.findall(r"(?<![\w/.])PROTOCOL\.md", text):
        yield tok, os.path.normpath(os.path.join(cwd, tok))
    if shell:  # bare ".." as a shell word (ls .., cat ..), not "..", in code or "..." in prose
        for m in re.finditer(r"(?:^|(?<=\s))\.\.(?=\s|$|[;|&)])", text):
            yield "..", os.path.normpath(os.path.join(cwd, ".."))


def classify(p, ws, root, home):
    """-> (kind, label). kind: inside, allowed, banned, review, system."""
    def under(d):
        return p == d or p.startswith(d.rstrip("/") + "/")
    if under(ws):
        return "inside", ""
    if under(os.path.join(root, "runs")):
        parts = os.path.relpath(p, root).split("/")
        seg = parts[1] if len(parts) > 1 else ""
        tags = [t for t in ("gate2b", "gate3", "gate4", "gate5", "stats", "mit-", "prior-work") if t in seg]
        return "banned", "runs/" + (f" ({','.join(tags)})" if tags else "")
    for d, label in (("external", "external/"), ("splits", "splits/")):
        if under(os.path.join(root, d)):
            return "banned", label
    if p == os.path.join(root, "PROTOCOL.md"):
        return "banned", "PROTOCOL.md"
    if under(os.path.join(home, ".claude")):
        return "banned", "~/.claude/"
    for s in (".ssh", ".aws", ".config", ".gnupg", ".netrc"):
        if under(os.path.join(home, s)):
            return "banned", "secret ~/" + s
    top = os.path.relpath(p, root).split("/")[0] if under(root) and p != root else ""
    if top == "gate4-workspace" or re.fullmatch(r"gate5-workspace-\d+", top):
        return "banned", top + "/"
    if p in {os.path.join(root, "envs", x) for x in ("run-sandboxed.sh", "gen/bin/python", "score/bin/python")}:
        return "allowed", os.path.relpath(p, root)
    if under(os.path.join(root, "envs")):
        return "review", "envs other"
    if under(os.path.join(home, ".cache", "huggingface")):
        return "review", "hf cache"
    if p == root:
        return "review", "project root"
    if under(root):
        return "review", "project other"
    if p.startswith(SYSTEM) or p in {"/dev/null", "/tmp"}:
        return "system", p.split("/")[1]
    return "review", "outside project"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    tr, ws, out = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
    root, home = os.path.dirname(ws), os.path.expanduser("~")
    uses = tool_uses(tr)
    names = collections.Counter(u["name"] for u in uses)
    banned, review, web, mentions = [], [], [], []
    allowed, allowed_occ, system = collections.Counter(), collections.Counter(), collections.Counter()
    for u in uses:
        cwd = u["cwd"] or ws
        if u["name"] in WEB_TOOLS or u["name"].startswith("mcp__"):
            web.append({"ts": u["ts"], "tool": u["name"], "input": json.dumps(u["input"])[:300]})
        if u["name"] in ("Agent", "Task"):  # a sub-agent's own tool calls live in another transcript file
            review.append({"ts": u["ts"], "tool": u["name"], "label": "spawned an agent: audit its transcript too",
                           "token": "", "path": "", "context": json.dumps(u["input"])[:300]})
        hit_allowed, seen = set(), set()
        fp = str(u["input"].get("file_path", ""))
        for key, s in strings(u["input"]):
            for url in URL_RE.findall(s):
                web.append({"ts": u["ts"], "tool": u["name"], "field": key, "url": url[:200]})
            # text, not commands: messages, and Write/Edit content of note files (.md, .txt, ...)
            is_text = u["name"] in MSG_TOOLS or (u["name"] in ("Write", "Edit") and key != "file_path"
                                                 and fp.endswith(NOTE_EXT))
            shell = u["name"] in ("Bash", "Monitor") and key == "command"
            # code written by Write/Edit runs later from its own folder or the workspace, not the session cwd.
            # v2 fix: resolve its relative tokens against both; f-string templates ({...}) only get listed.
            code = u["name"] in ("Write", "Edit") and key != "file_path" and not is_text
            bases = [os.path.dirname(fp) or ws, ws] if code else [cwd]
            pairs = [(t, q, b) for b in bases for t, q in tokens(s, b, shell)]
            for tok, p, base in pairs:
                kind, label = classify(p, ws, root, home)
                if code and "{" in tok and kind in ("banned", "review"):
                    kind, label = "review", "code template, unresolved: " + label
                if kind == "allowed":
                    allowed_occ[label] += 1
                if (key, tok, p) in seen:
                    continue
                seen.add((key, tok, p))
                rec = {"ts": u["ts"], "tool": u["name"], "field": key, "token": tok, "path": p, "label": label,
                       "context": s[max(0, s.find(tok) - 80):s.find(tok) + len(tok) + 80].replace("\n", " ")}
                if is_text and kind in ("banned", "review"):
                    rec["kind"] = kind
                    mentions.append(rec)
                elif kind == "banned":
                    banned.append(rec)
                elif kind == "review":
                    review.append(rec)
                elif kind == "allowed":
                    hit_allowed.add(label)
                elif kind == "system":
                    system[label] += 1
        for label in hit_allowed:
            allowed[label] += 1
    if banned or web:
        verdict = f"NOT blind: {len(banned)} banned path hits, {len(web)} web hits"
    elif review:
        verdict = f"blind (no banned path, no web); {len(review)} other-outside hits to review by hand"
    else:
        verdict = "blind: no banned path, no web, nothing else outside the workspace"
    res = {"transcript": os.path.abspath(tr), "workspace": ws, "n_tool_uses": len(uses),
           "tools": dict(names.most_common()),
           "first_ts": uses[0]["ts"] if uses else None, "last_ts": uses[-1]["ts"] if uses else None,
           "verdict": verdict, "n_banned": len(banned), "n_web": len(web), "n_review": len(review),
           "n_mentions_in_text": len(mentions),
           "banned": banned, "web": web, "review": review, "mentions_in_text": mentions,
           "allowed_outside_calls": dict(allowed), "allowed_outside_occurrences": dict(allowed_occ),
           "system_path_tokens": dict(system),
           "limits": ["only tool_use inputs are parsed; what a script reads at run time is seen only if its "
                      "path is written in a tool input (heredoc, Write, Edit) in this transcript",
                      "paths built at run time (os.path.join pieces, variables) are not resolved",
                      "the model's training data cannot be audited"]}
    with open(out, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_tool_uses", "tools", "verdict", "n_banned", "n_web",
                                          "n_review", "n_mentions_in_text", "allowed_outside_calls",
                                          "allowed_outside_occurrences")}))
    for r in review:
        print("REVIEW", r["ts"], r["tool"], r["label"], r["token"], "::", r["context"][:200])
    for r in banned:
        print("BANNED", r["ts"], r["tool"], r["label"], r["token"], "::", r["context"][:200])


if __name__ == "__main__":
    main()
