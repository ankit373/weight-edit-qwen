#!/bin/sh
# run one gpu step under caffeinate -i -d -m -s; every 30 s check battery, sleep, slow prompts, swap.
# based on runs/2026-11-08-side-mmlu-redux/scripts/run_watch.sh; battery rule from the eval brief.
# usage (project root): run_watch.sh <name> <log> <cmd...>
# exit 3 = battery < 15% (any charge state), 4 = 10 prompts in a row over 60 s,
# 5 = swap free < 256 MB, 6 = sleep/wake entry in pmset -g log after start, 7 = memory rule; else the job exit code.
R=runs/2026-11-10-gate4-eval; name=$1; log=$2; shift 2
W=$R/logs/watch_$name.log
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
batt() { /usr/bin/pmset -g batt | tr '\n' ' ' | sed 's/  */ /g'; }
n_sleep() { /usr/bin/pmset -g log | grep -cE "^20[0-9-]+ [0-9:]+ [+-][0-9]+ (Sleep|Wake|DarkWake) "; }
if [ "$(pct)" -lt 15 ]; then echo "NOSTART $name battery<15% $(date -u +%FT%TZ) $(batt)" >> $R/logs/steps.log; exit 3; fi
s0=$(n_sleep)
echo "START $name $(date -u +%FT%TZ) $(batt) | $(sysctl -n vm.swapusage)" >> $R/logs/steps.log
/usr/bin/caffeinate -i -d -m -s "$@" >> "$log" 2>&1 &
pid=$!
rc=""; tick=0
while kill -0 $pid 2>/dev/null; do
  sleep 30; tick=$((tick+1))
  [ "$(pct)" -lt 15 ] && { rc=3; break; }
  [ "$(n_sleep)" -gt "$s0" ] && { rc=6; break; }
  slow=$(grep -E '^[0-9]+/[0-9]+ .* [0-9.]+s$' "$log" | tail -10 | awk '{t=$NF; sub("s","",t); if (t+0>60) c++} END{print c+0}')
  n=$(grep -cE '^[0-9]+/[0-9]+ ' "$log")
  [ "$slow" -ge 10 ] && { rc=4; break; }
  swap=$(sysctl -n vm.swapusage)
  free=$(echo "$swap" | sed -E 's/.*free = ([0-9.]+)M.*/\1/')
  line="$(date -u +%FT%TZ) done=$n $swap"
  [ $((tick % 20)) -eq 0 ] && line="$line | $(batt)"  # battery line every ~10 min
  echo "$line" >> $W
  used=$(echo "$swap" | sed -E 's/.*used = ([0-9.]+)M.*/\1/')
  mfree=$(memory_pressure | awk -F': ' '/free percentage/ {gsub("%","",$2); print $2}')
  # memory rule (2026-11-10 13:5xZ, main): swap free < 256 MB, swap used > 18 GB, or memory free < 15%
  awk -v f="$free" -v u="$used" -v m="$mfree" \
    'BEGIN{exit !(f+0 < 256 || u+0 > 18432 || (m != "" && m+0 < 15))}' && {
    echo "MEM_STOP $(date -u +%FT%TZ) swap_free=${free}M swap_used=${used}M mem_free=${mfree}%" >> $R/logs/steps.log
    rc=5; break; }
  # memory rule (added at the 2nd resume): swap free < 1024 MB or memory_pressure free < 15% -> stop, hold
  mp=$(memory_pressure | awk -F': ' '/free percentage/ {gsub("%","",$2); print $2+0}')
  awk -v f="$free" -v m="$mp" 'BEGIN{exit !(f+0 < 1024 || m+0 < 15)}' && {
    echo "MEMSTOP $name swap_free=${free}M mem_free=${mp}% $(date -u +%FT%TZ)" >> $R/logs/steps.log; rc=7; break; }
done
if [ -n "$rc" ]; then
  pkill -INT -P $pid; sleep 5; pkill -TERM -P $pid; kill $pid 2>/dev/null
  echo "STOP $name rc=$rc $(date -u +%FT%TZ) $(batt)" >> $R/logs/steps.log
  [ "$rc" = 6 ] && /usr/bin/pmset -g log | grep -E "^20[0-9-]+ [0-9:]+ [+-][0-9]+ (Sleep|Wake|DarkWake) " | tail -5 >> $R/logs/steps.log
  exit $rc
fi
wait $pid; rc=$?
echo "END $name exit=$rc $(date -u +%FT%TZ) $(batt)" >> $R/logs/steps.log
exit $rc
