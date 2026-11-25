#!/bin/sh
# runs/2026-11-13-gate5-chain/retry_b4.sh pattern around queue_side.sh.
# rc 5 (memory): wait for swap used < 12 GB and mem free >= 30% for 5 min, retry. rc 3 (battery): wait for >= 25%, retry. max 6.
cd "$(dirname "$0")/../../.." || exit 1
L=runs/2026-11-22-partc-08b-side/logs/chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
ok_mem() { u=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6); print $6}'); m=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}'); [ "${u%.*}" -lt 12288 ] && [ "$m" -ge 30 ]; }
t=0
while :; do
  log "START queue_side.sh (retry try $t)"
  sh runs/2026-11-22-partc-08b-side/scripts/queue_side.sh >> $L 2>&1; rc=$?
  log "END rc=$rc queue_side.sh (retry try $t)"
  { [ $rc -eq 5 ] || [ $rc -eq 3 ]; } && [ $t -lt 6 ] || exit $rc
  t=$((t+1))
  if [ $rc -eq 3 ]; then
    until [ "$(pct)" -ge 25 ]; do sleep 120; done
  else
    n=0; while [ $n -lt 5 ]; do if ok_mem; then n=$((n+1)); else n=0; fi; sleep 60; done
  fi
  log "RETRY after rc=$rc"
done
