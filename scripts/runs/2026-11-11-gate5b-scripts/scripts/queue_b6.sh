#!/bin/sh
# B6 (part B plan): eval of the frozen 2B blind edit. part B copy of gate 4 eval queue_a..d, with
# the 2B run folders, the 2B model (run_2b.py) and the D7 controls. run from the project root.
#   queue_b6.sh random FINAL SHA          # cpu: 3 D7 controls from the frozen diff (2B loaded on cpu)
#   queue_b6.sh a FINAL SHA EDITOR_DEV    # path check (20 dev ids vs the editor's rows), final on test, NLL test + dev
#   queue_b6.sh b FINAL SHA               # final on mono 2400; mmlu-redux 5330 for base, final, 3 controls
#   queue_b6.sh c FINAL SHA               # controls: dev + test + NLL each
#   queue_b6.sh d FINAL SHA A R           # second seed on test: baseline, final, ReCoVeR winner (A, R=on|off), instr_end
#   queue_b6.sh noop A R                  # D9: ReCoVeR winner on 20 mmlu prompts vs the base mmlu rows
#   queue_b6.sh score FINAL SHA A R       # cpu: scores, guard summaries, instr_end s2 merge, table_eval.json
# FINAL = frozen diff folder (gate5b-workspace/candidates/<name>), SHA = its diff_file_sha256 (FINAL.md).
# EDITOR_DEV = the editor's own dev rows for that diff (gate5b-workspace/work/<name>/dev.jsonl).
set -f
. runs/2026-11-11-gate5b-scripts/scripts/qlib.sh
stage=${1:-}; [ $# -gt 0 ] && shift
case "$stage" in random|a|b|c|d|noop|score) ;; *) echo "usage: see the header of queue_b6.sh" >&2; exit 2;; esac
B1=$(find_run baseline) || exit 1
R=$(find_run eval new) || exit 1
mkdir -p $R/outputs $R/logs $R/scores $R/guard $R/diffs
I=$MM/data/items_ok.jsonl; A_ALL=$MM/ids/all_ok.txt
log "QUEUE_B6 $stage start R=$R B1=$B1 args=$*"
if [ "$stage" != noop ]; then FINAL=$1; FSHA=$2; shift 2; fi
GD="$RUN $X/gen_diff.py --diff $FINAL --expect-diff-sha $FSHA"
dsha() { $G -I -B -c "import json;print(json.load(open('$1/manifest.json'))['diff_file_sha256'])"; }
nll() {  # nll <name> <rows> <split> <n>
  step nll_$1 $R/guard/$1.nll.jsonl $4 $RUN $G3/scripts/guard.py nll $2 $B1/outputs/baseline_$3.jsonl $R/guard/$1.nll.jsonl
}
flag() { [ "$1" = on ] && echo --restore-norm; }

case "$stage" in
random)
  cpu make_random $SB $G -I -B $X/make_random.py $FINAL $R/diffs $RAND_SEEDS
  ;;
a)
  EDEV=$1
  step repro20_final $R/outputs/repro20_final_dev.jsonl 20 $GD --entry generate --ids $G3/ids/repro20_dev.txt --out $R/outputs/repro20_final_dev.jsonl --method none
  cpu repro20_vs_editor $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/repro20_final_dev.jsonl $EDEV $R/scores/repro20_vs_editor.json --ids $G3/ids/repro20_dev.txt
  $G -I -B -c "import json,sys; r=json.load(open('$R/scores/repro20_vs_editor.json')); sys.exit(0 if r['identical']==r['n']==20 else 1)" \
    || { log "HALT queue: eval path rows differ from the editor's rows"; exit 10; }
  step final_test $R/outputs/final_test.jsonl 2100 $GD --entry generate --ids splits/test.txt --out $R/outputs/final_test.jsonl --method none
  nll final_test $R/outputs/final_test.jsonl test 2100
  nll final_dev $EDEV dev 2086
  ;;
b)
  step final_mono $R/outputs/final_mono.jsonl 2400 $GD --entry generate --ids $G3/ids/mono_all.txt --out $R/outputs/final_mono.jsonl --method none
  step base_mmlu $R/outputs/base_mmlu.jsonl 5330 $RUN $MM/scripts/mmlu_gen.py --items $I --ids $A_ALL --out $R/outputs/base_mmlu.jsonl --method none
  step final_mmlu $R/outputs/final_mmlu.jsonl 5330 $GD --entry mmlu --items $I --ids $A_ALL --out $R/outputs/final_mmlu.jsonl --method none
  for s in $RAND_SEEDS; do
    D=$R/diffs/rand_s$s
    step rand_s${s}_mmlu $R/outputs/rand_s${s}_mmlu.jsonl 5330 $RUN $X/gen_diff.py --diff $D --expect-diff-sha $(dsha $D) --entry mmlu --items $I --ids $A_ALL --out $R/outputs/rand_s${s}_mmlu.jsonl --method none
  done
  ;;
c)
  for s in $RAND_SEEDS; do
    D=$R/diffs/rand_s$s; RD="$RUN $X/gen_diff.py --entry generate --diff $D --expect-diff-sha $(dsha $D)"
    step rand_s${s}_dev $R/outputs/rand_s${s}_dev.jsonl 2086 $RD --ids splits/dev.txt --out $R/outputs/rand_s${s}_dev.jsonl --method none
    step rand_s${s}_test $R/outputs/rand_s${s}_test.jsonl 2100 $RD --ids splits/test.txt --out $R/outputs/rand_s${s}_test.jsonl --method none
    nll rand_s${s}_dev $R/outputs/rand_s${s}_dev.jsonl dev 2086
    nll rand_s${s}_test $R/outputs/rand_s${s}_test.jsonl test 2100
  done
  ;;
d)
  A=$1; RR=$2; RC=$(find_run recover) || exit 1
  step base_test_s2 $R/outputs/base_test_s2.jsonl 2100 $RUN $S/generate.py --ids splits/test.txt --out $R/outputs/base_test_s2.jsonl --method none --seed $SEED2
  step final_test_s2 $R/outputs/final_test_s2.jsonl 2100 $GD --entry generate --ids splits/test.txt --out $R/outputs/final_test_s2.jsonl --method none --seed $SEED2
  step recover_a${A}_${RR}_test_s2 $R/outputs/recover_a${A}_${RR}_test_s2.jsonl 2100 $RUN $G3/scripts/gen_recover_dev.py --ids splits/test.txt --out $R/outputs/recover_a${A}_${RR}_test_s2.jsonl --method recover --vectors $RC/recover/vectors.safetensors --alpha $A $(flag $RR) --seed $SEED2
  step instr_end_test_s2_changed $R/outputs/instr_end_test_s2_changed.jsonl 1316 $RUN $G3/scripts/gen_variant.py --variants $G3/prompts/instr_end.jsonl --kind instr_end --ids $G3/ids/instr_end_changed_test.txt --out $R/outputs/instr_end_test_s2_changed.jsonl --method none --seed $SEED2
  ;;
noop)
  A=$1; RR=$2; RC=$(find_run recover) || exit 1
  [ -f $R/outputs/base_mmlu.jsonl ] || { log "HALT queue: base mmlu (stage b) first"; exit 2; }
  step recover_mmlu_noop20 $R/outputs/recover_a${A}_${RR}_mmlu_noop20.jsonl 20 $RUN $MM/scripts/mmlu_gen.py --items $I --ids $MM/ids/noop20.txt --out $R/outputs/recover_a${A}_${RR}_mmlu_noop20.jsonl --method recover --vectors $RC/recover/vectors.safetensors --alpha $A $(flag $RR)
  cpu noop20_compare $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/recover_a${A}_${RR}_mmlu_noop20.jsonl $R/outputs/base_mmlu.jsonl $R/scores/recover_mmlu_noop20_compare.json --ids $MM/ids/noop20.txt
  ;;
score)
  A=$1; RR=$2; RC=$(find_run recover) || exit 1; IE=$(find_run instr-end) || exit 1
  for n in final_test final_mono base_test_s2 final_test_s2 recover_a${A}_${RR}_test_s2 rand_s1001_dev rand_s1001_test rand_s1002_dev rand_s1002_test rand_s1003_dev rand_s1003_test; do
    cpu score_$n sh $X/score.sh $R/outputs/$n.jsonl $R/scores/$n
  done
  cpu merge_instr_end_s2 $SB $G -I -B $G3/scripts/merge_instr_end.py $R/outputs/instr_end_test_s2_changed.jsonl $R/outputs/base_test_s2.jsonl splits/test.txt $R/outputs/instr_end_test_s2.jsonl
  cpu score_instr_end_test_s2 sh $X/score.sh $R/outputs/instr_end_test_s2.jsonl $R/scores/instr_end_test_s2
  for n in final_test rand_s1001_test rand_s1002_test rand_s1003_test; do
    cpu guard_$n $RUN $G3/scripts/guard.py summary $R/outputs/$n.jsonl $R/guard/$n.nll.jsonl $B1/outputs/baseline_test.jsonl $B1/guard/baseline_test.nll.jsonl splits/test.txt $R/guard/$n.guard.json
  done
  for n in rand_s1001_dev rand_s1002_dev rand_s1003_dev; do
    cpu guard_$n $RUN $G3/scripts/guard.py summary $R/outputs/$n.jsonl $R/guard/$n.nll.jsonl $B1/outputs/baseline_dev.jsonl $B1/guard/baseline_dev.nll.jsonl splits/dev.txt $R/guard/$n.guard.json
  done
  cpu score_mmlu $SB $G -I -B $MM/scripts/score_mmlu.py $I $R/scores/mmlu base=$R/outputs/base_mmlu.jsonl \
    final=$R/outputs/final_mmlu.jsonl rand_s1001=$R/outputs/rand_s1001_mmlu.jsonl \
    rand_s1002=$R/outputs/rand_s1002_mmlu.jsonl rand_s1003=$R/outputs/rand_s1003_mmlu.jsonl
  cpu table $RUN $X/final_table.py $R/scores/table_eval.json \
    baseline=$B1/outputs/baseline_test.jsonl=$B1/scores/baseline_test \
    instr_end=$IE/outputs/instr_end_test.jsonl=$IE/scores/instr_end_test \
    recover_a${A}_${RR}=$RC/outputs/recover_a${A}_${RR}_test.jsonl=$RC/scores/recover_a${A}_${RR}_test \
    recover_a1_on=$RC/outputs/recover_a1_on_test.jsonl=$RC/scores/recover_a1_on_test \
    final_test=$R/outputs/final_test.jsonl=$R/scores/final_test \
    rand_s1001_test=$R/outputs/rand_s1001_test.jsonl=$R/scores/rand_s1001_test \
    rand_s1002_test=$R/outputs/rand_s1002_test.jsonl=$R/scores/rand_s1002_test \
    rand_s1003_test=$R/outputs/rand_s1003_test.jsonl=$R/scores/rand_s1003_test \
    base_test_s2=$R/outputs/base_test_s2.jsonl=$R/scores/base_test_s2 \
    final_test_s2=$R/outputs/final_test_s2.jsonl=$R/scores/final_test_s2 \
    recover_a${A}_${RR}_s2=$R/outputs/recover_a${A}_${RR}_test_s2.jsonl=$R/scores/recover_a${A}_${RR}_test_s2 \
    instr_end_s2=$R/outputs/instr_end_test_s2.jsonl=$R/scores/instr_end_test_s2
  ;;
*) echo "usage: see the header of queue_b6.sh" >&2; exit 2 ;;
esac
log "QUEUE_B6 $stage DONE"
