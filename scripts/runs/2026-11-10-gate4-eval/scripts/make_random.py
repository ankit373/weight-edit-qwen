"""random-edit control diffs (cpu). same tensor and column as the frozen edit, same entry count,
same Frobenius norm of the change, random direction.

usage: make_random.py <final_diff_dir> <out_root> <seed> [<seed> ...]

per seed: r ~ N(0, 1)^1024 (torch.Generator(cpu).manual_seed(seed), float64), scaled to the
final edit's measured delta_fro, added to the base column in float32, cast to bf16. one
correction: the scale is reset once by target / realized norm (bf16 rounding), then re-cast.
the diff is saved with gate4-workspace/tools/apply_diff.save_diff (hashes in the manifest).
"""
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "gate4-workspace", "tools"))
sys.path.insert(0, TOOLS)
import apply_diff  # noqa: E402
import common  # noqa: E402
from safetensors.torch import load_file  # noqa: E402

NAME = "model.layers.15.mlp.down_proj.weight"
COL = 1047


def main():
    final_dir, out_root, seeds = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3:]]
    man = json.load(open(os.path.join(final_dir, "manifest.json")))
    if common.file_sha256(os.path.join(final_dir, "diff.safetensors")) != man["diff_file_sha256"]:
        sys.exit("final diff file hash mismatch")
    model = common.load_model("cpu", "bfloat16")
    base = model.state_dict()[NAME].detach().clone()
    edited = load_file(os.path.join(final_dir, "diff.safetensors"))[NAME]
    delta = edited.float() - base.float()
    cols = sorted(set(torch.nonzero(delta)[:, 1].tolist()))
    target = float(delta.norm())
    final_col = delta[:, COL].double()
    info = {"tensor": NAME, "column": COL, "final_changed_columns": cols,
            "final_n_changed": int((edited != base).sum()), "final_delta_fro_measured": target,
            "final_delta_fro_manifest": man["tensors"][NAME]["delta_fro"], "seeds": {}}
    assert cols == [COL], cols
    for seed in seeds:
        g = torch.Generator().manual_seed(seed)
        r = torch.randn(base.shape[0], dtype=torch.float64, generator=g)
        scale = target / float(r.norm())
        for _ in range(2):
            new = base.clone()
            new[:, COL] = (base[:, COL].float() + (scale * r).float()).to(base.dtype)
            got = float((new.float() - base.float()).norm())
            if _ == 0:
                scale *= target / got
        out = os.path.join(out_root, f"rand_s{seed}")
        m = apply_diff.save_diff(model, {NAME: new}, out,
                                 note=json.dumps({"kind": "random_control", "seed": seed,
                                                  "column": COL, "target_fro": target}))
        t = m["tensors"][NAME]
        cos = float(torch.dot(r, final_col) / (r.norm() * final_col.norm()))
        info["seeds"][seed] = {"dir": out, "diff_file_sha256": m["diff_file_sha256"],
                               "n_changed": t["n_changed"], "delta_fro": t["delta_fro"],
                               "edited_sha256": t["edited_sha256"],
                               "cos_with_final_delta": cos}
        print(json.dumps({seed: info["seeds"][seed]}), flush=True)
    with open(os.path.join(out_root, "random_controls.json"), "w") as f:
        json.dump(info, f, indent=1)


if __name__ == "__main__":
    main()
