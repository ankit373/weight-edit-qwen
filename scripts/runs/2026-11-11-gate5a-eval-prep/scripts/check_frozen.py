"""check a frozen part A diff before any use. stdlib only, no torch, no model.

usage: check_frozen.py <diff_dir> <diff_sha256> <out.json> [--rows <editor_dev_rows.jsonl>]

refuses (exit 1) unless:
  sha256 of <diff_dir>/diff.safetensors == <diff_sha256>
  manifest.json diff_file_sha256 == <diff_sha256>
  manifest format / model / revision / base file sha256 == the gate 4 diff tools' values (0.8b pin)
writes <out.json>: the hashes (diff file, manifest, editor dev rows) and the manifest's tensor summary.
"""
import hashlib
import json
import os
import sys

# gate5-workspace-*/tools/common.py lines 6-9 and apply_diff.py FORMAT (byte copies of gate 4)
WANT = {"format": "gate4-diff-v1", "model": "Qwen/Qwen3.5-0.8B",
        "revision": "2fc06364715b967f1860aea9cf38778875588b17",
        "base_file_sha256": "04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    a = sys.argv[1:]
    rows = None
    if "--rows" in a:
        i = a.index("--rows")
        rows = a[i + 1]
        del a[i:i + 2]
    if len(a) != 3:
        sys.exit(__doc__)
    diff_dir, want_sha, out = a
    if len(want_sha) != 64 or any(c not in "0123456789abcdef" for c in want_sha):
        sys.exit(f"REFUSED: not a lowercase sha256: {want_sha}")
    path = os.path.join(diff_dir, "diff.safetensors")
    man_path = os.path.join(diff_dir, "manifest.json")
    for p in (path, man_path) + ((rows,) if rows else ()):
        if not os.path.isfile(p):
            sys.exit(f"REFUSED: missing file {p}")
    got = sha256(path)
    man = json.load(open(man_path))
    errors = []
    if got != want_sha:
        errors.append(f"diff.safetensors sha256 {got} != given {want_sha}")
    if man.get("diff_file_sha256") != want_sha:
        errors.append(f"manifest diff_file_sha256 {man.get('diff_file_sha256')} != given {want_sha}")
    for k, v in WANT.items():
        if man.get(k) != v:
            errors.append(f"manifest {k} {man.get(k)} != {v}")
    res = {"diff_dir": os.path.abspath(diff_dir), "given_sha256": want_sha, "diff_file_sha256": got,
           "manifest_sha256": sha256(man_path), "ok": not errors, "errors": errors,
           "editor_dev_rows": os.path.abspath(rows) if rows else None,
           "editor_dev_rows_sha256": sha256(rows) if rows else None,
           "tensors": {n: {k: t.get(k) for k in ("shape", "n_changed", "delta_fro", "base_sha256",
                                                 "edited_sha256", "tied_with")}
                       for n, t in man.get("tensors", {}).items()}}
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("diff_file_sha256", "manifest_sha256", "ok", "errors")}))
    if errors:
        sys.exit("REFUSED: " + "; ".join(errors))


if __name__ == "__main__":
    main()
