#!/bin/sh
# part C queue (PROTOCOL.md section 6). run from the project root; done steps are skipped and
# partial rows resume by id. step / cpu / battery / gpu-free / DRY mode: gate 5a eval-prep qlib.sh
# and run_watch.sh, unchanged (battery < 20% stop rc 3, restart at 25%; memory rc 5; sleep rc 6).
#   queue_c.sh all      pre det arena noop gmmlu mgsm ifeval greedy long xl stats, in that order
#   queue_c.sh <stage>  one stage: pre det arena noop gmmlu mgsm ifeval greedy long xl score stats
# a cross-lingual or side stage scores its own rows on cpu at its end; `score` redoes all scoring.
# DRY=1: write every step command to <run>/logs/dry_commands.txt instead of running it.
# PARTC_RUN=<dir>: use this run folder (default: the one runs/*-partc-run, made today if none).
set -f
if [ -z "$PC_CAFF" ]; then exec /usr/bin/caffeinate -i -d -m -s /usr/bin/env PC_CAFF=1 /bin/sh "$0" "$@"; fi
[ -f PROTOCOL.md ] || { echo "run from the project root" >&2; exit 2; }
STAGE=${1:-}
case "$STAGE" in all|pre|det|arena|noop|gmmlu|mgsm|ifeval|greedy|long|xl|score|stats) ;;
  *) sed -n 2,9p "$0" >&2; exit 2;; esac

if [ -n "$PARTC_RUN" ]; then R=$PARTC_RUN; else
  set +f; M_=$(ls -d runs/[0-9]*-partc-run 2>/dev/null); set -f
  case $(printf '%s' "$M_" | grep -c .) in
    0) R=runs/$(date -u +%F)-partc-run ;;
    1) R=$M_ ;;
    *) echo "more than one runs/*-partc-run folder" >&2; exit 2 ;;
  esac
fi
mkdir -p $R/logs $R/ids $R/evidence $R/outputs $R/scores
. runs/2026-11-11-gate5a-eval-prep/scripts/qlib.sh   # sets X, G3, SB, G; defines step, cpu, log

Y=runs/2026-11-22-partc-scripts/scripts
P=envs/score/bin/python
PG=$Y/partc_gen.py
RB=runs/2026-11-11-gate5b-scripts/scripts/run_2b.py
SC=runs/2026-11-11-gate5b-scripts/scripts/score.sh     # gate 1 score.py + wrong_lang.py, unchanged
G3S=runs/2026-11-06-gate3-run/scripts
GD=data/partc
EDITS_08="c02_nb_L15u1047_k2 h5_a2_n5 mix21_22b0.75_23b0.5 combo_a14_b14"
EDITS_2b="c06"
GREEDY_IDS=$GD/lcb-stress/greedy_test_complex_ids.txt
LONG_IDS=$GD/lcb-stress/long400_ids.txt

runner() { if [ "$1" = 08 ]; then echo "$SB $G -I -B"; else echo "$SB $G -I -B $RB"; fi; }
edits() { if [ "$1" = 08 ]; then echo "$EDITS_08"; else echo "$EDITS_2b"; fi; }
methods() { echo "baseline $(edits $1) recover instr_end"; }
rc_args() {  # ReCoVeR per model, PROTOCOL.md section 1
  if [ "$1" = 08 ]; then echo "--vectors runs/2026-11-06-gate3-run/recover/vectors.safetensors --alpha 0.03 --restore-norm"
  else echo "--vectors runs/2026-11-14-gate5b-recover/recover/vectors.safetensors --alpha 0.03"; fi
}
# frozen <edit>: check before use; prints "--diff DIR --expect-diff-sha SHA" for partc_gen.py
frozen() {
  F_=$1
  if [ -n "$DRY" ]; then L_=$($SB $G -I -B $Y/check_frozen_c.py $F_ /dev/null | tail -1)
  else L_=$($SB $G -I -B $Y/check_frozen_c.py $F_ $R/evidence/frozen_${F_}_$(date -u +%Y%m%dT%H%M%SZ).json | tail -1); fi
  set -- $L_
  [ $# = 2 ] || { log "HALT queue: frozen check failed for $F_"; exit 2; }
  echo "--diff $1 --expect-diff-sha $2"
}
odir() {  # odir <set> <model>: XL-AlpacaEval rows live apart (PROTOCOL.md section 8 release rule)
  if [ "$1" = xl-alpacaeval ]; then echo $R/outputs/nc-sa/xl-alpacaeval/$2; else echo $R/outputs/$2/$1; fi
}
sdir() {
  if [ "$1" = xl-alpacaeval ]; then echo $R/scores/nc-sa/xl-alpacaeval/$2; else echo $R/scores/$2/$1; fi
}
nrows() { grep -c . "$1"; }

# ---------------------------------------------------------------- cross-lingual row sets
# cross_set <set> <model>: baseline, edits, ReCoVeR, instruction at end (own rows file), 100 tokens,
# seed 1234 + file index; then guard NLL of every method vs the baseline (base model), then cpu.
cross_set() {
  S_=$1; M_=$2; D_=$(odir $S_ $M_); C_=$(sdir $S_ $M_); mkdir -p $D_/guard $C_
  ROWS_=$GD/$S_/prompts.jsonl; IROWS_=$GD/$S_/prompts_instr_end.jsonl; IDS_=$GD/$S_/ids.txt; N_=$(nrows $IDS_)
  for E_ in $(methods $M_); do
    O_=$D_/$E_.jsonl; T_=${M_}_${S_}_$E_
    case $E_ in
      baseline) step $T_ $O_ $N_ $(runner $M_) $PG --entry generate --rows $ROWS_ --ids $IDS_ --out $O_ --method none ;;
      recover) step $T_ $O_ $N_ $(runner $M_) $PG --entry recover --rows $ROWS_ --ids $IDS_ --out $O_ --method recover $(rc_args $M_) ;;
      instr_end) step $T_ $O_ $N_ $(runner $M_) $PG --entry generate --rows $IROWS_ --ids $IDS_ --out $O_ --method none ;;
      *) FA_=$(frozen $E_) || exit 2
         step $T_ $O_ $N_ $(runner $M_) $PG --entry generate $FA_ --rows $ROWS_ --ids $IDS_ --out $O_ --method none ;;
    esac
  done
  for E_ in $(methods $M_); do  # guard NLL (base model, context = baseline chat text of the same id)
    step ${M_}_${S_}_nll_$E_ $D_/guard/$E_.nll.jsonl $N_ $(runner $M_) $G3S/guard.py nll $D_/$E_.jsonl $D_/baseline.jsonl $D_/guard/$E_.nll.jsonl
  done
  score_cross $S_ $M_
}
score_cross() {
  S_=$1; M_=$2; D_=$(odir $S_ $M_); C_=$(sdir $S_ $M_); IDS_=$GD/$S_/ids.txt; mkdir -p $C_
  for E_ in $(methods $M_); do
    lcb_labels ${M_}_${S_}_$E_ $D_/$E_.jsonl $C_/$E_
    [ $E_ = baseline ] && continue
    cpu guard_${M_}_${S_}_$E_ $(runner $M_) $G3S/guard.py summary $D_/$E_.jsonl $D_/guard/$E_.nll.jsonl \
      $D_/baseline.jsonl $D_/guard/baseline.nll.jsonl $IDS_ $C_/$E_.guard.json
  done
}
# lcb_labels <name> <rows> <prefix> [old rows for the prefix check]: score.sh, per-row labels, loops
lcb_labels() {
  cpu score_$1 sh $SC $2 $3
  cpu perrow_$1 $SB $P -I -B $Y/per_row_lcb.py $2 $3.perrow.jsonl --check $3
  LM_=${1%%_*}  # model tag, first part of the step name
  if [ -n "$4" ]; then cpu loops_$1 $(runner $LM_) $Y/loops_rows.py $2 $3.loops.jsonl --prefix-of $4
  else cpu loops_$1 $(runner $LM_) $Y/loops_rows.py $2 $3.loops.jsonl; fi
}

# ---------------------------------------------------------------- side benchmarks
side_cmd() {  # side_cmd <set> <model> <method or edit> <ids> <out>
  case $1 in
    global-mmlu) A_="--entry gmmlu --items $GD/global-mmlu/items.jsonl" ;;
    mgsm) A_="--entry generate --rows $GD/mgsm/prompts.jsonl --max-new-tokens 384" ;;
    ifeval) A_="--entry generate --rows $GD/ifeval/prompts.jsonl --max-new-tokens 256" ;;
  esac
  case $3 in
    baseline) echo "$(runner $2) $PG $A_ --ids $4 --out $5 --method none" ;;
    recover) [ $1 = global-mmlu ] || A_=$(echo "$A_" | sed 's/--entry generate/--entry recover/')
             echo "$(runner $2) $PG $A_ --ids $4 --out $5 --method recover $(rc_args $2)" ;;
    *) FA_=$(frozen $3) || exit 2
       echo "$(runner $2) $PG $FA_ $A_ --ids $4 --out $5 --method none" ;;
  esac
}
noop_set() {  # noop_set <set> <model>: first 20 ids, ReCoVeR vs baseline, byte-identical + 0 hooks
  S_=$1; M_=$2; D_=$(odir $S_ $M_); C_=$(sdir $S_ $M_); mkdir -p $D_ $C_
  I20_=$R/ids/noop20_$S_.txt
  head -20 $GD/$S_/ids.txt > $I20_
  step ${M_}_${S_}_baseline_first20 $D_/baseline.jsonl 20 $(side_cmd $S_ $M_ baseline $I20_ $D_/baseline.jsonl)
  step ${M_}_${S_}_recover_noop20 $D_/recover_noop20.jsonl 20 $(side_cmd $S_ $M_ recover $I20_ $D_/recover_noop20.jsonl)
  if [ $S_ = global-mmlu ]; then H_=-; else H_=$D_/recover_noop20.jsonl.hooks.jsonl; fi
  cpu noop_${M_}_$S_ $SB $G -I -B $Y/same_rows.py $D_/recover_noop20.jsonl $D_/baseline.jsonl $I20_ \
    $C_/recover_noop20.json --hooks-zero $H_
}
side_set() {  # side_set <set> <model>: baseline and every edit on the whole set, then cpu scoring
  S_=$1; M_=$2; D_=$(odir $S_ $M_); IDS_=$GD/$S_/ids.txt; N_=$(nrows $IDS_); mkdir -p $D_
  for E_ in baseline $(edits $M_); do
    CMD_=$(side_cmd $S_ $M_ $E_ $IDS_ $D_/$E_.jsonl) || exit 2
    step ${M_}_${S_}_$E_ $D_/$E_.jsonl $N_ $CMD_
  done
  score_side $S_ $M_
}
score_side() {
  S_=$1; M_=$2; D_=$(odir $S_ $M_); C_=$(sdir $S_ $M_); mkdir -p $C_
  for E_ in baseline $(edits $M_); do
    case $S_ in
      mgsm) cpu score_${M_}_${S_}_$E_ $SB $P -I -B $Y/mgsm_score.py $D_/$E_.jsonl $GD/mgsm/prompts.jsonl $C_/$E_ ;;
      ifeval) cpu score_${M_}_${S_}_$E_ $SB $P -I -B $Y/ifeval_score.py $D_/$E_.jsonl $GD/ifeval/prompts.jsonl $C_/$E_ ;;
    esac
  done
}

# ---------------------------------------------------------------- LCB stress
# stress <greedy|long> <model>: test complex greedy (714, 100 tok) or long400 (238, 400 tok, sampled)
stress() {
  K_=$1; M_=$2; D_=$R/outputs/$M_/lcb-$K_; mkdir -p $D_
  if [ $K_ = greedy ]; then IDS_=$GREEDY_IDS; X_="--greedy"; else IDS_=$LONG_IDS; X_="--max-new-tokens 400"; fi
  N_=$(nrows $IDS_); CH_=$R/ids/instr_end_changed_$K_.txt
  grep -Fxf runs/2026-11-06-gate3-run/ids/instr_end_changed_test.txt $IDS_ > $CH_
  NC_=$(nrows $CH_)
  for E_ in $(methods $M_); do
    O_=$D_/$E_.jsonl; T_=${M_}_lcb-${K_}_$E_
    case $E_ in
      baseline) step $T_ $O_ $N_ $(runner $M_) $PG $X_ --entry generate --ids $IDS_ --out $O_ --method none ;;
      recover) step $T_ $O_ $N_ $(runner $M_) $PG $X_ --entry recover --ids $IDS_ --out $O_ --method recover $(rc_args $M_) ;;
      instr_end)  # changed prompts only; unchanged ones reuse the baseline rows (gate 3 merge_instr_end.py)
        step ${T_}_changed $D_/instr_end_changed.jsonl $NC_ $(runner $M_) $PG $X_ --entry variant \
          --variants runs/2026-11-06-gate3-run/prompts/instr_end.jsonl --kind instr_end --ids $CH_ --out $D_/instr_end_changed.jsonl --method none
        cpu merge_$T_ $SB $G -I -B $G3S/merge_instr_end.py $D_/instr_end_changed.jsonl $D_/baseline.jsonl $IDS_ $O_ ;;
      *) FA_=$(frozen $E_) || exit 2
         step $T_ $O_ $N_ $(runner $M_) $PG $X_ --entry generate $FA_ --ids $IDS_ --out $O_ --method none ;;
    esac
  done
  score_stress $K_ $M_
}
s1_rows() {  # existing seed 1, 100-token test rows of each method (2100 ids)
  case $1_$2 in
    08_baseline) echo runs/2026-11-06-gate3-run/outputs/baseline_test.jsonl ;;
    08_instr_end) echo runs/2026-11-06-gate3-run/outputs/instr_end_test.jsonl ;;
    08_recover) echo runs/2026-11-06-gate3-run/outputs/recover_a0.03_on_test.jsonl ;;
    08_c02_nb_L15u1047_k2) echo runs/2026-11-10-gate4-eval/outputs/final_test.jsonl ;;
    08_h5_a2_n5) echo runs/2026-11-11-gate5a-eval-ws1/outputs/final_test.jsonl ;;
    08_mix21_22b0.75_23b0.5) echo runs/2026-11-12-gate5a-eval-ws2/outputs/final_test.jsonl ;;
    08_combo_a14_b14) echo runs/2026-11-13-gate5a-eval-ws3/outputs/final_test.jsonl ;;
    2b_baseline) echo runs/2026-11-11-gate5b-baseline/outputs/baseline_test.jsonl ;;
    2b_instr_end) echo runs/2026-11-13-gate5b-instr-end/outputs/instr_end_test.jsonl ;;
    2b_recover) echo runs/2026-11-14-gate5b-recover/outputs/recover_a0.03_off_test.jsonl ;;
    2b_c06) echo runs/2026-11-17-gate5b-eval/outputs/final_test.jsonl ;;
  esac
}
score_stress() {
  K_=$1; M_=$2; D_=$R/outputs/$M_/lcb-$K_; C_=$R/scores/$M_/lcb-$K_; mkdir -p $C_
  for E_ in $(methods $M_); do
    if [ $K_ = long ]; then lcb_labels ${M_}_lcb-${K_}_$E_ $D_/$E_.jsonl $C_/$E_ $(s1_rows $M_ $E_)
    else lcb_labels ${M_}_lcb-${K_}_$E_ $D_/$E_.jsonl $C_/$E_; fi
    [ $K_ = greedy ] && cpu perrow_s1_${M_}_$E_ $SB $P -I -B $Y/per_row_lcb.py $(s1_rows $M_ $E_) $C_/${E_}_s1.perrow.jsonl
  done
}

# ---------------------------------------------------------------- determinism (step 1)
det() {  # det <model>: 20 rows twice per wrapper path, byte-identical
  M_=$1; D_=$R/outputs/$M_/det; C_=$R/scores/$M_/det; mkdir -p $D_ $C_
  head -20 $GD/m-arenahard/ids.txt > $R/ids/det20_arena.txt
  head -20 $LONG_IDS > $R/ids/det20_long.txt
  head -20 $GD/global-mmlu/ids.txt > $R/ids/det20_gmmlu.txt
  for T_ in a b; do
    step ${M_}_det_rows_$T_ $D_/rows_$T_.jsonl 20 $(runner $M_) $PG --entry generate --rows $GD/m-arenahard/prompts.jsonl --ids $R/ids/det20_arena.txt --out $D_/rows_$T_.jsonl --method none
    step ${M_}_det_cap_$T_ $D_/cap_$T_.jsonl 20 $(runner $M_) $PG --max-new-tokens 400 --entry generate --ids $R/ids/det20_long.txt --out $D_/cap_$T_.jsonl --method none
    step ${M_}_det_gmmlu_$T_ $D_/gmmlu_$T_.jsonl 20 $(runner $M_) $PG --entry gmmlu --items $GD/global-mmlu/items.jsonl --ids $R/ids/det20_gmmlu.txt --out $D_/gmmlu_$T_.jsonl --method none
  done
  for W_ in rows:arena cap:long gmmlu:gmmlu; do
    cpu det_${M_}_${W_%%:*} $SB $G -I -B $Y/same_rows.py $D_/${W_%%:*}_a.jsonl $D_/${W_%%:*}_b.jsonl $R/ids/det20_${W_#*:}.txt $C_/${W_%%:*}.json
  done
}

# ---------------------------------------------------------------- stats (cpu)
pairs_cross() {  # every method vs baseline; every edit vs ReCoVeR and vs instruction at end
  L_="recover:baseline,instr_end:baseline"
  for E_ in $(edits $1); do L_="$L_,$E_:baseline,$E_:recover,$E_:instr_end"; done
  echo $L_
}
labels_cross() {  # labels_cross <score dir> <model>
  for E_ in $(methods $2); do printf '%s ' "$E_=$1/$E_.perrow.jsonl,$1/$E_.loops.jsonl"; done
}
stats_all() {
  for M_ in 08 2b; do
    for S_ in m-arenahard xl-alpacaeval; do
      C_=$(sdir $S_ $M_)
      cpu stats_${M_}_$S_ $SB $P -I -B $Y/stats_c.py lpr $C_/stats.json $(labels_cross $C_ $M_) --pairs $(pairs_cross $M_)
    done
    for K_ in greedy long; do
      C_=$R/scores/$M_/lcb-$K_
      cpu stats_${M_}_lcb-$K_ $SB $P -I -B $Y/stats_c.py lpr $C_/stats.json $(labels_cross $C_ $M_) --pairs $(pairs_cross $M_)
    done
    C_=$R/scores/$M_/lcb-greedy; L_=""; PS_=""
    for E_ in $(methods $M_); do L_="$L_ ${E_}_greedy=$C_/$E_.perrow.jsonl ${E_}_s1=$C_/${E_}_s1.perrow.jsonl"; PS_="$PS_,${E_}_greedy:${E_}_s1"; done
    cpu stats_${M_}_greedy_vs_s1 $SB $P -I -B $Y/stats_c.py lpr $C_/stats_greedy_vs_s1.json $L_ --pairs ${PS_#,}
    PE_=""; for E_ in $(edits $M_); do PE_="$PE_,$E_:baseline"; done; PE_=${PE_#,}
    D_=$(odir global-mmlu $M_); C_=$(sdir global-mmlu $M_); L_=""
    for E_ in baseline $(edits $M_); do L_="$L_ $E_=$D_/$E_.jsonl"; done
    cpu stats_${M_}_gmmlu $SB $P -I -B $Y/stats_c.py gmmlu $C_/stats.json $L_ --pairs $PE_
    for S_ in mgsm ifeval; do
      C_=$(sdir $S_ $M_); L_=""
      for E_ in baseline $(edits $M_); do L_="$L_ $E_=$C_/$E_.rows.jsonl"; done
      cpu stats_${M_}_$S_ $SB $P -I -B $Y/stats_c.py $S_ $C_/stats.json $L_ --pairs $PE_
    done
  done
}

# ---------------------------------------------------------------- stages
pre() {
  [ -z "$(gpu_busy)" ] || { log "HALT queue: gpu busy at precheck: $(gpu_busy)"; exit 7; }
  cpu precheck sh $Y/precheck_c.sh $R
  for E_ in $EDITS_08 $EDITS_2b; do frozen $E_ > /dev/null || exit 2; done
}
run_stage() {
  log "QUEUE_C $1 start R=$R"
  case $1 in
    pre) pre ;;
    det) det 08; det 2b ;;
    arena) cross_set m-arenahard 08; cross_set m-arenahard 2b ;;
    noop) for S_ in global-mmlu mgsm ifeval; do noop_set $S_ 08; noop_set $S_ 2b; done ;;
    gmmlu) side_set global-mmlu 08; side_set global-mmlu 2b ;;
    mgsm) side_set mgsm 08; side_set mgsm 2b ;;
    ifeval) side_set ifeval 08; side_set ifeval 2b ;;
    greedy) stress greedy 08; stress greedy 2b ;;
    long) stress long 08; stress long 2b ;;
    xl) cross_set xl-alpacaeval 08; cross_set xl-alpacaeval 2b ;;
    score) for M0_ in 08 2b; do
             score_cross m-arenahard $M0_; score_cross xl-alpacaeval $M0_
             score_side mgsm $M0_; score_side ifeval $M0_
             score_stress greedy $M0_; score_stress long $M0_
           done ;;
    stats) stats_all ;;
  esac
  log "QUEUE_C $1 DONE"
}
if [ "$STAGE" = all ]; then
  for ST_ in pre det arena noop gmmlu mgsm ifeval greedy long xl stats; do run_stage $ST_; done
  log "QUEUE_C all DONE"
else
  run_stage $STAGE
fi
