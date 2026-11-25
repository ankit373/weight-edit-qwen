"""cpu timing + norm check of make_random.control_tensor on one synthetic 2048 x 6144 bf16 tensor
(2B down_proj shape, random values, not model weights), three fake edit shapes."""
import json, os, sys, time
import torch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import make_random
g = torch.Generator().manual_seed(0)
base = (torch.randn(2048, 6144, generator=g) * 0.02).to(torch.bfloat16)
res = {}
# fake final edits: whole tensor nudged by ~1 dtype step (hardest case: all changes near one step),
# whole tensor by ~20 steps, and 1% of entries; target = the fake edit's own measured fro norm
cases = {}
for name, amp, frac in (("full_1step", 1.2e-4, 1.0), ("full_20step", 2.4e-3, 1.0), ("1pct", 2.4e-3, 0.01)):
    m = torch.rand(base.shape, generator=g) < frac
    e = torch.where(m, (base.float() + amp * torch.randn(base.shape, generator=g)).to(torch.bfloat16), base)
    cases[name] = (e != base, float((e.double() - base.double()).norm()))
for name, (mask, target) in cases.items():
    t0 = time.time()
    new, r, info = make_random.control_tensor(base, mask, target, torch.Generator().manual_seed(1001))
    fro = float((new.double() - base.double()).norm())
    res[name] = {"k": info["k"], "n_stepped": info["n_stepped"], "n_switched": info["n_rounding_switched"],
                 "mask_equal": bool(torch.equal(new != base, mask)), "fro_rel_err": fro / target - 1,
                 "target": target, "seconds": round(time.time() - t0, 2)}
print(json.dumps(res, indent=1))
sys.exit(0 if all(v["mask_equal"] and abs(v["fro_rel_err"]) < make_random.TOL for v in res.values()) else 1)
