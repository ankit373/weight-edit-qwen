#!/bin/sh
# rerun queue_b4.sh <stage args>; on a memory stop (rc 5) wait for swap < 12 GB and mem free >= 30% for 5 min, retry (max 6).
cd "$(dirname "$0")/../.." || exit 1
L=runs/2026-11-13-gate5-chain/chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
ok_mem() { u=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6); print $6}'); m=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}'); [ "${u%.*}" -lt 12288 ] && [ "$m" -ge 30 ]; }
t=0
while :; do
  log "START queue_b4.sh $* (retry_b4 try $t)"
  sh runs/2026-11-11-gate5b-scripts/scripts/queue_b4.sh "$@" >> $L 2>&1; rc=$?
  log "END rc=$rc queue_b4.sh $* (retry_b4 try $t)"
  [ $rc -eq 5 ] && [ $t -lt 6 ] || exit $rc
  t=$((t+1)); n=0
  while [ $n -lt 5 ]; do if ok_mem; then n=$((n+1)); else n=0; fi; sleep 60; done
done
