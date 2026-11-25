"""run a gate 3 / gate 4 eval / mmlu script, unchanged, on Qwen/Qwen3.5-2B (part B plan, "scripts").

usage: run_2b.py [--mock-load] <target.py> [target args ...]

sets g3common.MODEL / REVISION to the 2B pin, then runs the target as __main__ (runpy).
g3common.load_model / load_tokenizer read those globals at call time. before the first model
load, the cached weights file is checked against the setup sha256. after the load, the config
widths are checked and one json meta line naming the 2B revision is printed.
--mock-load: stop with exit 0 at the first model load (cpu dry run: imports, paths, args).
"""
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.abspath(os.path.join(HERE, "..", ".."))
S = os.path.join(RUNS, "2026-11-06-gate3-scripts", "scripts")

# runs/2026-11-11-gate5b-setup/README.md "model" + model/sha256_files.txt
MODEL = "Qwen/Qwen3.5-2B"
REVISION = "15852e8c16360a2fea060d615a32b45270f8a8fc"
WEIGHTS_FILE = "model.safetensors-00001-of-00001.safetensors"
WEIGHTS_SHA256 = "aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1"
EXPECT = {"hidden_size": 2048, "intermediate_size": 6144, "num_hidden_layers": 24}  # config_2b.json
N_PARAMS = 1881825088  # text model params, setup env/cpu_check.json (meta build)

mock = len(sys.argv) > 1 and sys.argv[1] == "--mock-load"
if mock:
    del sys.argv[1]
if len(sys.argv) < 2:
    sys.exit(__doc__)
target = os.path.abspath(sys.argv[1])

sys.path.insert(0, S)
import g3common  # noqa: E402

g3common.MODEL, g3common.REVISION = MODEL, REVISION
_load_model = g3common.load_model
_checked = []


def check_weights():
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(MODEL, WEIGHTS_FILE, revision=REVISION, local_files_only=True)
    got = g3common.file_sha256(path)
    if got != WEIGHTS_SHA256:
        sys.exit(f"run_2b: weights sha256 mismatch {got}")
    _checked.append(got)


def load_model(device, dtype):
    if mock:
        print(json.dumps({"run_2b_mock": "stop before weight load", "device": device,
                          "dtype": dtype, "model": g3common.MODEL,
                          "revision": g3common.REVISION}), flush=True)
        sys.exit(0)
    if not _checked:
        check_weights()
    model = _load_model(device, dtype)
    cfg = model.config
    got = {k: getattr(cfg, k) for k in EXPECT}
    n_params = sum(p.numel() for p in model.parameters())
    if got != EXPECT or n_params != N_PARAMS:
        sys.exit(f"run_2b: config {got} / {n_params} params is not the 2B text model {EXPECT} / {N_PARAMS}")
    print(json.dumps({"run_2b": {"model": g3common.MODEL, "revision": g3common.REVISION,
                                 "weights_sha256": _checked[0], "config": got, "n_params": n_params,
                                 "device": device, "dtype": dtype}}), flush=True)
    return model


g3common.load_model = load_model
print(json.dumps({"run_2b_start": {"model": MODEL, "revision": REVISION, "target": target,
                                   "argv": sys.argv[2:], "mock_load": mock}}), flush=True)
sys.argv = [target] + sys.argv[2:]
# as `python -I target.py` would set it; this folder and S leave the path (targets add S themselves)
sys.path[:] = [os.path.dirname(target)] + [p for p in sys.path if p not in (S, HERE)]
runpy.run_path(target, run_name="__main__")
