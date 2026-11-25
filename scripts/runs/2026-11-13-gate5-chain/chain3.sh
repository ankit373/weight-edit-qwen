#!/bin/sh
# resume after the B1 memory stop (2026-11-13T08:21Z): waits until swap used < 17 GB and memory free >= 25%
# for 5 minutes in a row, then B1 full (resumes by id), D12, B2 cpu, B2 lens, B3, B4 vectors, B4 screen.
cd "$(dirname "$0")/../.." || exit 1
L=runs/2026-11-13-gate5-chain/chain.log
S=runs/2026-11-11-gate5b-scripts/scripts
log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
ok_mem() { u=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6); print $6}'); m=$(memory_pressure | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}'); [ "${u%.*}" -lt 14336 ] && [ "$m" -ge 25 ]; }
run() { log "START $*"; "$@" >> $L 2>&1; rc=$?; log "END rc=$rc $*"; [ $rc -eq 0 ] || { log "CHAIN STOP"; exit $rc; }; }
log "chain3 start; waiting for swap < 14 GB and mem free >= 25% for 5 min"
n=0; while [ $n -lt 5 ]; do if ok_mem; then n=$((n+1)); else n=0; fi; sleep 60; done
run sh $S/queue_b1.sh full
d12=$(grep "D12" runs/*-gate5b-baseline/logs/steps.log | tail -1); log "$d12"
case "$d12" in *STOP*) log "D12 says STOP part B; chain ends"; exit 0;; esac
run sh $S/queue_b2.sh cpu
run sh $S/queue_b2.sh lens
run sh $S/queue_b3.sh
run sh $S/queue_b4.sh vectors
run sh $S/queue_b4.sh screen
log "chain3 done; next is the B4 dev hand-pick (main)"
