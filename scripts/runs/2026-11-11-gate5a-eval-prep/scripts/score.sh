#!/bin/sh
# gate 3 score_run.sh with -B added (no .pyc). gate 1 score.py + wrong_lang.py unchanged. run from the project root.
# usage: score.sh <rows.jsonl> <out_prefix>
set -eu
G1=runs/2026-11-05-gate1-baseline
envs/run-sandboxed.sh envs/score/bin/python -I -B $G1/score.py "$1" "$2" > "$2.score.log" 2>&1
envs/run-sandboxed.sh envs/score/bin/python -I -B $G1/wrong_lang.py "$1" "$2_wrong_lang.json" >> "$2.score.log" 2>&1
awk -F"\t" '$3=="all" && ($2=="all"||$2=="complex_prompts"||$2=="okapi"||$2=="sharegpt"||$2=="aya"||$2=="dolly"||$2=="native")' "$2.tsv"
