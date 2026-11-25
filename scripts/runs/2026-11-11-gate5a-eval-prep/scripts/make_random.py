"""random-edit control diffs for part B (plan D7), cpu. rewrite of gate 4 eval make_random.py.

rule (D7): for every tensor in the frozen edit, same tensor, same changed positions
(edited != base, compared in the stored dtype), same Frobenius norm of the change, random
gaussian direction on those positions. nothing about the edit is hard-coded.

usage: make_random.py [--tools DIR] <final_diff_dir> <out_root> <seed> [<seed> ...]
  --tools  diff tools folder (default gate5b-workspace/tools, the 2B copy of the gate 4 tools)

per seed: one torch.Generator(cpu).manual_seed(seed); tensors in sorted name order; per tensor
r ~ N(0, 1)^k in float64 (k = changed positions), new = base + s * r, cast to the tensor dtype.
an entry that rounds back to its base value is moved one dtype step in the sign of r, so the
changed positions stay exactly the edit's. s is reset twice by target / realized norm.
checks (exit 1 if broken): changed-position mask equal to the edit's, |fro / target - 1| < TOL.
the diff is saved with the tools' apply_diff.save_diff (hashes in the manifest).
"""
import argparse
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "gate5b-workspace", "tools"))
TOL = 1e-3  # ours: relative fro error allowed after the rescale
BATCH_MIN_K = 10000  # ours: batch rounding moves only above this many changed entries


def step_away(base, d):
    """one representable step from base in direction d (+1 / -1), same dtype (bf16/fp16/fp32)."""
    ib = {torch.bfloat16: torch.int16, torch.float16: torch.int16, torch.float32: torch.int32}[base.dtype]
    sign_bit = 1 << (torch.iinfo(ib).bits - 1)
    i = base.view(ib).to(torch.int64)  # sign-magnitude float bits, sign-extended
    mag, neg, down = i & (sign_bit - 1), i < 0, d < 0
    away = (mag == 0) | (neg == down)  # step grows |x| (or leaves zero)
    new_mag = torch.where(away, mag + 1, mag - 1)
    new_neg = torch.where(mag == 0, down, neg)
    u = new_mag + new_neg.to(torch.int64) * sign_bit  # unsigned pattern
    return torch.where(u >= sign_bit, u - 2 * sign_bit, u).to(ib).view(base.dtype)


def control_tensor(base, mask, target, gen):
    """random change on mask positions with fro norm ~ target. returns new tensor and info."""
    flat_b = base.reshape(-1)
    idx = torch.nonzero(mask.reshape(-1)).squeeze(1)
    b = flat_b[idx]
    r = torch.randn(idx.numel(), dtype=torch.float64, generator=gen)
    scale = target / float(r.norm())
    for i in range(3):
        v = b.double() + scale * r
        vals = v.to(base.dtype)
        stuck = vals == b
        if bool(stuck.any()):
            vals[stuck] = step_away(b[stuck], torch.sign(r[stuck]))
        got = float((vals.double() - b.double()).norm())
        if i < 2:
            scale *= target / got
    vals, n_switch = fix_rounding(b, v, vals, r, target)
    new = flat_b.clone()
    new[idx] = vals
    new = new.reshape(base.shape)
    return new, r, {"k": idx.numel(), "n_stepped": int(stuck.sum()), "n_rounding_switched": n_switch,
                    "scale": scale}


def fix_rounding(b, v, cur, r, target, max_iter=500):
    """greedy: move single entries to their other dtype neighbour of v (never onto the base value)
    while that brings sum(delta^2) closer to target^2. only matters for small k / 1-step edits."""
    d = torch.where(v != cur.double(), torch.sign(v - cur.double()), torch.sign(r))
    alt = step_away(cur, d)
    ok = alt != b
    cur, alt = cur.clone(), alt.clone()
    sq = lambda x: (x.double() - b.double()) ** 2
    s_cur, s_alt = sq(cur), sq(alt)
    t2, total, n = target ** 2, float(sq(cur).sum()), 0
    # large k only: one batch of the smallest useful moves, stopping short of the gap (the
    # single-move loop below then polishes). small k keeps its fine moves for that loop.
    gain = torch.where(ok, s_alt - s_cur, torch.zeros_like(s_cur))
    err = total - t2
    cand = torch.nonzero(gain * err < 0).squeeze(1)
    if cand.numel() and b.numel() > BATCH_MIN_K:
        order = cand[gain[cand].abs().argsort()]
        csum = gain[order].abs().cumsum(0)
        m = int(torch.searchsorted(csum, torch.tensor(abs(err), dtype=csum.dtype)))
        sel = order[:m]
        if m:
            total += float(gain[sel].sum())
            cur[sel], alt[sel] = alt[sel].clone(), cur[sel].clone()
            s_cur[sel], s_alt[sel] = s_alt[sel].clone(), s_cur[sel].clone()
            n += m
    for _ in range(max_iter):
        err = total - t2
        if abs(err) <= 1e-9 * t2:  # already as close as float64 sums can tell
            break
        new_err = torch.where(ok, (err + s_alt - s_cur).abs(), torch.full_like(s_cur, float("inf")))
        j = int(new_err.argmin())
        if float(new_err[j]) >= abs(err):
            break
        total += float(s_alt[j] - s_cur[j])
        cur[j], alt[j] = alt[j].clone(), cur[j].clone()
        s_cur[j], s_alt[j] = s_alt[j].clone(), s_cur[j].clone()
        n += 1
    return cur, n


def make_controls(model, final_dir, out_root, seeds, apply_diff, common):
    from safetensors.torch import load_file
    man = json.load(open(os.path.join(final_dir, "manifest.json")))
    if common.file_sha256(os.path.join(final_dir, "diff.safetensors")) != man["diff_file_sha256"]:
        sys.exit("final diff file hash mismatch")
    if (man["model"], man["revision"]) != (common.MODEL, common.REVISION):
        sys.exit("final diff is for another model or revision")
    sd = model.state_dict()
    edited = load_file(os.path.join(final_dir, "diff.safetensors"))
    names = sorted(man["tensors"])
    final = {}
    for name in names:
        base = sd[name].detach().to("cpu")
        if common.tensor_sha256(base) != man["tensors"][name]["base_sha256"]:
            sys.exit(f"{name}: loaded base is not the edit's base")
        e = edited[name].to(base.dtype)
        mask = e != base
        delta = e.double() - base.double()
        final[name] = {"base": base, "mask": mask, "delta": delta, "target": float(delta.norm())}
    info = {"final_dir": final_dir, "final_diff_file_sha256": man["diff_file_sha256"], "tol": TOL,
            "tensors": {n: {"n_changed": int(f["mask"].sum()), "fro_measured": f["target"],
                            "fro_manifest": man["tensors"][n]["delta_fro"]} for n, f in final.items()},
            "seeds": {}}
    bad = []
    for seed in seeds:
        g = torch.Generator().manual_seed(seed)
        new_t, per = {}, {}
        for name in names:
            f = final[name]
            if f["target"] == 0:
                bad.append(f"{name}: zero change in the final edit")
                continue
            new, r, extra = control_tensor(f["base"], f["mask"], f["target"], g)
            mask_ok = bool(torch.equal(new != f["base"], f["mask"]))
            fro = float((new.double() - f["base"].double()).norm())
            fd = f["delta"].reshape(-1)[torch.nonzero(f["mask"].reshape(-1)).squeeze(1)]
            cos = float(torch.dot(r, fd) / (r.norm() * fd.norm()))
            per[name] = {**extra, "mask_equal": mask_ok, "fro": fro, "fro_rel_err": fro / f["target"] - 1,
                         "cos_with_final_delta": cos}
            if not mask_ok or abs(fro / f["target"] - 1) >= TOL:
                bad.append(f"seed {seed} {name}: mask_equal={mask_ok} fro={fro} target={f['target']}")
            new_t[name] = new
        out = os.path.join(out_root, f"rand_s{seed}")
        m = apply_diff.save_diff(model, new_t, out, note=json.dumps(
            {"kind": "random_control_D7", "seed": seed, "final_diff_file_sha256": man["diff_file_sha256"]}))
        for name in names:
            t = m["tensors"][name]
            per[name].update({"n_changed": t["n_changed"], "delta_fro": t["delta_fro"],
                              "base_sha256": t["base_sha256"], "edited_sha256": t["edited_sha256"],
                              "base_sha256_equals_final": t["base_sha256"] == man["tensors"][name]["base_sha256"]})
        info["seeds"][seed] = {"dir": out, "diff_file_sha256": m["diff_file_sha256"], "tensors": per}
        print(json.dumps({seed: info["seeds"][seed]}), flush=True)
    info["failed_checks"] = bad
    with open(os.path.join(out_root, "random_controls.json"), "w") as fh:
        json.dump(info, fh, indent=1)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tools", default=DEFAULT_TOOLS)
    ap.add_argument("final_dir")
    ap.add_argument("out_root")
    ap.add_argument("seeds", type=int, nargs="+")
    a = ap.parse_args()
    sys.path.insert(0, os.path.abspath(a.tools))
    import apply_diff  # noqa: E402
    import common  # noqa: E402
    model = common.load_model("cpu", "bfloat16")
    info = make_controls(model, os.path.abspath(a.final_dir), a.out_root, a.seeds, apply_diff, common)
    if info["failed_checks"]:
        print(json.dumps({"failed_checks": info["failed_checks"]}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
