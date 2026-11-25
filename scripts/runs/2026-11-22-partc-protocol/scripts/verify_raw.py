"""check every file under <dir>/raw against the last fetch_log.jsonl line for its path.

usage: python3 -I verify_raw.py <data/partc/name> [--delete-bad]
prints counts; with --delete-bad, removes files with no log line or a sha256 mismatch.
"""
import hashlib
import json
import os
import sys


def main():
    d, delete = sys.argv[1], "--delete-bad" in sys.argv
    logged = {}
    with open(os.path.join(d, "fetch_log.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            logged[os.path.normpath(r["path"])] = r["sha256"]
    ok, bad = 0, []
    for root, _, files in os.walk(os.path.join(d, "raw")):
        for name in files:
            p = os.path.normpath(os.path.join(root, name))
            with open(p, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            if logged.get(p) == h:
                ok += 1
            else:
                bad.append(p)
    for p in bad:
        print("bad", p)
        if delete:
            os.remove(p)
    print(json.dumps({"ok": ok, "bad": len(bad)}))


if __name__ == "__main__":
    main()
