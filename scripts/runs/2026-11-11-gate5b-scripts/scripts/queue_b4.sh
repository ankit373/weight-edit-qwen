#!/bin/sh
# B4 (part B plan): ReCoVeR tuned on dev, 2B. gate 3 code unchanged (generate.py through
# gen_recover_dev.py, recover_collect.py, recover_norms.py, guard.py), model via run_2b.py.
# run from the project root, one stage at a time, in this order:
#   queue_b4.sh vectors              # 2B language vectors (2048-d) on gate 3's FLORES files + langs, then norms
#   queue_b4.sh screen               # D4 grid (18) on screen98, certain-fail loop rule, passers -> 672 + NLL + guard
#   queue_b4.sh dev A1 R1 A2 R2      # best 2 guard passers (chosen by hand from the screen stage) + paper default -> all dev 2086
#   queue_b4.sh test A R             # winner (chosen by hand by the selection rule) and paper default on test, once
# R = on|off (restore norm). grid fixed before any 2B result (D4), no extension.
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
stage=${1:-}
case "$stage" in vectors|screen|dev|test) ;; *) echo "usage: queue_b4.sh vectors|screen|dev A1 R1 A2 R2|test A R" >&2; exit 2;; esac
B1=$(find_run baseline) || exit 1
R=$(find_run recover new) || exit 1
mkdir -p $R/outputs $R/logs $R/scores $R/guard $R/recover
V=$R/recover/vectors.safetensors
RG="$RUN $G3/scripts/gen_recover_dev.py"
GRID_ALPHAS="0.01 0.02 0.03 0.05 0.1 0.25 0.5 1 2"
LANGS=eng_Latn,arb_Arab,deu_Latn,spa_Latn,fra_Latn,hin_Deva,ind_Latn,ita_Latn,jpn_Jpan,kor_Hang,por_Latn,rus_Cyrl,tur_Latn,vie_Latn,zho_Hans,eus_Latn,swh_Latn,tha_Thai,pes_Arab
log "QUEUE_B4 $stage start R=$R B1=$B1"
flag() { [ "$1" = on ] && echo --restore-norm; }
# guard <name> <rows> <ids> [n]: NLL of the rows (2B base, no hook), then the 3 checks vs the B1 2B rows
guard() {
  step nll_$1 $R/guard/$1.nll.jsonl ${4:--} $RUN $G3/scripts/guard.py nll $2 $B1/outputs/baseline_dev.jsonl $R/guard/$1.nll.jsonl
  cpu guard_$1 $RUN $G3/scripts/guard.py summary $2 $R/guard/$1.nll.jsonl $B1/outputs/baseline_dev.jsonl $B1/guard/baseline_dev.nll.jsonl $3 $R/guard/$1.guard.json
}

case "$stage" in
vectors)
  [ -f $V ] && { log "HALT queue: $V exists"; exit 2; }
  step recover_vectors - - $RUN $S/recover_collect.py --flores-dir external/flores200/extracted/flores200_dataset/dev --langs $LANGS --out $V
  step recover_norms - - $RUN $G3/scripts/recover_norms.py $G3/ids/smoke5_dev.txt $V $R/recover/norms_smoke5.json
  # ReCoVeR attaches no hook to monolingual prompts (gate 3 check): same check on 2B, 20 mono prompts vs B1 rows
  step recover_mono20 $R/outputs/recover_a1_on_mono20.jsonl 20 $RG --ids $G3/ids/mono20.txt --out $R/outputs/recover_a1_on_mono20.jsonl --method recover --vectors $V --alpha 1 --restore-norm
  cpu mono20_compare $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/recover_a1_on_mono20.jsonl $B1/outputs/full_nonthinking.jsonl $R/scores/recover_mono20_compare.json --ids $G3/ids/mono20.txt
  ;;
screen)
  [ -f $V ] || { log "HALT queue: run the vectors stage first"; exit 2; }
  # certain-fail rule (gate 3 README): smallest loop count L on the 98 that already breaks +2 pts on the 672
  b=$($SB $G -I -B $G3/scripts/loop_count.py $B1/outputs/baseline_dev.jsonl $G3/ids/dev_complex.txt 2>>$R/logs/loop_count.err | grep "\"loop\"" | tail -1 | $G -I -B -c "import json,sys;print(json.load(sys.stdin)['loop'])")
  case "$b" in ""|*[!0-9]*) log "SCREEN baseline loop count unreadable: [$b], halt"; exit 3;; esac
  T=$($G -I -B -c "b=$b; print(next(L for L in range(673) if 100*(L-b)/672 > 2.0))")
  log "SCREEN rule: B1 dev complex loops $b of 672 -> certain fail at >= $T loops on the 98"
  for a in $GRID_ALPHAS; do
    for r in on off; do
      n=recover_a${a}_${r}_devcx; out=$R/outputs/$n.jsonl
      step ${n}_screen - - $RG --ids $G3/ids/dev_complex_screen98.txt --out $out --method recover --vectors $V --alpha $a $(flag $r)
      out=$R/outputs/$n.jsonl  # step() sets the global out; reset it (fix 2026-11-14)
      loops=$($SB $G -I -B $G3/scripts/loop_count.py $out $G3/ids/dev_complex_screen98.txt 2>>$R/logs/loop_count.err | grep "\"loop\"" | tail -1 | $G -I -B -c "import json,sys;print(json.load(sys.stdin)['loop'])")
      case "$loops" in ""|*[!0-9]*) log "SCREEN $n loop count unreadable: [$loops], halt"; exit 3;; esac
      log "SCREEN $n loops=$loops (certain fail at >= $T)"
      if [ "$loops" -lt "$T" ]; then
        step $n $out 672 $RG --ids $G3/ids/dev_complex.txt --out $out --method recover --vectors $V --alpha $a $(flag $r)
        guard $n $out $G3/ids/dev_complex.txt 672
        cpu score_$n sh $X/score.sh $out $R/scores/$n
      fi
    done
  done
  ;;
dev)
  [ $# = 5 ] || { echo "dev needs A1 R1 A2 R2" >&2; exit 2; }
  for pair in "$2 $3" "$4 $5" "1 on"; do
    set -- $pair; a=$1; r=$2; n=recover_a${a}_${r}_dev; out=$R/outputs/$n.jsonl
    step $n $out 2086 $RG --ids splits/dev.txt --out $out --method recover --vectors $V --alpha $a $(flag $r)
    guard $n $out splits/dev.txt 2086
    cpu score_$n sh $X/score.sh $out $R/scores/$n
  done
  ;;
test)
  [ $# = 3 ] || { echo "test needs A R" >&2; exit 2; }
  for pair in "$2 $3" "1 on"; do
    set -- $pair; a=$1; r=$2; n=recover_a${a}_${r}_test; out=$R/outputs/$n.jsonl
    step $n $out 2100 $RG --ids splits/test.txt --out $out --method recover --vectors $V --alpha $a $(flag $r)
    cpu score_$n sh $X/score.sh $out $R/scores/$n
  done
  ;;
esac
log "QUEUE_B4 $stage DONE"
