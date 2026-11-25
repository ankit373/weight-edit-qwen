#!/bin/sh
# no charger today (user, 2026-11-22): stop the side-check queue at <=40% battery on battery power, so the user keeps charge. rows are resumable.
cd "$(dirname "$0")/../../.." || exit 1
L=runs/2026-11-22-partc-08b-side/logs/steps.log
while :; do
  b=$(pmset -g batt | tail -1)
  pct=$(echo "$b" | grep -o '[0-9]*%' | tr -d %)
  if echo "$b" | grep -q discharging && [ "$pct" -le 40 ]; then
    echo "PAUSE manual: battery ${pct}%, no charger (user 2026-11-22), queue stopped by pause_at_40.sh $(date -u +%FT%TZ)" >> $L
    pkill -f "partc-08b-side/scripts/retry.sh"; pkill -f "partc-08b-side/scripts/queue_side.sh"
    pkill -f "run_watch.sh runs/2026-11-22-partc-08b-side"; pkill -f "gen_diff.py --diff gate5-workspace"
    sleep 5; ps -eo pid,command | grep -E "partc-08b-side|gen_diff" | grep -v grep
    echo "paused at ${pct}%"; exit 0
  fi
  pgrep -f "partc-08b-side/scripts/retry.sh" >/dev/null || { echo "queue ended on its own"; exit 0; }
  sleep 60
done
