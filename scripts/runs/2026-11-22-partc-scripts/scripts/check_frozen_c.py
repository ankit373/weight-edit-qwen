"""check one frozen part C edit before use. stdlib only, no torch, no model.

usage (project root): check_frozen_c.py <edit> <out.json>
prints "<diff dir> <diff sha256>" on the last stdout line when ok; exit 1 (REFUSED) otherwise.

checks, for <edit> in EDITS (PROTOCOL.md section 1):
  diff.safetensors sha256 == the PROTOCOL.md diff sha == SHA_CHECK.json diff_expected
  manifest.json sha256 == SHA_CHECK.json manifest_expected; manifest diff_file_sha256 == the diff sha
  manifest format / model / revision / base_file_sha256 == the pin of that edit's model
  release copy runs/2026-11-12-gate5-release/hf-models/<edit>/diff.safetensors has the same sha256
"""
import hashlib
import json
import os
import sys

SHA_CHECK = "runs/2026-11-12-gate5-release/hf-models/SHA_CHECK.json"
RELEASE = "runs/2026-11-12-gate5-release/hf-models"
PINS = {  # check_frozen.py (gate5a eval-prep) WANT for the 0.8B; run_2b.py / c06 manifest for the 2B
    "0.8b": {"format": "gate4-diff-v1", "model": "Qwen/Qwen3.5-0.8B",
             "revision": "2fc06364715b967f1860aea9cf38778875588b17",
             "base_file_sha256": "04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696"},
    "2b": {"format": "gate4-diff-v1", "model": "Qwen/Qwen3.5-2B",
           "revision": "15852e8c16360a2fea060d615a32b45270f8a8fc",
           "base_file_sha256": "aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1"},
}
EDITS = {  # edit: (model, diff dir, diff sha from PROTOCOL.md section 1)
    "c02_nb_L15u1047_k2": ("0.8b", "gate4-workspace/candidates/c02_nb_L15u1047_k2",
                           "b96ac6f72020da49d39e4f7b89ba1f9854e2e0461a0d80c308723aa40d792824"),
    "h5_a2_n5": ("0.8b", "gate5-workspace-1/candidates/h5_a2_n5",
                 "bd4e68b981c939b5bec42b6d103651ddd1309030e44fed5e6a5a0eb772bfa41e"),
    "mix21_22b0.75_23b0.5": ("0.8b", "gate5-workspace-2/candidates/mix21_22b0.75_23b0.5",
                             "d78e7b1bc77a5969c7bc260950bcda4a19c1b7872c47c09e790dfca0b1e7758d"),
    "combo_a14_b14": ("0.8b", "gate5-workspace-3/candidates/combo_a14_b14",
                      "b86d058a80f35a6747748028179e6c227909436322a435dccf228b921e050f1f"),
    "c06": ("2b", "gate5b-workspace/candidates/c06",
            "eb3bc15fd70f9257323e35e3895ca07661d6b6c83a5e3c370245eed7fe903bba"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(edit):
    if edit not in EDITS:
        return None, [f"unknown edit {edit}"], {}
    model, d, want = EDITS[edit]
    errors = []
    sc = {e["edit"]: e for e in json.load(open(SHA_CHECK))}.get(edit)
    if sc is None:
        return d, [f"{edit} not in {SHA_CHECK}"], {}
    if os.path.normpath(sc["source"]) != os.path.normpath(d):
        errors.append(f"SHA_CHECK source {sc['source']} != {d}")
    paths = {"diff": os.path.join(d, "diff.safetensors"), "manifest": os.path.join(d, "manifest.json"),
             "release": os.path.join(RELEASE, edit, "diff.safetensors")}
    missing = [p for p in paths.values() if not os.path.isfile(p)]
    if missing:
        return d, [f"missing file {p}" for p in missing], {}
    got = {k: sha256(p) for k, p in paths.items()}
    man = json.load(open(paths["manifest"]))
    if got["diff"] != want:
        errors.append(f"diff.safetensors {got['diff']} != protocol {want}")
    if sc["diff_expected"] != want:
        errors.append(f"SHA_CHECK diff_expected {sc['diff_expected']} != protocol {want}")
    if got["manifest"] != sc["manifest_expected"]:
        errors.append(f"manifest.json {got['manifest']} != SHA_CHECK {sc['manifest_expected']}")
    if man.get("diff_file_sha256") != want:
        errors.append(f"manifest diff_file_sha256 {man.get('diff_file_sha256')} != {want}")
    if got["release"] != want:
        errors.append(f"release copy {got['release']} != {want}")
    for k, v in PINS[model].items():
        if man.get(k) != v:
            errors.append(f"manifest {k} {man.get(k)} != {v}")
    info = {"edit": edit, "model": model, "diff_dir": d, "protocol_diff_sha256": want, "got": got,
            "manifest_expected": sc["manifest_expected"],
            "tensors": {n: {k: t.get(k) for k in ("base_sha256", "edited_sha256", "n_changed")}
                        for n, t in man.get("tensors", {}).items()}}
    return d, errors, info


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    edit, out = sys.argv[1:]
    d, errors, info = check(edit)
    res = dict(info, ok=not errors, errors=errors)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    if errors:
        sys.exit("REFUSED: " + "; ".join(errors))
    print(json.dumps({"edit": edit, "ok": True}))
    print(d, EDITS[edit][2])


if __name__ == "__main__":
    main()
