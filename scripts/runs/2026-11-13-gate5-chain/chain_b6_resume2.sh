#!/bin/sh
# B6 chain resume 2 (2026-11-19): stage b before noop, since noop needs base mmlu from b. stops on the first failure.
cd "$(dirname "$0")/../.." || exit 1
F=gate5b-workspace/candidates/c06
S=eb3bc15fd70f9257323e35e3895ca07661d6b6c83a5e3c370245eed7fe903bba
D=gate5b-workspace/work/c06/dev.jsonl
W=runs/2026-11-13-gate5-chain/retry_b6.sh
sh $W b $F $S || exit $?
sh $W noop 0.03 off || exit $?
sh $W score $F $S 0.03 off || exit $?
echo B6 CHAIN DONE
