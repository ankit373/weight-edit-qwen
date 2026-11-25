#!/bin/sh
# cpu: c06 dev guard summary, left out of queue_b6 score stage (open question 56). same call as the rand_*_dev guards.
cd "$(dirname "$0")/../.." || exit 1
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
B1=$(find_run baseline) || exit 1
R=runs/2026-11-17-gate5b-eval
EDEV=gate5b-workspace/work/c06/dev.jsonl
$RUN $G3/scripts/guard.py summary $EDEV $R/guard/final_dev.nll.jsonl $B1/outputs/baseline_dev.jsonl $B1/guard/baseline_dev.nll.jsonl splits/dev.txt $R/guard/final_dev.guard.json
