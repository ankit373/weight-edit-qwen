#!/bin/sh
# PROTOCOL.md section 6 step 0, cpu only, no model: env freeze + lock sha256 equal to part B,
# sandbox probes (no outside network call), every prompt-set sha256, input files present.
# usage (project root): precheck_c.sh <run_dir>     exit 1 on any failure
R=$1; [ -n "$R" ] || { echo "usage: precheck_c.sh <run_dir>" >&2; exit 2; }
mkdir -p "$R/env" "$R/security"
SB=envs/run-sandboxed.sh; G=envs/gen/bin/python; P=envs/score/bin/python
Y=runs/2026-11-22-partc-scripts/scripts
REF=runs/2026-11-10-gate4-eval/env              # freeze files part A / part B evals were checked against
LOCKREF=runs/2026-11-13-gate5a-eval-ws3/env/lock_sha256.txt
UV=${UV:-$HOME/.local/bin/uv}
bad=0
fail() { echo "FAIL $*"; bad=1; }

"$UV" pip freeze --python $G > "$R/env/freeze-gen.txt" 2> "$R/env/freeze.stderr" || fail "uv freeze gen"
"$UV" pip freeze --python $P > "$R/env/freeze-score.txt" 2>> "$R/env/freeze.stderr" || fail "uv freeze score"
cmp -s "$R/env/freeze-gen.txt" "$REF/freeze-gen.txt" && echo "ok freeze-gen = $REF" || fail "freeze-gen differs from $REF"
cmp -s "$R/env/freeze-score.txt" "$REF/freeze-score.txt" && echo "ok freeze-score = $REF" || fail "freeze-score differs from $REF"
: > "$R/env/lock_sha256.txt"
for f in gen.lock.txt score.lock.txt score-build.lock.txt; do
  got=$(shasum -a 256 envs/lock/$f | cut -d' ' -f1)
  want=$(awk -v f=$f '$1==f {print $2}' $LOCKREF)
  echo "$f $got want $want" >> "$R/env/lock_sha256.txt"
  [ "$got" = "$want" ] && echo "ok lock $f" || fail "lock $f $got != $want"
done
{ /usr/sbin/sysctl -n hw.model machdep.cpu.brand_string hw.memsize; sw_vers; } > "$R/env/hardware.txt" 2>&1

# sandbox: network and secret dirs must be denied inside envs/run-sandboxed.sh
{
  echo "# sandbox probes $(date -u +%FT%TZ) (inside the sandbox only)"
  $SB /usr/bin/curl -sS -m 10 -o /dev/null https://huggingface.co >/dev/null 2>&1 && echo "curl huggingface.co: ALLOWED" || echo "curl huggingface.co: blocked"
  $SB $G -I -c "import urllib.request; urllib.request.urlopen('https://pypi.org', timeout=10)" >/dev/null 2>&1 \
    && echo "python urlopen pypi.org: ALLOWED" || echo "python urlopen pypi.org: blocked"
  for d in .ssh .aws .config .gnupg; do
    $SB /bin/ls "$HOME/$d" >/dev/null 2>&1 && echo "ls ~/$d: ALLOWED" || echo "ls ~/$d: blocked or absent"
  done
} > "$R/security/sandbox-check.txt"
grep -q ALLOWED "$R/security/sandbox-check.txt" && fail "sandbox lets something through (security/sandbox-check.txt)" || echo "ok sandbox"

$SB $P -I -B $Y/check_sets.py --out "$R/env/prompt_sets_sha256.json" || fail "prompt-set sha256"
for f in runs/2026-11-06-gate3-run/recover/vectors.safetensors runs/2026-11-14-gate5b-recover/recover/vectors.safetensors \
         runs/2026-11-06-gate3-run/prompts/instr_end.jsonl runs/2026-11-06-gate3-run/ids/instr_end_changed_test.txt; do
  [ -f "$f" ] && echo "ok $f $(shasum -a 256 $f | cut -d' ' -f1)" || fail "missing $f"
done
exit $bad
