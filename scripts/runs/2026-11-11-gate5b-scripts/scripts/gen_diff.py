"""gate 3 generate.py (or mmlu-redux mmlu_gen.py), unchanged, with a gate 4 weight diff applied
in memory after the base load. only g3common.load_model is swapped.

usage: run_2b.py gen_diff.py --entry generate|mmlu --diff DIR --expect-diff-sha SHA <generate.py or mmlu_gen.py args>
part B copy: TOOLS points at gate5b-workspace/tools (2B common.py); run it through run_2b.py.

the diff is applied by gate5b-workspace/tools/apply_diff.py (checks base file sha256, diff file
sha256, per-tensor base sha256 before and edited sha256 after; exits on any mismatch).
--expect-diff-sha: the diff file sha256 this run must use (refuse on mismatch).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.abspath(os.path.join(HERE, "..", ".."))
S = os.path.join(RUNS, "2026-11-06-gate3-scripts", "scripts")
MMLU = os.path.join(RUNS, "2026-11-08-side-mmlu-redux", "scripts")
TOOLS = os.path.abspath(os.path.join(RUNS, "..", "gate5b-workspace", "tools"))
sys.path.insert(0, S)
import g3common  # noqa: E402
import generate  # noqa: E402  (gate 3 generate.py; imported before the gate 4 tools dir is on the path)

sys.path.insert(1, TOOLS)
import apply_diff  # noqa: E402  (puts TOOLS first on sys.path; it has its own generate.py)

sys.path[:] = [p for p in sys.path if os.path.abspath(p) != TOOLS]
# part B: the base load (g3common, set by run_2b.py) and the diff tools must name the same model
assert (g3common.MODEL, g3common.REVISION) == (apply_diff.common.MODEL, apply_diff.common.REVISION), \
    (g3common.MODEL, apply_diff.common.MODEL)
assert os.path.dirname(os.path.abspath(generate.__file__)) == S, generate.__file__


def pop_arg(name):
    i = sys.argv.index(name)
    val = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    return val


ENTRY = pop_arg("--entry")
DIFF = os.path.abspath(pop_arg("--diff"))
WANT = pop_arg("--expect-diff-sha")
assert ENTRY in ("generate", "mmlu"), ENTRY
with open(os.path.join(DIFF, "manifest.json")) as f:
    if json.load(f)["diff_file_sha256"] != WANT:
        sys.exit("manifest diff_file_sha256 is not the expected one. refused.")

_base_load = g3common.load_model


def load_model(device, dtype):
    model = _base_load(device, dtype)
    man = apply_diff.apply_diff(model, DIFF)  # exits on any hash mismatch
    print(json.dumps({"diff": DIFF, "diff_file_sha256": man["diff_file_sha256"], "applied": True,
                      "tensors": {n: [i["base_sha256"], i["edited_sha256"], i["n_changed"],
                                      i["delta_fro"]] for n, i in man["tensors"].items()}}),
          flush=True)
    return model


g3common.load_model = load_model

if __name__ == "__main__":
    if ENTRY == "generate":
        sys.argv[0] = os.path.join(S, "generate.py")
        generate.main()
    else:
        sys.path.insert(0, MMLU)
        import mmlu_gen  # noqa: E402
        sys.argv[0] = os.path.join(MMLU, "mmlu_gen.py")
        mmlu_gen.main()
