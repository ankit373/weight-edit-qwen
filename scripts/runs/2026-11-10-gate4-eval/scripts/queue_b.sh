#!/bin/sh
# queue B (eval step 4): final edit on the 2400 monolingual prompts and on mmlu-redux (5330).
set -f
. runs/2026-11-10-gate4-eval/scripts/qlib.sh
GD="$SB $G -I -B $R/scripts/gen_diff.py --diff $FINAL --expect-diff-sha $FSHA"
step final_mono $R/outputs/final_mono.jsonl $GD --entry generate --ids $G3/ids/mono_all.txt --out $R/outputs/final_mono.jsonl --method none
step final_mmlu $R/outputs/final_mmlu.jsonl $GD --entry mmlu --items $MM/data/items_ok.jsonl --ids $MM/ids/all_ok.txt --out $R/outputs/final_mmlu.jsonl --method none
echo "QUEUE_B DONE $(date -u +%FT%TZ)" >> $R/logs/steps.log
