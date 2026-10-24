#!/usr/bin/env bash
# M3 acceptance: N consecutive launches reach the main menu loop and stay in
# it without a fatal stop.
#
#   scripts/m3_accept.sh [launches] [seconds]     # defaults: 3, 60
#
# Each launch runs in the background (REFROZEN_TEST_FOCUS=follow activates the
# game's window guest-side, as clicking it would) and saves every 600th
# presented frame to game/attempts/m3-accept-<n>-shots/. A launch passes iff
# its log has no FATAL and no watchdog report (the runtime's watchdog reports
# any 5 s without a presented frame, so none means frames kept coming), it is
# still running at the deadline, and at least one frame was saved. The frame
# rate depends on the host's load and is not a criterion. Exit 0 iff every
# launch passes. The frames are the evidence of what was on screen.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-3}" SECS="${2:-60}"
fail=0
for ((i = 1; i <= N; i++)); do
  shots="$ROOT/game/attempts/m3-accept-$i-shots"
  mkdir -p "$shots"
  find "$shots" -name 'frame_*.bmp' -delete
  line=$(REFROZEN_TEST_FOCUS=follow REFROZEN_SHOT_EVERY=600 REFROZEN_SHOT_DIR="$shots" \
    "$ROOT/scripts/run_attempt.sh" "m3-accept-$i" "$SECS" | head -1)
  log="$ROOT/game/attempts/m3-accept-$i.log"
  fatal=$(grep -c FATAL "$log")
  watchdog=$(grep -c watchdog "$log")
  frames=$(find "$shots" -name 'frame_*.bmp' | wc -l | tr -d ' ')
  alive=no
  [[ "$line" == *"killed at the ${SECS} s deadline"* ]] && alive=yes
  ok=PASS
  if [ "$fatal" != 0 ] || [ "$watchdog" != 0 ] || [ "$alive" != yes ] || [ "$frames" -lt 1 ]; then
    ok=FAIL
    fail=1
  fi
  last=$(find "$shots" -name 'frame_*.bmp' | sort | tail -1)
  echo "launch $i: $ok  fatal=$fatal watchdog=$watchdog alive_at_deadline=$alive frames_saved=$frames last=$(basename "${last:-none}")"
done
exit $fail
