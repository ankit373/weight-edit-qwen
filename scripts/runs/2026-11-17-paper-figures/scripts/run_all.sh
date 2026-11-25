#!/bin/sh
# rebuild every figure and table from the run files. cpu only, stdlib only. run from the project root.
set -e
R=runs/2026-11-17-paper-figures
SB=envs/run-sandboxed.sh
P=envs/score/bin/python
for s in fig1_main_08b fig2_forest_vs_recover fig3_recover_sweep fig4_partb_2b fig5_mechanism_probe \
         fig6_logit_lens fig7_per_language tab_main_08b tab_partb_2b tab_guard tab_costs tab_examples \
         check_svg hash_files; do
  $SB $P -I -B $R/scripts/$s.py
done
