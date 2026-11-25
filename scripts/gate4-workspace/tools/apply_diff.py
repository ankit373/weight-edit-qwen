"""weight diffs: save, check and apply (in memory only; the base files are never written).

a diff is a folder with
  diff.safetensors   the edited values of each changed tensor, keyed by Qwen3_5ForCausalLM
                     state_dict name (e.g. model.layers.20.mlp.down_proj.weight)
  manifest.json      model, revision, base file sha256, diff file sha256, and per tensor:
                     shape, dtype, base_sha256, edited_sha256, n_changed, delta_fro

usage:
  apply_diff.py check <diff_dir> [--device cpu|mps]   load base, apply, verify every hash
  apply_diff.py noop <out_dir> --tensor <name> [...]   zero-change diff (for tests)
in python:  from apply_diff import save_diff, apply_diff
"""
import argparse
import json
import os
import sys

import torch
from safetensors.torch import load_file, save_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

FORMAT = "gate4-diff-v1"


def tied_aliases(model):
    """state_dict names that share storage with another name (e.g. tied embedding / lm_head)."""
    by_ptr = {}
    for name, t in model.state_dict(keep_vars=True).items():
        by_ptr.setdefault(t.data_ptr(), []).append(name)
    return {n: [m for m in names if m != n] for names in by_ptr.values() if len(names) > 1 for n in names}


def save_diff(model, edited, out_dir, note=""):
    """model = unedited base model. edited = {name: tensor} new values. writes out_dir/."""
    common.check_base_file()
    sd = model.state_dict()
    aliases = tied_aliases(model)
    os.makedirs(out_dir, exist_ok=False)
    tensors, store = {}, {}
    for name, new in edited.items():
        base = sd[name]
        new = new.detach().to("cpu", base.dtype).contiguous()
        if tuple(new.shape) != tuple(base.shape):
            raise ValueError(f"{name}: shape {tuple(new.shape)} != base {tuple(base.shape)}")
        b = base.detach().to("cpu")
        delta = new.float() - b.float()
        tensors[name] = {
            "shape": list(base.shape), "dtype": str(base.dtype).removeprefix("torch."),
            "base_sha256": common.tensor_sha256(b), "edited_sha256": common.tensor_sha256(new),
            "n_changed": int((new != b).sum()), "n_total": base.numel(),
            "delta_fro": float(delta.norm()), "base_fro": float(b.float().norm()),
            "tied_with": aliases.get(name, []),
        }
        store[name] = new
    path = os.path.join(out_dir, "diff.safetensors")
    save_file(store, path)
    manifest = {
        "format": FORMAT, "model": common.MODEL, "revision": common.REVISION,
        "model_class": "Qwen3_5ForCausalLM", "base_file_sha256": common.BASE_FILE_SHA256,
        "diff_file_sha256": common.file_sha256(path), "note": note, "tensors": tensors,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def apply_diff(model, diff_dir):
    """check base file, diff file and per-tensor base hashes, copy the edits in, check edited hashes."""
    with open(os.path.join(diff_dir, "manifest.json")) as f:
        man = json.load(f)
    if man.get("format") != FORMAT or man["model"] != common.MODEL or man["revision"] != common.REVISION:
        raise SystemExit("diff manifest is for another format, model or revision")
    common.check_base_file()
    path = os.path.join(diff_dir, "diff.safetensors")
    got = common.file_sha256(path)
    if got != man["diff_file_sha256"]:
        raise SystemExit(f"diff file sha256 mismatch: {got}")
    store = load_file(path)
    if set(store) != set(man["tensors"]):
        raise SystemExit("diff file and manifest list different tensors")
    sd = model.state_dict()
    for name, info in man["tensors"].items():
        if common.tensor_sha256(sd[name]) != info["base_sha256"]:
            raise SystemExit(f"{name}: model tensor is not the base tensor (hash mismatch)")
    with torch.no_grad():
        for name in man["tensors"]:
            sd[name].copy_(store[name].to(sd[name].device))
    for name, info in man["tensors"].items():
        if common.tensor_sha256(sd[name]) != info["edited_sha256"]:
            raise SystemExit(f"{name}: edited hash mismatch after apply")
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "noop"])
    ap.add_argument("dir")
    ap.add_argument("--tensor", nargs="+")
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    model = common.load_model(a.device, "bfloat16")
    if a.cmd == "noop":
        sd = model.state_dict()
        man = save_diff(model, {n: sd[n].clone() for n in a.tensor}, a.dir,
                        note="zero-change diff for tool tests")
    else:
        man = apply_diff(model, a.dir)
    summary = {n: {k: v for k, v in i.items() if k in ("n_changed", "delta_fro", "base_sha256",
                                                        "edited_sha256", "tied_with")}
               for n, i in man["tensors"].items()}
    print(json.dumps({"cmd": a.cmd, "diff_file_sha256": man["diff_file_sha256"], "ok": True,
                      "tensors": summary}, indent=1))


if __name__ == "__main__":
    main()
