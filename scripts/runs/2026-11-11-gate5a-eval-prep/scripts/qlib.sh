# part A eval queue helpers. copy of runs/2026-11-11-gate5b-scripts/scripts/qlib.sh (step, cpu,
# wait_charge: 20% stop / 25% restart), with gate 5b paths dropped, a gpu-free check and DRY=1 mode.
# source from a queue script run at the project root, with `set -f`, after R (run dir) is set.
# DRY=1: write each step's command to $R/logs/dry_commands.txt instead of running it.
X=runs/2026-11-11-gate5a-eval-prep/scripts
G3=runs/2026-11-06-gate3-run
SB=envs/run-sandboxed.sh; G=envs/gen/bin/python
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
log() { echo "$* $(date -u +%FT%TZ)" >> $R/logs/steps.log; }
dry() { echo "$*" >> $R/logs/dry_commands.txt; }

wait_charge() {  # under 20% (any charge state): hold until 25%
  if [ "$(pct)" -lt 20 ]; then
    log "HOLD battery $(pct)% before $1"
    until [ "$(pct)" -ge 25 ]; do sleep 120; done
    log "RESUME battery $(pct)% before $1"
  fi
}

# gpu_busy: prints what holds the gpu (editor lock file, or any gen-env python), empty if free
gpu_busy() {
  b=""
  [ -e "$WS/logs/gpu.lock" ] && b="lock $WS/logs/gpu.lock"
  p=$(/usr/bin/pgrep -f 'envs/gen/bin/python' | tr '\n' ' ')
  [ -n "$p" ] && b="$b pids $p"
  echo "$b"
}
wait_gpu() {  # hold (poll 60 s) while another job uses the gpu
  if [ -n "$(gpu_busy)" ]; then
    log "HOLD gpu busy before $1: $(gpu_busy)"
    while [ -n "$(gpu_busy)" ]; do sleep 60; done
    log "RESUME gpu free before $1"
  fi
}

n_unique() { $SB $G -I -B $X/check_rows.py "$1" | sed -E 's/.*"n_unique": ([0-9]+).*/\1/'; }

# step <name> <rows.jsonl or -> <expected rows or -> <cmd...>
# done already (rows file has the expected count) -> skipped. battery stop (3) -> wait to 25% and
# resume by id; sleep/wake (6) -> resume by id (max 5); memory (5), slow (4), any other -> halt.
# after the step: row check (parse, no duplicate ids) and, if given, the expected count.
step() {
  name=$1; out=$2; want=$3; shift 3; tries=0
  if [ -n "$DRY" ]; then dry "step $name out=$out want=$want :: $*"; return 0; fi
  if [ "$out" != "-" ] && [ "$want" != "-" ] && [ -f "$out" ] && [ "$(n_unique $out)" -ge "$want" ]; then
    log "SKIP $name (already $want rows)"; return 0
  fi
  while :; do
    wait_charge $name
    wait_gpu $name
    sh $X/run_watch.sh $R $name $R/logs/$name.log "$@"; rc=$?
    if [ "$rc" = 0 ]; then break; fi
    tries=$((tries+1))
    if [ "$rc" = 3 ] || { [ "$rc" = 6 ] && [ $tries -le 5 ]; }; then
      log "RESTART $name after rc=$rc (try $tries)"
      [ "$rc" = 3 ] && { until [ "$(pct)" -ge 25 ]; do sleep 120; done; }
      continue
    fi
    log "HALT queue at $name rc=$rc"; exit $rc
  done
  if [ "$out" != "-" ]; then
    $SB $G -I -B $X/check_rows.py $out >> $R/logs/steps.log 2>&1 || { log "HALT queue: row check failed for $out"; exit 9; }
    if [ "$want" != "-" ] && [ "$(n_unique $out)" != "$want" ]; then log "HALT queue: $out has $(n_unique $out) rows, want $want"; exit 9; fi
  fi
}

# cpu <name> <cmd...>: no gpu, output to logs/<name>.log, halt on non-zero
cpu() {
  name=$1; shift
  if [ -n "$DRY" ]; then dry "cpu $name :: $*"; return 0; fi
  log "CPU $name start"
  "$@" >> $R/logs/$name.log 2>&1 || { log "HALT queue: cpu step $name failed"; exit 8; }
  log "CPU $name end"
}
