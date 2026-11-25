"""cpu mock of the B4 ReCoVeR path: gate 3 recover_collect.py and generate.py --method recover,
unchanged, with g3common set to the 2B pin (as run_2b.py does) and load_model swapped for a tiny
random Qwen3.5 with the real vocab (gate 3 smoke_cli.py idea). no real weights, no gpu.

checks that nothing assumes a hidden size: vectors collected on a width-64 mock come out 64-d,
steering with them runs, steering a width-64 mock with width-32 vectors raises, and the vectors
sidecar names the 2B revision. usage: smoke_2b_recover.py <workdir>
"""
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts"))
sys.path.insert(0, S)
import g3common  # noqa: E402
import test_methods  # noqa: E402  (gate 3 tiny_model)

sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("run_2b_consts", os.path.join(HERE, "..", "scripts", "run_2b.py"))
src = open(spec.origin).read()
MODEL = src.split('MODEL = "')[1].split('"')[0]
REVISION = src.split('REVISION = "')[1].split('"')[0]
g3common.MODEL, g3common.REVISION = MODEL, REVISION  # what run_2b.py sets
VOCAB = 248320
WIDTH = {"w": 64}


def tiny(device, dtype):
    torch.manual_seed(0)
    cfg = test_methods.tiny_model().config
    cfg.vocab_size, cfg.hidden_size = VOCAB, WIDTH["w"]
    return type(test_methods.tiny_model())(cfg).eval().to(getattr(torch, dtype))


g3common.load_model = tiny
import generate  # noqa: E402
import recover_collect  # noqa: E402


def run(mod, argv):
    sys.argv = [mod.__name__ + ".py"] + argv
    mod.main()


work = os.path.abspath(sys.argv[1])
os.makedirs(work, exist_ok=True)
res, bad = {"model": MODEL, "revision": REVISION}, []
langs = ("eng_Latn,arb_Arab,deu_Latn,spa_Latn,fra_Latn,hin_Deva,ind_Latn,ita_Latn,jpn_Jpan,kor_Hang,"
         "por_Latn,rus_Cyrl,tur_Latn,vie_Latn,zho_Hans,eus_Latn,swh_Latn,tha_Thai,pes_Arab")
flores = os.path.join(HERE, "..", "..", "..", "external", "flores200", "extracted", "flores200_dataset", "dev")
for w in (32, 64):
    WIDTH["w"] = w
    out = os.path.join(work, f"vectors_w{w}.safetensors")
    for p in (out, out + ".json"):
        if os.path.exists(p):
            os.remove(p)
    run(recover_collect, ["--flores-dir", flores, "--langs", langs, "--out", out, "--device", "cpu",
                          "--dtype", "float32", "--limit", "2"])
    from safetensors.torch import load_file
    v = load_file(out)
    meta = json.load(open(out + ".json"))
    res[f"w{w}"] = {"eng_shape": list(v["eng_Latn"].shape), "meta_model_revision": meta["model_revision"]}
    if list(v["eng_Latn"].shape) != [5, w] or meta["model_revision"] != REVISION:
        bad.append(f"vectors w{w}")

ids = os.path.join(work, "ids.txt")
open(ids, "w").write("crosslingual/complex_prompts/de/2\ncrosslingual/okapi/ja/0\nmonolingual/okapi/fr/0\n")
WIDTH["w"] = 64
common = ["--ids", ids, "--device", "cpu", "--dtype", "float32"]
for name, vec in (("ok_w64", "vectors_w64.safetensors"), ("mismatch_w32_on_w64", "vectors_w32.safetensors")):
    out = os.path.join(work, f"recover_{name}.jsonl")
    if os.path.exists(out):
        os.remove(out)
    try:
        run(generate, common + ["--out", out, "--method", "recover", "--vectors", os.path.join(work, vec),
                                "--alpha", "0.05", "--restore-norm"])
        rows = [json.loads(l) for l in open(out)]
        res[name] = {"ran": True, "rows": len(rows)}
    except Exception as e:  # noqa: BLE001
        res[name] = {"ran": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}
if not (res["ok_w64"]["ran"] and res["ok_w64"]["rows"] == 3):
    bad.append("w64 steering did not run")
if res["mismatch_w32_on_w64"]["ran"]:
    bad.append("width mismatch did not raise")
res["failed"] = bad
print(json.dumps(res, indent=1))
sys.exit(1 if bad else 0)
