"""check every part C prompt-set file against the sha256 table in PROTOCOL.md section 9. stdlib only.

usage (project root): check_sets.py [--protocol PATH] [--out OUT.json]
exit 1 if a file is missing or its sha256 differs, or the table has no rows.
"""
import hashlib
import json
import re
import sys

PROTOCOL = "runs/2026-11-22-partc-protocol/PROTOCOL.md"
ROW = re.compile(r"^\| `(data/partc/[^`]+)` \| `([0-9a-f]{64})` \|$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def table(protocol):
    """(path, sha) rows of the section 9 table."""
    text = open(protocol, encoding="utf-8").read()
    sec = text.split("## 9. files", 1)[1].split("\n## ", 1)[0]
    return [m.groups() for m in map(ROW.match, sec.splitlines()) if m]


def main():
    a = sys.argv[1:]
    protocol = a[a.index("--protocol") + 1] if "--protocol" in a else PROTOCOL
    out = a[a.index("--out") + 1] if "--out" in a else None
    rows = table(protocol)
    res = {"protocol": protocol, "protocol_sha256": sha256(protocol), "files": []}
    bad = []
    for path, want in rows:
        try:
            got = sha256(path)
        except FileNotFoundError:
            got = None
        res["files"].append({"path": path, "want": want, "got": got, "ok": got == want})
        if got != want:
            bad.append(path)
    res["n"], res["bad"] = len(rows), bad
    res["ok"] = bool(rows) and not bad
    if out:
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
    print(json.dumps({"n": res["n"], "bad": bad, "ok": res["ok"]}))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
