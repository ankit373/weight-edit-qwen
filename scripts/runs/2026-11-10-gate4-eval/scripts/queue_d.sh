#!/bin/sh
# queue D (eval step 5): second sampling seed on test (seed = 100000 + global prompt index).
set -f
. runs/2026-11-10-gate4-eval/scripts/qlib.sh
step base_test_s2 $R/outputs/base_test_s2.jsonl $SB $G -I -B $S/generate.py --ids splits/test.txt --out $R/outputs/base_test_s2.jsonl --method none --seed $SEED2
step final_test_s2 $R/outputs/final_test_s2.jsonl $SB $G -I -B $R/scripts/gen_diff.py --entry generate --diff $FINAL --expect-diff-sha $FSHA --ids splits/test.txt --out $R/outputs/final_test_s2.jsonl --method none --seed $SEED2
step recover_a0.03_on_test_s2 $R/outputs/recover_a0.03_on_test_s2.jsonl $SB $G -I -B $G3/scripts/gen_recover_dev.py --ids splits/test.txt --out $R/outputs/recover_a0.03_on_test_s2.jsonl --method recover --vectors $V --alpha 0.03 --restore-norm --seed $SEED2
step instr_end_test_s2_changed $R/outputs/instr_end_test_s2_changed.jsonl $SB $G -I -B $G3/scripts/gen_variant.py --variants $G3/prompts/instr_end.jsonl --kind instr_end --ids $G3/ids/instr_end_changed_test.txt --out $R/outputs/instr_end_test_s2_changed.jsonl --method none --seed $SEED2
echo "QUEUE_D DONE $(date -u +%FT%TZ)" >> $R/logs/steps.log
