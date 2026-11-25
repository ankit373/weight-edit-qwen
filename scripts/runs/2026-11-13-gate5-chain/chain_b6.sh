#!/bin/sh
# B6 chain: every stage of queue_b6.sh in order, each through retry_b6.sh (memory retry). stops on the first failure.
cd "$(dirname "$0")/../.." || exit 1
F=gate5b-workspace/candidates/c06
S=eb3bc15fd70f9257323e35e3895ca07661d6b6c83a5e3c370245eed7fe903bba
D=gate5b-workspace/work/c06/dev.jsonl
W=runs/2026-11-13-gate5-chain/retry_b6.sh
sh $W random $F $S || exit $?
sh $W a $F $S $D || exit $?
sh $W c $F $S || exit $?
sh $W d $F $S 0.03 off || exit $?
sh $W noop 0.03 off || exit $?
sh $W b $F $S || exit $?
sh $W score $F $S 0.03 off || exit $?
echo B6 CHAIN DONE
