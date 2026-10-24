#!/usr/bin/env bash
# One launch of the recompiled game with a hard deadline, its log saved.
#
#   scripts/run_attempt.sh <name> [seconds] [game arguments...]   # default 30 s
#
# Runs build/main/refrozen (REFROZEN_BACKGROUND=1, REFROZEN_TRACE if set in the
# environment), writes game/attempts/<name>.log, and reports whether GameMain was
# reached (the config/game.manifest probe), the first fatal stop, and the exit
# status. Exit 0 iff GameMain was reached.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$1"; SECS="${2:-30}"; shift; [ $# -gt 0 ] && shift
LOG="$ROOT/game/attempts/$NAME.log"
mkdir -p "$ROOT/game/attempts"

REFROZEN_BACKGROUND=1 "$ROOT/build/main/refrozen" "$@" > "$LOG" 2>&1 &
pid=$!
status=timeout
for ((i = 0; i < SECS * 10; i++)); do
  if ! kill -0 "$pid" 2>/dev/null; then
    wait "$pid"; status="exit $?"
    break
  fi
  sleep 0.1
done
if [ "$status" = timeout ]; then
  kill -9 "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  status="killed at the ${SECS} s deadline"
fi
echo "$NAME: $status; log $LOG ($(wc -l < "$LOG" | tr -d ' ') lines)"
grep -m1 "probe: GameMain" "$LOG" && reached=1 || { echo "GameMain: not reached"; reached=0; }
grep -m1 -iE "fatal|unimplemented import|indirect branch" "$LOG" || true
[ "$reached" = 1 ]
