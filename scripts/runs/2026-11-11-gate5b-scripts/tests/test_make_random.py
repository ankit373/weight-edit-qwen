"""cpu test of scripts/make_random.py on a small fake diff. no real weights, no forward pass.

usage (project root): envs/run-sandboxed.sh envs/gen/bin/python -I -B \
  runs/2026-11-11-gate5b-scripts/tests/test_make_random.py <scratch_dir>
fake model: a few bf16 tensors with the real state_dict names (one tied pair), random values.
fake tools: the gate 4 apply_diff.py / common.py logic, copied in as mock_tools/ (2B constants),
with check_base_file stubbed (there is no fake base file). exit 1 on any failed check.
"""
import json
import os
import shutil
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "mock_tools"))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import apply_diff  # noqa: E402
import common  # noqa: E402
import make_random  # noqa: E402

common.check_base_file = lambda: common.BASE_FILE_SHA256  # no fake base file to hash
SEEDS = [1001, 1002, 1003]
out = os.path.abspath(sys.argv[1])
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)


class Fake(torch.nn.Module):
    def __init__(self):
        super().__init__()
        g = torch.Generator().manual_seed(0)
        mk = lambda *s: torch.nn.Parameter((torch.randn(*s, generator=g) * 0.05).to(torch.bfloat16))
        self.embed = mk(64, 32)
        self.lm_head = self.embed  # tied, like Qwen3.5
        self.down = mk(32, 48)
        self.q = mk(32, 32)

    def state_dict(self, *a, **k):
        sd = super().state_dict(*a, **k)
        names = {"embed": "model.embed_tokens.weight", "lm_head": "lm_head.weight",
                 "down": "model.layers.15.mlp.down_proj.weight", "q": "model.layers.3.self_attn.q_proj.weight"}
        return {names[n]: t for n, t in sd.items()}


torch.manual_seed(1)
model = Fake()
sd = model.state_dict()
D, Q, E = "model.layers.15.mlp.down_proj.weight", "model.layers.3.self_attn.q_proj.weight", "model.embed_tokens.weight"
# fake frozen edit: one full column (gate 4 shape), scattered tiny entries (forces the round-back
# step), one row of the tied embedding
ed = {n: sd[n].detach().clone() for n in (D, Q, E)}
ed[D][:, 7] = (ed[D][:, 7].float() + 0.3 * torch.randn(32)).to(torch.bfloat16)
pos = torch.randperm(32 * 32)[:50]
flat = ed[Q].view(-1)
flat[pos] = (flat[pos].float() * (1 + 2 ** -7)).to(torch.bfloat16)  # about one bf16 step
ed[E][5] = (ed[E][5].float() + 0.1 * torch.randn(32)).to(torch.bfloat16)
final = os.path.join(out, "final")
fm = apply_diff.save_diff(model, ed, final, note="fake final edit for the make_random test")

ctrl = os.path.join(out, "controls")
os.makedirs(ctrl)
info = make_random.make_controls(model, final, ctrl, SEEDS, apply_diff, common)
again = os.path.join(out, "controls_again")
os.makedirs(again)
info2 = make_random.make_controls(model, final, again, SEEDS[:1], apply_diff, common)

res, bad = {"final": {n: {k: t[k] for k in ("n_changed", "delta_fro", "base_sha256")} for n, t in fm["tensors"].items()}}, []
bad += info["failed_checks"]
for seed in SEEDS:
    d = os.path.join(ctrl, f"rand_s{seed}")
    m = json.load(open(os.path.join(d, "manifest.json")))
    r = {"diff_file_sha256_ok": common.file_sha256(os.path.join(d, "diff.safetensors")) == m["diff_file_sha256"]}
    fresh = Fake()  # same seed 0 init -> the same base values
    apply_diff.apply_diff(fresh, d)  # exits on any hash mismatch
    fsd = fresh.state_dict()
    for n, t in m["tensors"].items():
        f = fm["tensors"][n]
        base = sd[n]
        new_mask = fsd[n] != base
        fin = apply_diff.load_file(os.path.join(final, "diff.safetensors"))[n] != base
        r[n] = {"base_sha256_equal": t["base_sha256"] == f["base_sha256"],
                "positions_equal": bool(torch.equal(new_mask, fin)),
                "n_changed": [t["n_changed"], f["n_changed"]],
                "fro": [t["delta_fro"], f["delta_fro"]],
                "fro_rel_err": t["delta_fro"] / f["delta_fro"] - 1,
                "n_stepped": info["seeds"][seed]["tensors"][n]["n_stepped"],
                "cos_with_final": info["seeds"][seed]["tensors"][n]["cos_with_final_delta"]}
        ok = r[n]["base_sha256_equal"] and r[n]["positions_equal"] and abs(r[n]["fro_rel_err"]) < make_random.TOL
        ok &= t["n_changed"] == f["n_changed"]
        if not ok:
            bad.append(f"seed {seed} {n}")
    if E in m["tensors"]:
        r["tied_lm_head_follows"] = bool(torch.equal(fsd["lm_head.weight"], fsd[E]))
        bad += [] if r["tied_lm_head_follows"] else [f"seed {seed} tied"]
    bad += [] if r["diff_file_sha256_ok"] else [f"seed {seed} file sha"]
    res[seed] = r
shas = [info["seeds"][s]["diff_file_sha256"] for s in SEEDS]
res["seeds_differ"] = len(set(shas)) == len(shas)
res["same_seed_same_diff"] = info2["seeds"][SEEDS[0]]["diff_file_sha256"] == shas[0]
bad += [] if res["seeds_differ"] else ["seeds give the same diff"]
bad += [] if res["same_seed_same_diff"] else ["same seed not reproducible"]
# step_away: one dtype step, both directions, through zero and negatives
x = torch.tensor([0.0, -0.0, 1.0, -1.0, 3e-3, -3e-3], dtype=torch.bfloat16)
for d in (1.0, -1.0):
    y = make_random.step_away(x, torch.full((6,), d))
    moved = ((y.double() - x.double()) * d > 0).all().item()
    tight = all(((x[i:i+1].double() + (y[i:i+1].double() - x[i:i+1].double()) / 2).to(torch.bfloat16) in (x[i], y[i]))
                for i in range(6))
    res[f"step_away_{d:+.0f}"] = {"moved_right_way": bool(moved), "one_step": bool(tight), "y": y.float().tolist()}
    bad += [] if moved and tight else [f"step_away {d}"]
res["failed"] = bad
print(json.dumps(res, indent=1))
sys.exit(1 if bad else 0)
