"""compare a built checkpoint with the base file, tensor by tensor, chunked reads (low memory).

usage: verify_ckpt.py <base.safetensors> <built.safetensors> <manifest.json> <out.json>

pass = same tensor names, dtypes, shapes; manifest tensors hash to base_sha256 before and
edited_sha256 after; every other tensor byte-equal to the base.
"""
import hashlib
import json
import struct
import sys

CHUNK = 1 << 20


def header(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        head = json.loads(f.read(n))
    head.pop("__metadata__", None)
    return head, 8 + n


def tensor_sha(f, off, info):
    a, b = info["data_offsets"]
    f.seek(off + a)
    h, left = hashlib.sha256(), b - a
    while left:
        block = f.read(min(CHUNK, left))
        h.update(block)
        left -= len(block)
    return h.hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def main(base_path, built_path, man_path, out_path):
    hb, ob = header(base_path)
    he, oe = header(built_path)
    man = {t["name"]: t for t in json.load(open(man_path))["tensors"]}
    res = {"base_file": base_path, "built_file": built_path,
           "base_file_sha256": file_sha(base_path), "built_file_sha256": file_sha(built_path),
           "same_names": sorted(hb) == sorted(he), "meta_mismatch": [], "unexpected_changes": [],
           "edited": {}}
    with open(base_path, "rb") as fb, open(built_path, "rb") as fe:
        for name in sorted(hb):
            if name not in he:
                continue
            ib, ie = hb[name], he[name]
            if (ib["dtype"], ib["shape"]) != (ie["dtype"], ie["shape"]):
                res["meta_mismatch"].append(name)
                continue
            sb, se = tensor_sha(fb, ob, ib), tensor_sha(fe, oe, ie)
            if name in man:
                res["edited"][name] = {
                    "sha256_before": sb, "sha256_after": se,
                    "before_ok": sb == man[name]["base_sha256"],
                    "after_ok": se == man[name]["edited_sha256"]}
            elif sb != se:
                res["unexpected_changes"].append(name)
    res["n_tensors"] = len(hb)
    res["pass"] = (res["same_names"] and not res["meta_mismatch"] and not res["unexpected_changes"]
                   and len(res["edited"]) == len(man)
                   and all(v["before_ok"] and v["after_ok"] for v in res["edited"].values()))
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
