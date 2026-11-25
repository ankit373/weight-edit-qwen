#!/bin/sh
# part A eval of one frozen editor diff (PROTOCOL "decisions after gate 4": test, guard, 1 random control seed).
# usage (project root): sh runs/2026-11-11-gate5a-eval-prep/scripts/queue_eval.sh \
#   <workspace> <diff_dir> <diff_sha256> <run_dir> [<editor_dev_rows.jsonl>]
# workspace = gate5-workspace-N (seed = 1000 + N). editor dev rows default: <workspace>/work/<diff name>/dev.jsonl.
# DRY=1 in the env: checks args, sha, env locks, then lists the steps in <run_dir>/logs/dry_commands.txt.
set -f
if [ -z "$G5A_CAFF" ]; then exec /usr/bin/caffeinate -i -d -m -s /usr/bin/env G5A_CAFF=1 /bin/sh "$0" "$@"; fi
die() { echo "REFUSED: $*" >&2; exit 2; }
[ -f PROTOCOL.md ] && [ -d runs/2026-11-11-gate5a-eval-prep ] || die "run from the project root"
[ $# -eq 4 ] || [ $# -eq 5 ] || die "usage: queue_eval.sh <workspace> <diff_dir> <diff_sha256> <run_dir> [<editor_dev_rows>]"
abs() { (cd "$1" 2>/dev/null && pwd -P) || die "not a folder: $1"; }

WS=$(abs "$1") || exit 2; DIFF=$(abs "$2") || exit 2; SHA=$3
n=$(basename "$WS" | sed -nE 's/^gate5-workspace-([123])$/\1/p')
[ -n "$n" ] || die "workspace must be gate5-workspace-1, -2 or -3: $WS"
SEED=$((1000 + n))
case "$DIFF" in "$WS"/candidates/*) ;; *) die "diff dir is not under $WS/candidates/: $DIFF";; esac
[ -f "$WS/tools/apply_diff.py" ] || die "no $WS/tools/apply_diff.py"
ROWS=${5:-$WS/work/$(basename "$DIFF")/dev.jsonl}
[ -f "$ROWS" ] || die "editor dev rows not found: $ROWS (pass them as the 5th arg)"
ROWS=$(abs "$(dirname "$ROWS")")/$(basename "$ROWS") || exit 2
mkdir -p "$4" || die "cannot make $4"
R=$(abs "$4") || exit 2
mkdir -p $R/logs $R/outputs $R/guard $R/diffs $R/scores $R/evidence $R/env
. runs/2026-11-11-gate5a-eval-prep/scripts/qlib.sh

# 1. frozen diff check (stdlib, no model). refuse on any mismatch. a rerun must name the same diff.
$SB $G -I -B $X/check_frozen.py $DIFF $SHA $R/evidence/frozen_check_$(date -u +%Y%m%dT%H%M%SZ).json --rows $ROWS \
  || die "frozen diff check failed (see stderr above)"
pin="workspace $WS
diff_dir $DIFF
diff_sha256 $SHA
control_seed $SEED
editor_dev_rows $ROWS"
if [ -f $R/evidence/pin.txt ]; then
  [ "$(cat $R/evidence/pin.txt)" = "$pin" ] || die "$R was started for another diff (evidence/pin.txt)"
else
  echo "$pin" > $R/evidence/pin.txt
fi
[ -n "$DRY" ] && : > $R/logs/dry_commands.txt

# 2. env: lock files must equal gate 1 / gate 4 eval (runs/2026-11-10-gate4-eval/env/lock_sha256.txt)
for f in gen score score-build; do
  want=$(awk -v f="$f.lock.txt" '$1==f {print $2}' runs/2026-11-10-gate4-eval/env/lock_sha256.txt)
  got=$(shasum -a 256 envs/lock/$f.lock.txt | cut -d' ' -f1)
  echo "$f.lock.txt $got $([ "$got" = "$want" ] && echo same_as_gate4_eval || echo DIFFERENT)"
  [ "$got" = "$want" ] || die "envs/lock/$f.lock.txt changed since the gate 4 eval"
done > $R/env/lock_sha256.txt
{ sysctl -n hw.model machdep.cpu.brand_string hw.memsize; sw_vers; } > $R/env/hardware.txt

# 3. one gpu job at a time
busy=$(gpu_busy)
if [ -n "$busy" ]; then
  [ -n "$DRY" ] || die "gpu busy: $busy"
  dry "note: a real run would refuse now, gpu busy: $busy"
fi
[ -n "$DRY" ] || log "QUEUE start ws=$WS diff=$DIFF sha=$SHA seed=$SEED"

GD="$SB $G -I -B $X/gen_diff.py --tools $WS/tools --diff $DIFF --expect-diff-sha $SHA"
NT=$(grep -c . splits/test.txt); ND=$(grep -c . splits/dev.txt)

# A0 path check: 20 dev prompts through this wrapper must equal the editor's own dev rows
step repro20 $R/outputs/repro20_dev.jsonl 20 $GD --ids $G3/ids/repro20_dev.txt --out $R/outputs/repro20_dev.jsonl --method none
cpu repro20_compare $SB $G -I -B $G3/scripts/compare_outputs.py $R/outputs/repro20_dev.jsonl $ROWS $R/evidence/repro20_compare.json --ids $G3/ids/repro20_dev.txt
cpu repro20_gate $SB $G -I -B -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['identical'], r['n']); sys.exit(r['identical'] != 20)" $R/evidence/repro20_compare.json

# A1 final edit on test, A2 guard nll test, A3 guard nll dev (editor rows)
step final_test $R/outputs/final_test.jsonl $NT $GD --ids splits/test.txt --out $R/outputs/final_test.jsonl --method none
step nll_final_test $R/guard/final_test.nll.jsonl $NT $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/final_test.jsonl $G3/outputs/baseline_test.jsonl $R/guard/final_test.nll.jsonl
step nll_final_dev $R/guard/final_dev.nll.jsonl $ND $SB $G -I -B $G3/scripts/guard.py nll $ROWS $G3/outputs/baseline_dev.jsonl $R/guard/final_dev.nll.jsonl

# C random control, one seed, test only: same tensors, positions, fro norm (make_random v3, cpu model load)
RD=$R/diffs/rand_s$SEED
if [ -n "$DRY" ] || [ ! -f $RD/manifest.json ]; then
  cpu make_random $SB $G -I -B $X/make_random.py --tools $WS/tools $DIFF $R/diffs $SEED
fi
if [ -n "$DRY" ]; then DS="<diff_file_sha256 from $RD/manifest.json>"; else
  DS=$($SB $G -I -B -c "import json,sys; print(json.load(open(sys.argv[1]))['diff_file_sha256'])" $RD/manifest.json) \
    || { log "HALT queue: no control manifest"; exit 8; }
fi
GR="$SB $G -I -B $X/gen_diff.py --tools $WS/tools --diff $RD --expect-diff-sha $DS"
step rand_s${SEED}_test $R/outputs/rand_s${SEED}_test.jsonl $NT $GR --ids splits/test.txt --out $R/outputs/rand_s${SEED}_test.jsonl --method none
step nll_rand_s${SEED}_test $R/guard/rand_s${SEED}_test.nll.jsonl $NT $SB $G -I -B $G3/scripts/guard.py nll $R/outputs/rand_s${SEED}_test.jsonl $G3/outputs/baseline_test.jsonl $R/guard/rand_s${SEED}_test.nll.jsonl
[ -n "$DRY" ] || log "QUEUE gpu done"

# cpu scoring (gate 1 scorer via score.sh, gate 3 guard summary / report / eyeball, gate 4 final_table)
P1=runs/2026-11-08-mit-p50c/guard/baseline_test.nll.jsonl
cpu score_final_test sh $X/score.sh $R/outputs/final_test.jsonl $R/scores/final_test
cpu score_rand_test sh $X/score.sh $R/outputs/rand_s${SEED}_test.jsonl $R/scores/rand_s${SEED}_test
cpu guard_final_test $SB $G -I -B $G3/scripts/guard.py summary $R/outputs/final_test.jsonl $R/guard/final_test.nll.jsonl $G3/outputs/baseline_test.jsonl $P1 splits/test.txt $R/guard/final_test.guard.json
cpu guard_final_dev $SB $G -I -B $G3/scripts/guard.py summary $ROWS $R/guard/final_dev.nll.jsonl $G3/outputs/baseline_dev.jsonl $G3/guard/baseline_dev.nll.jsonl splits/dev.txt $R/guard/final_dev.guard.json
cpu guard_rand_test $SB $G -I -B $G3/scripts/guard.py summary $R/outputs/rand_s${SEED}_test.jsonl $R/guard/rand_s${SEED}_test.nll.jsonl $G3/outputs/baseline_test.jsonl $P1 splits/test.txt $R/guard/rand_s${SEED}_test.guard.json
cpu report_test $SB $G -I -B $G3/scripts/report.py $R/scores/report_test.md test gate1=$G3/scores/baseline_test final=$R/scores/final_test rand_s$SEED=$R/scores/rand_s${SEED}_test
cpu final_table $SB $G -I -B $X/final_table.py $R/scores/table_eval.json final=$R/outputs/final_test.jsonl=$R/scores/final_test rand_s$SEED=$R/outputs/rand_s${SEED}_test.jsonl=$R/scores/rand_s${SEED}_test gate1=$G3/outputs/baseline_test.jsonl=$G3/scores/baseline_test
if [ -n "$DRY" ]; then dry "cpu eyeball :: $SB $G -I -B $G3/scripts/eyeball.py $R/outputs/final_test.jsonl splits/test.txt 20 300 > $R/evidence/eyeball20_final_test.txt"
else
  $SB $G -I -B $G3/scripts/eyeball.py $R/outputs/final_test.jsonl splits/test.txt 20 300 > $R/evidence/eyeball20_final_test.txt \
    || { log "HALT queue: eyeball failed"; exit 8; }
  log "QUEUE done"
fi
