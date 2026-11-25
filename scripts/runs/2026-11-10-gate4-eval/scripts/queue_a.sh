#!/bin/sh
# queue A (eval steps 1 + 3): reproduction check, final edit on test, guard NLL test + dev.
set -f
. runs/2026-11-10-gate4-eval/scripts/qlib.sh
GD="$SB $G -I -B $R/scripts/gen_diff.py --entry generate --diff $FINAL --expect-diff-sha $FSHA"
step repro20_final $R/outputs/repro20_final_dev.jsonl $GD --ids $G3/ids/repro20_dev.txt --out $R/outputs/repro20_final_dev.jsonl --method none
step final_test $R/outputs/final_test.jsonl $GD --ids splits/test.txt --out $R/outputs/final_test.jsonl --method none
step nll_final_test $R/guard/final_test.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/final_test.jsonl $G3/outputs/baseline_test.jsonl $R/guard/final_test.nll.jsonl
step nll_final_dev $R/guard/final_dev.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll gate4-workspace/work/c02_nb_L15u1047_k2/dev.jsonl $G3/outputs/baseline_dev.jsonl $R/guard/final_dev.nll.jsonl
echo "QUEUE_A DONE $(date -u +%FT%TZ)" >> $R/logs/steps.log
