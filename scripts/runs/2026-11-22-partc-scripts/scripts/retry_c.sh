#!/bin/sh
# runs/2026-11-22-partc-08b-side/scripts/retry.sh pattern around queue_c.sh (default stage: all).
# rc 5 (memory): wait for swap used < 12 GB and mem free >= 30% for 5 min, retry. rc 3 (battery):
# wait for >= 25%, retry. max 6 retries. any other rc stops. log: <run>/logs/chain.log; the run folder is fixed once
# here and passed to queue_c.sh as PARTC_RUN, so a restart after midnight keeps the same folder.
# usage (project root): sh runs/2026-11-22-partc-scripts/scripts/retry_c.sh [stage]
[ -f PROTOCOL.md ] || { echo "run from the project root" >&2; exit 2; }
ST=${1:-all}
Q=runs/2026-11-22-partc-scripts/scripts/queue_c.sh
if [ -z "$PARTC_RUN" ]; then  # same rule as queue_c.sh: the one runs/*-partc-run, else made today
  m=$(ls -d runs/[0-9]*-partc-run 2>/dev/null)
  case $(printf '%s' "$m" | grep -c .) in
    0) PARTC_RUN=runs/$(date -u +%F)-partc-run ;;
    1) PARTC_RUN=$m ;;
    *) echo "more than one runs/*-partc-run folder" >&2; exit 2 ;;
  esac
fi
export PARTC_RUN
mkdir -p $PARTC_RUN/logs
L=$PARTC_RUN/logs/chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
ok_mem() { u=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6); print $6}'); m=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}'); [ "${u%.*}" -lt 12288 ] && [ "$m" -ge 30 ]; }
t=0
while :; do
  log "START queue_c.sh $ST (retry try $t)"
  sh $Q $ST >> $L 2>&1; rc=$?
  log "END rc=$rc queue_c.sh $ST (retry try $t)"
  { [ $rc -eq 5 ] || [ $rc -eq 3 ]; } && [ $t -lt 6 ] || exit $rc
  t=$((t+1))
  if [ $rc -eq 3 ]; then
    until [ "$(pct)" -ge 25 ]; do sleep 120; done
  else
    n=0; while [ $n -lt 5 ]; do if ok_mem; then n=$((n+1)); else n=0; fi; sleep 60; done
  fi
  log "RETRY after rc=$rc"
done
