#!/bin/sh
# gate 4 queue B (mono 2400 + mmlu-redux 5330) on the three part A 0.8B edits, h5 first.
# gen: gate 4 eval gen_diff.py (has the mmlu entry). watch + step: gate 5a eval-prep qlib.sh / run_watch.sh.
# run from the project root. done steps are skipped; partial rows resume by id.
set -f
if [ -z "$PC_CAFF" ]; then exec /usr/bin/caffeinate -i -d -m -s /usr/bin/env PC_CAFF=1 /bin/sh "$0" "$@"; fi
[ -f PROTOCOL.md ] || { echo "run from the project root" >&2; exit 2; }
R=runs/2026-11-22-partc-08b-side
. runs/2026-11-11-gate5a-eval-prep/scripts/qlib.sh
MM=runs/2026-11-08-side-mmlu-redux
GD4=runs/2026-11-10-gate4-eval/scripts/gen_diff.py
REL=runs/2026-11-12-gate5-release/hf-models
NMONO=$(grep -c . $G3/ids/mono_all.txt); NMMLU=$(grep -c . $MM/ids/all_ok.txt)

# edit -> workspace and diff_file_sha256 (from each FINAL.md)
ws_of() { case $1 in h5_a2_n5) echo gate5-workspace-1;; mix21_22b0.75_23b0.5) echo gate5-workspace-2;;
  combo_a14_b14) echo gate5-workspace-3;; esac; }
sha_of() { case $1 in h5_a2_n5) echo bd4e68b981c939b5bec42b6d103651ddd1309030e44fed5e6a5a0eb772bfa41e;;
  mix21_22b0.75_23b0.5) echo d78e7b1bc77a5969c7bc260950bcda4a19c1b7872c47c09e790dfca0b1e7758d;;
  combo_a14_b14) echo b86d058a80f35a6747748028179e6c227909436322a435dccf228b921e050f1f;; esac; }

log "QUEUE start"
for en in h5_a2_n5 mix21_22b0.75_23b0.5 combo_a14_b14; do
  WS=$(ws_of $en); sha=$(sha_of $en); D=$WS/candidates/$en
  $SB $G -I -B $X/check_frozen.py $D $sha $R/evidence/frozen_${en}_$(date -u +%Y%m%dT%H%M%SZ).json \
    || { log "HALT queue: frozen check failed for $D"; exit 2; }
  rs=$(shasum -a 256 $REL/$en/diff.safetensors | cut -d' ' -f1)
  [ "$rs" = "$sha" ] || { log "HALT queue: release copy sha $rs != $sha"; exit 2; }
  GD="$SB $G -I -B $GD4 --diff $D --expect-diff-sha $sha"
  o=$R/outputs/${en}_mono.jsonl
  step ${en}_mono $o $NMONO $GD --entry generate --ids $G3/ids/mono_all.txt --out $o --method none
  o=$R/outputs/${en}_mmlu.jsonl
  step ${en}_mmlu $o $NMMLU $GD --entry mmlu --items $MM/data/items_ok.jsonl --ids $MM/ids/all_ok.txt --out $o --method none
done
log "QUEUE DONE"
