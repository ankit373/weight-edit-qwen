#!/bin/sh
# run one gpu step under caffeinate -i -d -m -s; every 30 s check battery, sleep/wake, slow prompts,
# memory. part B copy of gate 4 eval run_watch.sh with the D10 rules (plan status line):
#   battery < 20% in any charge state -> stop (rc 3); the queue restarts the step at >= 25%
#   memory_pressure free < 15% or swap used > 18 GB -> stop (rc 5); gate 4's swap free < 256 MB kept too
#   sleep/wake entry in pmset -g log after start -> stop (rc 6); the queue resumes by id
#   10 prompts in a row over 60 s -> stop (rc 4)
# usage (project root): run_watch.sh <run_dir> <name> <log> <cmd...>
R=$1; name=$2; log=$3; shift 3
W=$R/logs/watch_$name.log
pct() { /usr/bin/pmset -g batt | grep -oE '[0-9]+%' | head -1 | tr -d '%'; }
batt() { /usr/bin/pmset -g batt | tr '\n' ' ' | sed 's/  */ /g'; }
n_sleep() { /usr/bin/pmset -g log | grep -cE "^20[0-9-]+ [0-9:]+ [+-][0-9]+ (Sleep|Wake|DarkWake) "; }
mem_free() { /usr/bin/memory_pressure | awk -F': ' '/free percentage/ {gsub("%","",$2); print $2+0}'; }
swap_used() { /usr/sbin/sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/'; }
swap_free() { /usr/sbin/sysctl -n vm.swapusage | sed -E 's/.*free = ([0-9.]+)M.*/\1/'; }
# D10 (mem free < 15%, swap used > 18 GB) + gate 4's swap free < 256 MB (D10 replaced only the 1 GB clause)
mem_bad() { awk -v m="$(mem_free)" -v u="$(swap_used)" -v f="$(swap_free)" \
  'BEGIN{exit !((m != "" && m+0 < 15) || u+0 > 18432 || f+0 < 256)}'; }
if [ "$(pct)" -lt 20 ]; then echo "NOSTART $name battery<20% $(date -u +%FT%TZ) $(batt)" >> $R/logs/steps.log; exit 3; fi
if mem_bad; then echo "NOSTART $name memory mem_free=$(mem_free)% swap_used=$(swap_used)M swap_free=$(swap_free)M $(date -u +%FT%TZ)" >> $R/logs/steps.log; exit 5; fi
s0=$(n_sleep)
echo "START $name $(date -u +%FT%TZ) $(batt) | $(/usr/sbin/sysctl -n vm.swapusage) | mem_free=$(mem_free)%" >> $R/logs/steps.log
/usr/bin/caffeinate -i -d -m -s "$@" >> "$log" 2>&1 &
pid=$!
rc=""; tick=0
while kill -0 $pid 2>/dev/null; do
  sleep 30; tick=$((tick+1))
  [ "$(pct)" -lt 20 ] && { rc=3; break; }
  [ "$(n_sleep)" -gt "$s0" ] && { rc=6; break; }
  slow=$(grep -E '^[0-9]+/[0-9]+ .* [0-9.]+s$' "$log" | tail -10 | awk '{t=$NF; sub("s","",t); if (t+0>60) c++} END{print c+0}')
  n=$(grep -cE '^[0-9]+/[0-9]+ ' "$log")
  [ "$slow" -ge 10 ] && { rc=4; break; }
  mf=$(mem_free); su=$(swap_used); sf=$(swap_free)
  line="$(date -u +%FT%TZ) done=$n mem_free=${mf}% swap_used=${su}M swap_free=${sf}M"
  [ $((tick % 20)) -eq 0 ] && line="$line | $(batt)"  # battery line every ~10 min
  echo "$line" >> $W
  if mem_bad; then
    echo "MEM_STOP $name $(date -u +%FT%TZ) mem_free=${mf}% swap_used=${su}M swap_free=${sf}M" >> $R/logs/steps.log
    rc=5; break
  fi
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
