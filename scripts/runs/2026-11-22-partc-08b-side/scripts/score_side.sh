#!/bin/sh
# cpu scoring, as gate 4 eval scored c02 (README "exact commands"). run from the project root after queue_side.sh.
set -eu
R=runs/2026-11-22-partc-08b-side; G4=runs/2026-11-10-gate4-eval; G3=runs/2026-11-06-gate3-run
MM=runs/2026-11-08-side-mmlu-redux; SB=envs/run-sandboxed.sh; G=envs/gen/bin/python
E="h5_a2_n5 mix21_22b0.75_23b0.5 combo_a14_b14"
for en in $E; do sh $G4/scripts/score.sh $R/outputs/${en}_mono.jsonl $R/scores/${en}_mono; done
# mono loops (guard unit), gate 3 loop_count.py: gate 1, c02, the three edits
{
  echo "base $($SB $G -I -B $G3/scripts/loop_count.py $G3/outputs/baseline_mono.jsonl $G3/ids/mono_all.txt | tail -1)"
  echo "c02 $($SB $G -I -B $G3/scripts/loop_count.py $G4/outputs/final_mono.jsonl $G3/ids/mono_all.txt | tail -1)"
  for en in $E; do
    echo "$en $($SB $G -I -B $G3/scripts/loop_count.py $R/outputs/${en}_mono.jsonl $G3/ids/mono_all.txt | tail -1)"
  done
} > $R/scores/mono_loops.txt 2> $R/logs/mono_loops.err
# mmlu: paired vs the side-check base, c02 + the three edits in one run of score_mmlu.py
$SB $G -I -B $MM/scripts/score_mmlu.py $MM/data/items_ok.jsonl $R/scores/mmlu \
  base=$MM/outputs/full_base.jsonl c02_nb_L15u1047_k2=$G4/outputs/final_mmlu.jsonl \
  h5_a2_n5=$R/outputs/h5_a2_n5_mmlu.jsonl mix21_22b0.75_23b0.5=$R/outputs/mix21_22b0.75_23b0.5_mmlu.jsonl \
  combo_a14_b14=$R/outputs/combo_a14_b14_mmlu.jsonl > $R/logs/score_mmlu.log 2>&1
$SB $G -I -B $R/scripts/table.py > $R/scores/table.md
