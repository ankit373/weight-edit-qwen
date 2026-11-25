#!/bin/sh
# queue C (eval step 2): random-edit controls, 3 seeds, dev + test, guard NLL.
set -f
. runs/2026-11-10-gate4-eval/scripts/qlib.sh
for s in 1001 1002 1003; do
  D=$R/diffs/rand_s$s
  DS=$($SB $G -I -B -c "import json;print(json.load(open('$D/manifest.json'))['diff_file_sha256'])")
  GD="$SB $G -I -B $R/scripts/gen_diff.py --entry generate --diff $D --expect-diff-sha $DS"
  step rand_s${s}_dev $R/outputs/rand_s${s}_dev.jsonl $GD --ids splits/dev.txt --out $R/outputs/rand_s${s}_dev.jsonl --method none
  step rand_s${s}_test $R/outputs/rand_s${s}_test.jsonl $GD --ids splits/test.txt --out $R/outputs/rand_s${s}_test.jsonl --method none
  step nll_rand_s${s}_dev $R/guard/rand_s${s}_dev.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/rand_s${s}_dev.jsonl $G3/outputs/baseline_dev.jsonl $R/guard/rand_s${s}_dev.nll.jsonl
  step nll_rand_s${s}_test $R/guard/rand_s${s}_test.nll.jsonl $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/rand_s${s}_test.jsonl $G3/outputs/baseline_test.jsonl $R/guard/rand_s${s}_test.nll.jsonl
done
echo "QUEUE_C DONE $(date -u +%FT%TZ)" >> $R/logs/steps.log
