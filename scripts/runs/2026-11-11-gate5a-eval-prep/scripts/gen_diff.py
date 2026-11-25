"""gate 3 generate.py, unchanged, with a part A weight diff applied in memory after the base load.
copy of gate 4 eval gen_diff.py: only TOOLS changed (now --tools, the editor's own tools folder)
and the mmlu entry dropped (part A has no mmlu). only g3common.load_model is swapped.

usage: gen_diff.py --tools <workspace>/tools --diff DIR --expect-diff-sha SHA <generate.py args>

the diff is applied by <workspace>/tools/apply_diff.py (checks base file sha256, diff file sha256,
per-tensor base sha256 before and edited sha256 after; exits on any mismatch).
--expect-diff-sha: the diff file sha256 this run must use (refuse on mismatch).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.abspath(os.path.join(HERE, "..", ".."))
S = os.path.join(RUNS, "2026-11-06-gate3-scripts", "scripts")


def pop_arg(name):
    if name not in sys.argv:
        sys.exit(f"missing {name}. refused.")
    i = sys.argv.index(name)
    val = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    return val


TOOLS = os.path.abspath(pop_arg("--tools"))
DIFF = os.path.abspath(pop_arg("--diff"))
WANT = pop_arg("--expect-diff-sha")
with open(os.path.join(DIFF, "manifest.json")) as f:
    if json.load(f)["diff_file_sha256"] != WANT:
        sys.exit("manifest diff_file_sha256 is not the expected one. refused.")

sys.path.insert(0, S)
import g3common  # noqa: E402
import generate  # noqa: E402  (gate 3 generate.py; imported before the tools dir is on the path)

sys.path.insert(1, TOOLS)
import apply_diff  # noqa: E402  (puts TOOLS first on sys.path; it has its own generate.py)

sys.path[:] = [p for p in sys.path if os.path.abspath(p) != TOOLS]
assert os.path.dirname(os.path.abspath(generate.__file__)) == S, generate.__file__
assert os.path.dirname(os.path.abspath(apply_diff.__file__)) == TOOLS, apply_diff.__file__
# the base load (g3common, gate 1 pin) and the diff tools must name the same model
assert (g3common.MODEL, g3common.REVISION) == (apply_diff.common.MODEL, apply_diff.common.REVISION), \
    (g3common.MODEL, apply_diff.common.MODEL)

_base_load = g3common.load_model


def load_model(device, dtype):
    model = _base_load(device, dtype)
    man = apply_diff.apply_diff(model, DIFF)  # exits on any hash mismatch
    print(json.dumps({"diff": DIFF, "diff_file_sha256": man["diff_file_sha256"], "applied": True,
                      "tools": TOOLS,
                      "tensors": {n: [i["base_sha256"], i["edited_sha256"], i["n_changed"],
                                      i["delta_fro"]] for n, i in man["tensors"].items()}}),
          flush=True)
    return model


g3common.load_model = load_model

if __name__ == "__main__":
    sys.argv[0] = os.path.join(S, "generate.py")
    generate.main()
