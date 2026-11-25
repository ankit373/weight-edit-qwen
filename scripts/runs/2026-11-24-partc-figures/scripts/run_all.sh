#!/bin/sh
# rebuild the part C figures and the number table from the run files. cpu only, stdlib only. run from the project root.
set -e
R=runs/2026-11-24-partc-figures
SB=envs/run-sandboxed.sh
P=envs/score/bin/python
for s in extract figc1_crossling_gain figc2_damage figc3_judge_2b; do
  $SB $P -I -B $R/scripts/$s.py
done
