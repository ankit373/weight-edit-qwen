# queue helpers. source from a queue script run at the project root (sh, set -f).
R=runs/2026-11-10-gate4-eval; S=runs/2026-11-06-gate3-scripts/scripts; G3=runs/2026-11-06-gate3-run
MM=runs/2026-11-08-side-mmlu-redux
SB=envs/run-sandboxed.sh; G=envs/gen/bin/python
FINAL=gate4-workspace/candidates/c02_nb_L15u1047_k2
FSHA=b96ac6f72020da49d39e4f7b89ba1f9854e2e0461a0d80c308723aa40d792824
V=$G3/recover/vectors.safetensors
SEED2=100000
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
wait_charge() {  # under 15%: hold until 22%
  if [ "$(pct)" -lt 15 ]; then
    echo "HOLD battery $(pct)% before $1 $(date -u +%FT%TZ)" >> $R/logs/steps.log
    until [ "$(pct)" -ge 22 ]; do sleep 120; done
    echo "RESUME battery $(pct)% before $1 $(date -u +%FT%TZ)" >> $R/logs/steps.log
  fi
}
# step <name> <rows.jsonl or -> <cmd...>: battery stop (3) -> wait to 22% and resume by id;
# sleep/wake (6) -> logged, resume by id (max 5); any other non-zero -> queue halts.
step() {
  name=$1; out=$2; shift 2; tries=0
  while :; do
    wait_charge $name
    sh $R/scripts/run_watch.sh $name $R/logs/$name.log "$@"; rc=$?
    if [ "$rc" = 0 ]; then break; fi
    tries=$((tries+1))
    if [ "$rc" = 3 ] || { [ "$rc" = 6 ] && [ $tries -le 5 ]; }; then
      echo "RESTART $name after rc=$rc (try $tries) $(date -u +%FT%TZ)" >> $R/logs/steps.log
      [ "$rc" = 3 ] && { until [ "$(pct)" -ge 22 ]; do sleep 120; done; }
      continue
    fi
    echo "HALT queue at $name rc=$rc $(date -u +%FT%TZ)" >> $R/logs/steps.log; exit $rc
  done
  if [ "$out" != "-" ]; then
    $SB $G -I -B $R/scripts/check_rows.py $out >> $R/logs/steps.log 2>&1 || {
      echo "HALT queue: row check failed for $out" >> $R/logs/steps.log; exit 9; }
  fi
}
