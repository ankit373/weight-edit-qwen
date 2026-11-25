#!/bin/sh
# run a command with a clean env, hub offline, network + secret dirs denied (envs/sandbox.sb).
here=$(cd "$(dirname "$0")" && pwd)
exec env -i \
  HOME="$HOME" PATH=/usr/bin:/bin \
  HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1 \
  TMPDIR="$here/tmp" PYTHONHASHSEED=0 TOKENIZERS_PARALLELISM=false \
  sandbox-exec -f "$here/sandbox.sb" "$@"
