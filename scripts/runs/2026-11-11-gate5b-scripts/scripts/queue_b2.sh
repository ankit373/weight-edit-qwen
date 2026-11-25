#!/bin/sh
# B2 (part B plan): gate 2-style failure breakdown on the 2B, dev only. run from the project root.
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b2.sh cpu    # step 1 + token labels, from B1 outputs
#   sh runs/2026-11-11-gate5b-scripts/scripts/queue_b2.sh lens   # step 2 logit lens (gpu, D3), then its summaries
# gate 2 scripts run unchanged from their folder, except the 3 with the model pin (copies in gate2/).
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
stage=${1:-}
case "$stage" in cpu|lens) ;; *) echo "usage: queue_b2.sh cpu|lens" >&2; exit 2;; esac
B1=$(find_run baseline) || exit 1
R=$(find_run diagnosis new) || exit 1
mkdir -p $R/outputs $R/logs $R/scores $R/token_labels
D=splits/dev.txt; FULL=$B1/outputs/full_nonthinking.jsonl; DEVROWS=$B1/outputs/baseline_dev.jsonl
log "QUEUE_B2 $stage start R=$R B1=$B1"

if [ "$stage" = cpu ]; then
  cpu step1_behaviour $SB $P -I -B $G2/step1_behaviour.py $FULL $D $R/outputs/step1_dev_behaviour.jsonl
  cpu step1_summary $SB $G -I -B $X/gate2/step1_summary.py $R/outputs/step1_dev_behaviour.jsonl $R/scores/step1_summary.json
  cpu step1_paired $SB $G -I -B $G2/step1_paired.py $R/outputs/step1_dev_behaviour.jsonl $R/scores/step1_paired.json
  cpu step1_position $SB $G -I -B $G2/step1_position.py $R/outputs/step1_dev_behaviour.jsonl $R/scores/step1_position.json
  cpu step1_extra $SB $G -I -B $G2/step1_extra.py $R/outputs/step1_dev_behaviour.jsonl $DEVROWS $R/scores/step1_extra.json
  cpu eyeball1 sh -c "$SB $G -I -B $G2/eyeball.py $R/outputs/step1_dev_behaviour.jsonl $DEVROWS 1 > $R/logs/eyeball_sample1.txt"
  cpu eyeball2 sh -c "$SB $G -I -B $G2/eyeball.py $R/outputs/step1_dev_behaviour.jsonl $DEVROWS 2 > $R/logs/eyeball_sample2.txt"
  # contrast sets come from the 2B monolingual outputs (plan B2 step 2)
  cpu token_labels $SB $G -I -B $X/gate2/step2_token_labels.py $FULL $R/token_labels
else
  [ -f $R/token_labels/token_labels.json ] || { log "HALT queue: run the cpu stage first"; exit 2; }
  step lens $R/outputs/step2_lens_dev.jsonl 2086 $SB $G -I -B $X/gate2/step2_lens.py --ids $D --gate1 $DEVROWS \
    --beh $R/outputs/step1_dev_behaviour.jsonl --labels $R/token_labels --out $R/outputs/step2_lens_dev.jsonl
  cpu step2_summary $SB $G -I -B $G2/step2_summary.py $R/outputs/step2_lens_dev.jsonl $R/token_labels $R/scores
  cpu step2_layers $SB $G -I -B $G2/step2_layers.py $R/scores/step2_summary.json $R/scores/step2_layers_nonlatin.tsv
  cpu step2_tokens $SB $G -I -B $G2/step2_tokens.py $R/outputs/step2_lens_dev.jsonl $R/scores/step2_tokens.json
fi
log "QUEUE_B2 $stage DONE"
