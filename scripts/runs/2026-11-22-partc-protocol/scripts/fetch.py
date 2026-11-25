"""download urls to files and log url, http headers, size, sha256, utc time (stdlib only).

usage: python3 -I fetch.py <log.jsonl> <url> <out_path> [<url> <out_path> ...]
an existing out_path is not fetched again (its log line is kept). no token is sent.
"""
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (generic research client)"
KEEP = ("x-repo-commit", "etag", "x-linked-etag", "x-linked-size", "last-modified",
        "content-length", "content-type")


def get(url, tries=8):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.geturl(), {h: r.headers.get(h) for h in KEEP}, r.read()
        except Exception as e:  # noqa: BLE001 - logged, retried, then raised
            print(f"retry {k + 1} {url}: {e}", file=sys.stderr, flush=True)
            time.sleep(5 * (k + 1))
    raise SystemExit(f"fetch failed: {url}")


def main():
    log, pairs = sys.argv[1], sys.argv[2:]
    assert pairs and len(pairs) % 2 == 0, __doc__
    with open(log, "a") as fl:
        for url, out in zip(pairs[::2], pairs[1::2]):
            if os.path.exists(out):
                continue
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            status, final, hdr, body = get(url)
            with open(out, "wb") as f:
                f.write(body)
            rec = {"url": url, "final_url": final, "status": status, "headers": hdr,
                   "path": out, "size": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                   "fetched_at_utc": t}
            fl.write(json.dumps(rec) + "\n")
            fl.flush()
            print(status, len(body), out, flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
