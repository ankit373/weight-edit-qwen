#!/bin/sh
# B3 (part B plan): instruction at the end on the 2B. gate 3 prompts/instr_end.jsonl unchanged.
# only the changed prompts are generated (dev 1288, test 1316); unchanged ones reuse B1 rows
# (same prompt, same seed). guard on dev. test is scored once. run from the project root.
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b3.sh
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
B1=$(find_run baseline) || exit 1
R=$(find_run instr-end new) || exit 1
mkdir -p $R/outputs $R/logs $R/scores $R/guard
GV="$RUN $G3/scripts/gen_variant.py --variants $G3/prompts/instr_end.jsonl --kind instr_end"
log "QUEUE_B3 start R=$R B1=$B1"
step instr_end_dev_changed $R/outputs/instr_end_dev_changed.jsonl 1288 $GV --ids $G3/ids/instr_end_changed_dev.txt --out $R/outputs/instr_end_dev_changed.jsonl --method none
step instr_end_test_changed $R/outputs/instr_end_test_changed.jsonl 1316 $GV --ids $G3/ids/instr_end_changed_test.txt --out $R/outputs/instr_end_test_changed.jsonl --method none
cpu merge_dev $SB $G -I -B $G3/scripts/merge_instr_end.py $R/outputs/instr_end_dev_changed.jsonl $B1/outputs/baseline_dev.jsonl splits/dev.txt $R/outputs/instr_end_dev.jsonl
cpu merge_test $SB $G -I -B $G3/scripts/merge_instr_end.py $R/outputs/instr_end_test_changed.jsonl $B1/outputs/baseline_test.jsonl splits/test.txt $R/outputs/instr_end_test.jsonl
# guard reference = B1 2B rows and B1 2B base-model NLL (plan "settings")
step nll_instr_end_dev $R/guard/instr_end_dev.nll.jsonl 2086 $RUN $G3/scripts/guard.py nll $R/outputs/instr_end_dev.jsonl $B1/outputs/baseline_dev.jsonl $R/guard/instr_end_dev.nll.jsonl
cpu guard_dev $RUN $G3/scripts/guard.py summary $R/outputs/instr_end_dev.jsonl $R/guard/instr_end_dev.nll.jsonl $B1/outputs/baseline_dev.jsonl $B1/guard/baseline_dev.nll.jsonl splits/dev.txt $R/guard/instr_end_dev.guard.json
cpu score_dev sh $X/score.sh $R/outputs/instr_end_dev.jsonl $R/scores/instr_end_dev
cpu score_test sh $X/score.sh $R/outputs/instr_end_test.jsonl $R/scores/instr_end_test
log "QUEUE_B3 DONE"
