"""part C generation wrapper. runs an existing entry script unchanged, with four patches only:

usage: [run_2b.py] partc_gen.py --entry generate|recover|variant|gmmlu [options] <entry args>
  --rows FILE             prompts come from FILE (id/task/source/language/prompt rows), in file
                          order, so the seed is 1234 + the row's index in FILE (PROTOCOL.md sec 1).
                          replaces g3common.load_prompts, as gen_variant.py does for LCB variants.
  --max-new-tokens N      default token cap of g3common.gen_kwargs (100 if not given)
  --diff DIR --expect-diff-sha SHA
                          frozen diff applied after the base load by the existing gen_diff.py
                          (0.8B: gate 4 eval copy, 2B: gate 5b copy, picked by g3common.MODEL)
  --mock-load             stop with exit 0 at the first model load (cpu dry run)
  --mock-tiny             tiny random Qwen3_5 model (hidden 64, 4 layers, real tokenizer), cpu tests
entries: generate = gate 3 generate.py; recover = gate 3 run gen_recover_dev.py (ReCoVeR);
variant = gate 3 run gen_variant.py (LCB instruction at end); gmmlu = gmmlu_logit.py.
every row also gets a line {id, n_layer_hooks} in <out>.hooks.jsonl: forward hooks on the decoder
layers right after the method's before(row) (input to the ReCoVeR no-op check).
"""
import importlib.util
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.abspath(os.path.join(HERE, "..", ".."))
S = os.path.join(RUNS, "2026-11-06-gate3-scripts", "scripts")
G3 = os.path.join(RUNS, "2026-11-06-gate3-run", "scripts")
GEN_DIFF = {"Qwen/Qwen3.5-0.8B": os.path.join(RUNS, "2026-11-10-gate4-eval", "scripts", "gen_diff.py"),
            "Qwen/Qwen3.5-2B": os.path.join(RUNS, "2026-11-11-gate5b-scripts", "scripts", "gen_diff.py")}
ENTRIES = {"generate": os.path.join(S, "generate.py"), "recover": os.path.join(G3, "gen_recover_dev.py"),
           "variant": os.path.join(G3, "gen_variant.py"), "gmmlu": os.path.join(HERE, "gmmlu_logit.py")}
ROW_KEYS = ("id", "task", "source", "language", "prompt")


def pop(argv, name, has_value=True):
    if name not in argv:
        return None
    i = argv.index(name)
    if not has_value:
        del argv[i]
        return True
    val = argv[i + 1]
    del argv[i:i + 2]
    return val


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for r in rows:
        missing = [k for k in ROW_KEYS if k not in r]
        if missing:
            sys.exit(f"partc_gen: row {r.get('id')} lacks {missing}")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit("partc_gen: duplicate ids in --rows file")
    return rows


def tiny_model(device, dtype):
    """random tiny model with the real config family; no checkpoint is read."""
    import torch
    from transformers import AutoConfig, Qwen3_5ForCausalLM
    import g3common
    cfg = AutoConfig.from_pretrained(g3common.MODEL, revision=g3common.REVISION,
                                     trust_remote_code=False).text_config
    small = dict(hidden_size=64, intermediate_size=128, num_hidden_layers=4, num_attention_heads=2,
                 num_key_value_heads=1, head_dim=32, linear_num_key_heads=2, linear_num_value_heads=2,
                 linear_key_head_dim=16, linear_value_head_dim=16,
                 layer_types=["linear_attention"] * 3 + ["full_attention"])
    for k, v in small.items():
        setattr(cfg, k, v)
    torch.manual_seed(0)
    model = Qwen3_5ForCausalLM(cfg).to(getattr(torch, dtype))
    print(json.dumps({"partc_gen_mock_tiny": small, "device": device, "dtype": dtype}), flush=True)
    return model.to(device).eval()


def main():
    argv = sys.argv[1:]
    entry = pop(argv, "--entry")
    rows_path = pop(argv, "--rows")
    cap = pop(argv, "--max-new-tokens")
    diff = pop(argv, "--diff")
    want_sha = pop(argv, "--expect-diff-sha")
    mock_load = pop(argv, "--mock-load", has_value=False)
    mock_tiny = pop(argv, "--mock-tiny", has_value=False)
    if entry not in ENTRIES:
        sys.exit(__doc__)
    if bool(diff) != bool(want_sha):
        sys.exit("partc_gen: --diff and --expect-diff-sha go together")
    if rows_path and entry == "variant":
        sys.exit("partc_gen: --rows is for new row files; variant reads LCB rows")

    sys.path.insert(0, S)
    import g3common  # noqa: E402  (same module object run_2b.py patched, if run under it)
    import generate  # noqa: E402  (imported before gen_diff, which checks it came from S)

    if rows_path:
        rows = load_rows(rows_path)
        g3common.load_prompts = lambda: [dict(r) for r in rows]
    if cap:
        base_kw = g3common.gen_kwargs

        def gen_kwargs(tok, greedy, max_new_tokens=int(cap)):
            return base_kw(tok, greedy, max_new_tokens)
        g3common.gen_kwargs = gen_kwargs
    if mock_load:
        def stop_load(device, dtype):
            print(json.dumps({"partc_gen_mock": "stop before weight load", "model": g3common.MODEL,
                              "revision": g3common.REVISION, "device": device}), flush=True)
            sys.exit(0)
        g3common.load_model = stop_load
    if mock_tiny:
        g3common.load_model = tiny_model

    out = argv[argv.index("--out") + 1]
    hooks_path = out + ".hooks.jsonl"
    base_build = generate.build_method

    def build_method(model, args):
        m = base_build(model, args)
        before = m.before

        def logged_before(row):
            before(row)
            n = sum(len(layer._forward_hooks) for layer in model.model.layers)
            with open(hooks_path, "a") as f:
                f.write(json.dumps({"id": row.get("id"), "n_layer_hooks": n}) + "\n")
        m.before = logged_before
        return m
    generate.build_method = build_method

    meta = {"partc_gen": {"entry": entry, "model": g3common.MODEL, "revision": g3common.REVISION,
                          "rows": rows_path, "rows_sha256": g3common.file_sha256(rows_path) if rows_path else None,
                          "max_new_tokens": int(cap) if cap else None, "diff": diff,
                          "expect_diff_sha": want_sha, "mock_load": bool(mock_load),
                          "mock_tiny": bool(mock_tiny), "argv": argv}}
    print(json.dumps(meta), flush=True)

    if diff:
        gd = GEN_DIFF[g3common.MODEL]
        saved = sys.argv
        sys.argv = [gd, "--entry", "generate", "--diff", diff, "--expect-diff-sha", want_sha]
        spec = importlib.util.spec_from_file_location("partc_gen_diff", gd)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # refuses on a manifest sha mismatch; wraps g3common.load_model
        sys.argv = saved

    target = ENTRIES[entry]
    sys.argv = [target] + argv
    if entry == "generate":
        generate.main()
    elif entry == "gmmlu":
        sys.path.insert(0, HERE)
        import gmmlu_logit  # noqa: E402
        gmmlu_logit.main()
    else:
        runpy.run_path(target, run_name="__main__")


if __name__ == "__main__":
    main()
