#!/bin/sh
# keeps the gpu busy without waiting on main: ws3 eval -> B1 full -> D12 -> B2 -> B3 -> B4 vectors + screen.
# stops on any failure, on D12 STOP, or before the B4 hand-pick step. run from the project root.
cd "$(dirname "$0")/../.." || exit 1
L=runs/2026-11-13-gate5-chain/chain.log
S=runs/2026-11-11-gate5b-scripts/scripts
log() { echo "$(date -u +%FT%TZ) $*" >> $L; }
busy() { pgrep -f "envs/gen/bin/python" > /dev/null; }
run() { log "START $*"; "$@" >> $L 2>&1; rc=$?; log "END rc=$rc $*"; [ $rc -eq 0 ] || { log "CHAIN STOP"; exit $rc; }; }

log "chain start; waiting for gate5-workspace-3/FINAL.md"
while [ ! -f gate5-workspace-3/FINAL.md ]; do sleep 120; done
n=0; while [ $n -lt 3 ]; do if busy; then n=0; else n=$((n+1)); fi; sleep 60; done  # 3 free minutes in a row
set -- $(/usr/bin/python3 -I -B -c "
import re; t=open('gate5-workspace-3/FINAL.md').read()
c=re.search(r'candidates/([A-Za-z0-9_.\-]+)', t).group(1)
s=re.search(r'diff_file_sha256.*?\b([0-9a-f]{64})\b', t, re.S).group(1)
print(c, s)") || { log "parse FINAL.md failed"; exit 1; }
log "ws3 frozen: $1 $2"
R3=runs/$(date -u +%F)-gate5a-eval-ws3; mkdir -p $R3/logs
run sh runs/2026-11-11-gate5a-eval-prep/scripts/queue_eval.sh gate5-workspace-3 gate5-workspace-3/candidates/$1 $2 $R3

run sh $S/queue_b1.sh full
d12=$(grep "D12" runs/*-gate5b-baseline/logs/steps.log | tail -1); log "$d12"
case "$d12" in *STOP*) log "D12 says STOP part B; chain ends"; exit 0;; esac
run sh $S/queue_b2.sh cpu
run sh $S/queue_b2.sh lens
run sh $S/queue_b3.sh
run sh $S/queue_b4.sh vectors
run sh $S/queue_b4.sh screen
log "chain done; next is the B4 dev hand-pick (main)"
