#!/bin/sh
# resume after the 05:34Z pause: rest of queue C (seed 1003), then queue D. run under caffeinate -i -d -m -s.
set -f
. runs/2026-11-10-gate4-eval/scripts/qlib.sh
s=1003; D=$R/diffs/rand_s$s
DS=f3f8d3f823bfdcf65faaa89b52630fff1db02fd4bbec2eb65022073c108885fa
GD="$SB $G -I -B $R/scripts/gen_diff.py --entry generate --diff $D --expect-diff-sha $DS"
echo "RESUME_QUEUE start $(date -u +%FT%TZ)" >> $R/logs/steps.log
step rand_s${s}_dev $R/outputs/rand_s${s}_dev.jsonl $GD --ids splits/dev.txt --out $R/outputs/rand_s${s}_dev.jsonl --method none
step rand_s${s}_test $R/outputs/rand_s${s}_test.jsonl $GD --ids splits/test.txt --out $R/outputs/rand_s${s}_test.jsonl --method none
step nll_rand_s${s}_dev $R/guard/rand_s${s}_dev.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/rand_s${s}_dev.jsonl $G3/outputs/baseline_dev.jsonl $R/guard/rand_s${s}_dev.nll.jsonl
step nll_rand_s${s}_test $R/guard/rand_s${s}_test.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/rand_s${s}_test.jsonl $G3/outputs/baseline_test.jsonl $R/guard/rand_s${s}_test.nll.jsonl
echo "QUEUE_C DONE $(date -u +%FT%TZ)" >> $R/logs/steps.log
sh $R/scripts/queue_d.sh
