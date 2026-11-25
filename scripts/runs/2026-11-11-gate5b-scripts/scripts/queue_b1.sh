#!/bin/sh
# B1 (part B plan): gate 1 baseline on Qwen3.5-2B. run from the project root. run folder:
# runs/<utc date of the first B1 step>-gate5b-baseline (made by the timing stage, found again later).
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b1.sh timing   # D1: 10 prompts, the only gpu use before part A ends
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b1.sh full     # D11: only after all of part A
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b1.sh all      # timing, then full
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
stage=${1:-}
case "$stage" in timing|full|all) ;; *) echo "usage: queue_b1.sh timing|full|all" >&2; exit 2;; esac
R=$(find_run baseline new) || exit 1
mkdir -p $R/outputs $R/logs $R/scores $R/guard $R/env
log "QUEUE_B1 $stage start R=$R"

timing() {
  step timing10 $R/outputs/timing10.jsonl 10 $RUN $S/generate.py --ids $G1/ids/timing10.txt --out $R/outputs/timing10.jsonl --method none
  cpu timing10_summary $SB $G -I -B $X/timing_summary.py $R/outputs/timing10.jsonl $G1/outputs/full_nonthinking.jsonl $R/scores/timing10.json
}

full() {
  # step 1: real load check (gate 1 env_check.py, 2B constants) and 20-prompt determinism
  step env_check - - $SB $G -I -B $X/env_check_2b.py
  step repro20_a $R/outputs/repro20_a.jsonl 20 $RUN $S/generate.py --ids $G3/ids/repro20_dev.txt --out $R/outputs/repro20_a.jsonl --method none
  step repro20_b $R/outputs/repro20_b.jsonl 20 $RUN $S/generate.py --ids $G3/ids/repro20_dev.txt --out $R/outputs/repro20_b.jsonl --method none
  cpu repro20_compare $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/repro20_a.jsonl $R/outputs/repro20_b.jsonl $R/scores/repro20_compare.json
  $G -I -B -c "import json,sys; r=json.load(open('$R/scores/repro20_compare.json')); sys.exit(0 if r['identical']==r['n']==20 else 1)" \
    || { log "HALT queue: repro20 runs are not byte-identical"; exit 10; }
  # step 3: all 6586 prompts, gate 1 settings (generate.py = gate 1 loop, gate 3 step 0)
  step full $R/outputs/full_nonthinking.jsonl 6586 $RUN $S/generate.py --ids $G1/ids/all.txt --out $R/outputs/full_nonthinking.jsonl --method none
  cpu repro20_vs_full $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/repro20_a.jsonl $R/outputs/full_nonthinking.jsonl $R/scores/repro20_vs_full.json
  cpu subset_dev $SB $G -I -B $S/subset.py $R/outputs/full_nonthinking.jsonl splits/dev.txt $R/outputs/baseline_dev.jsonl
  cpu subset_test $SB $G -I -B $S/subset.py $R/outputs/full_nonthinking.jsonl splits/test.txt $R/outputs/baseline_test.jsonl
  cpu subset_mono $SB $G -I -B $S/subset.py $R/outputs/full_nonthinking.jsonl $G3/ids/mono_all.txt $R/outputs/baseline_mono.jsonl
  cpu subset_devcx $SB $G -I -B $S/subset.py $R/outputs/full_nonthinking.jsonl $G3/ids/dev_complex.txt $R/outputs/baseline_devcx.jsonl
  # step 4: guard reference, base-model NLL of the 2B rows (unedited 2B, no hook)
  step nll_baseline_dev $R/guard/baseline_dev.nll.jsonl 2086 $RUN $G3/scripts/guard.py nll $R/outputs/baseline_dev.jsonl $R/outputs/baseline_dev.jsonl $R/guard/baseline_dev.nll.jsonl
  step nll_baseline_test $R/guard/baseline_test.nll.jsonl 2100 $RUN $G3/scripts/guard.py nll $R/outputs/baseline_test.jsonl $R/outputs/baseline_test.jsonl $R/guard/baseline_test.nll.jsonl
  # scoring (cpu, score env): gate 1 score.py + wrong_lang.py unchanged
  for n in full_nonthinking baseline_dev baseline_test baseline_mono; do
    cpu score_$n sh $X/score.sh $R/outputs/$n.jsonl $R/scores/$n
  done
  cpu table $RUN $X/final_table.py $R/scores/table_b1.json \
    dev=$R/outputs/baseline_dev.jsonl=$R/scores/baseline_dev test=$R/outputs/baseline_test.jsonl=$R/scores/baseline_test
  cpu loops_devcx $RUN $G3/scripts/loop_count.py $R/outputs/baseline_dev.jsonl $G3/ids/dev_complex.txt
  # step 5 (D12): dev cross complex LPR >= 90 -> part B stops after B1. logged, not acted on here
  $G -I -B -c "import json; t=json.load(open('$R/scores/table_b1.json')); x=t['dev']['complex']['lpr']; print('D12 dev cross complex LPR', x, 'STOP part B' if x >= 90 else 'continue part B')" >> $R/logs/steps.log
}

case "$stage" in
  timing) timing ;;
  full) full ;;
  all) timing; full ;;
esac
log "QUEUE_B1 $stage DONE"
