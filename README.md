# weight-edit-qwen

Code for a study of blind weight edits against cross-lingual language confusion in Qwen3.5-0.8B and Qwen3.5-2B.

Small multilingual chat models often answer in English when an English prompt asks for an answer in another language. We asked whether Claude Opus 5.5, acting as a blind editor, can reduce this by editing the model's weights directly: no training, no runtime hooks, one static weight diff. Five editor runs were made, four on Qwen3.5-0.8B and one on Qwen3.5-2B. The edits are compared with published training-free fixes on the Language Confusion Benchmark (LCB, Marchisio et al., arXiv:2406.20052). A later part of the study checked the frozen edits on two other cross-lingual prompt sets, on Global-MMLU, MGSM and IFEval, with greedy decoding and longer answers, and with a second blind judge (also Claude Opus 5.5). The editor found the edits; the author ran the evals and checked the numbers.

- Paper: arXiv link not yet assigned.
- Weight diffs, one repo per edit:
  - c02, Qwen3.5-0.8B: https://huggingface.co/ankit373/qwen3.5-0.8b-langconf-edit-c02
  - h5_a2_n5, Qwen3.5-0.8B: https://huggingface.co/ankit373/qwen3.5-0.8b-langconf-edit-h5
  - mix21_22b0.75_23b0.5, Qwen3.5-0.8B: https://huggingface.co/ankit373/qwen3.5-0.8b-langconf-edit-mix21
  - combo_a14_b14, Qwen3.5-0.8B: https://huggingface.co/ankit373/qwen3.5-0.8b-langconf-edit-combo
  - c06, Qwen3.5-2B: https://huggingface.co/ankit373/qwen3.5-2b-langconf-edit-c06
- Generated answers and scores: https://huggingface.co/datasets/ankit373/qwen3.5-langconf-edit-outputs

## What is in here

`scripts/` holds the scripts that made the paper's tables and figures. It mirrors the study folder: `scripts/runs/<run>/...`, `scripts/gate4-workspace/tools/`, `scripts/gate5b-workspace/tools/` and `scripts/splits/`. The scripts import each other and read data by paths relative to the study root, so run them from `scripts/`. The run folders' READMEs, with the exact commands, are not in this repo; the commands are in the queue scripts (`queue_*.sh`, `chain*.sh`).

`SCRIPTS.md` and `scripts.json` list every file with its sha256, grouped by the table it makes. 13 files differ from the study copies: an absolute path to the study folder was replaced by a relative one. Their original hashes are listed there, so you can check them against the run records.

Left out on purpose:

- `envs/`: virtual envs and lock files. Lock sha256 from the gate 4 eval: gen `0b2448356951015d48a5d195a20cbb275c91fb186efe8757c62ebfcb09a4ec7b`, score `6321065004a47aa9a480527dbb49d0c9d168e1f71d9647021652bbd20f6e3074`, score-build `8693232a813825eb0f4583f3de02bab911c428f0a055c1fa313388942fbc39ec`.
- `external/` and `data/`: the LCB clone, FLORES, the LCB paper, the third-party p50c files and the part C source sets. Get them from their own sources. `scripts/runs/2026-11-22-partc-protocol/scripts/fetch.py` and `build_sets.py` rebuild the part C sets from pinned revisions.
- Model weights, run outputs, logs and transcripts. The outputs and scores are in the dataset above.
- The editor workspaces, apart from the three tool files under `scripts/gate4-workspace/tools/` and `scripts/gate5b-workspace/tools/`.

## What you need

- Qwen/Qwen3.5-0.8B at revision `2fc06364715b967f1860aea9cf38778875588b17`, base file sha256 `04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696`.
- Qwen/Qwen3.5-2B at revision `15852e8c16360a2fea060d615a32b45270f8a8fc`, base file sha256 `aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1`. The 2B runs go through `scripts/runs/2026-11-11-gate5b-scripts/scripts/run_2b.py`, which loads the 2B in place of the 0.8B and checks that hash.
- LCB at commit `0cfdbb4a64502648938c456b2fa9689968f22298`, with `test_sets.zip` unpacked under `external/language-confusion/`.
- fastText lid.176.bin, sha256 `7e69ec5451bc261cc7844e49e4792a85d7f09c06789ec800fc4a44aec362764e`.
- Python 3.12.13, torch 2.15.0, transformers 5.22.1, numpy 2.5.4.
- We ran on an Apple M4 Pro with 24 GB, on MPS, in bf16. Other hardware is untested. Timings will differ there, and the generated text may too.

## How the tables were made

1. Generate answers with `runs/2026-11-06-gate3-scripts/scripts/generate.py`, or with a wrapper that applies a diff first (`runs/2026-11-10-gate4-eval/scripts/gen_diff.py`). Settings: temperature 0.3, top_p 0.75, top_k 20, 100 new tokens, non-thinking chat template, seed 1234 plus the prompt index.
2. Score with `runs/2026-11-05-gate1-baseline/score.py`, which imports LCB's `compute_metrics.py` unchanged, and `wrong_lang.py`.
3. Guard numbers (empty answers, loops, base-model NLL) with `runs/2026-11-06-gate3-run/scripts/guard.py`.
4. Main tables: `final_table.py` in each eval's scripts folder.
5. Statistics: `runs/2026-11-11-stats-gate4/scripts/`, `runs/2026-11-13-gate5a-summary/scripts/` and `runs/2026-11-20-stats-2b/scripts/` (per-prompt rows, cluster bootstrap, permutation tests).
6. The blind LLM judges: `runs/2026-11-11-judge/` (0.8B) and `runs/2026-11-24-judge-2b/` (2B).
7. Part C: sets from `runs/2026-11-22-partc-protocol/scripts/`, generation and scoring from `runs/2026-11-22-partc-scripts/scripts/` (`queue_c.sh` runs it all), the 0.8B side run from `runs/2026-11-22-partc-08b-side/scripts/`, figures and number tables from `runs/2026-11-24-partc-figures/scripts/run_all.sh`. The IFEval scorer is a stdlib port; its differences from the official checker are in `runs/2026-11-22-partc-scripts/DEVIATIONS.md`.

All paths in this section are under `scripts/`.

## License

Apache-2.0, see LICENSE. NOTICE lists the third-party code that is ported or quoted. LCB's `compute_metrics.py` is not copied; it is imported from the LCB clone, which is Apache-2.0.

## Citing

See CITATION.cff.
