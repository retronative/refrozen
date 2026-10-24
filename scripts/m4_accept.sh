#!/usr/bin/env bash
# M4 acceptance: N consecutive launches walk the menus with mouse and
# keyboard (tests/m4/native_path.txt: main menu, a new profile, Single
# Player, Custom Game with the DotA map selected, Options/Video, focus loss
# and return, minimize and restore) and quit from the menu.
#
#   scripts/m4_accept.sh [launches] [seconds]     # defaults: 3, 110
#
# Each launch starts from a fresh per-user tree (XDG_DATA_HOME: registry,
# drive C, the install overlay where profiles go) on an APFS clone of
# game/native-install with the DotA map in Maps\Download (made once, as
# game/attempts/m4-accept-install; the map comes from the oracle install).
# Shots: game/attempts/m4-accept-<n>-<time>/shots/<name>.bmp, one per
# "shot" line. A launch passes iff every shot was saved, the log has no
# FATAL and no watchdog report, and the process ended by itself (the Quit
# button) with status 0 before the deadline. Exit 0 iff every launch passes.
# The comparison with the Wine oracle is scripts/m4_compare.sh.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-3}" SECS="${2:-110}"
SCRIPT="$ROOT/tests/m4/native_path.txt"
INSTALL="$ROOT/game/attempts/m4-accept-install"
MAP="DotA v6.85oz LoD.w3x"
if [ ! -d "$INSTALL" ]; then
  cp -cR "$ROOT/game/native-install" "$INSTALL"
  mkdir -p "$INSTALL/Maps/Download"
  cp -c "$ROOT/game/wine-oracle/Maps/Download/$MAP" "$INSTALL/Maps/Download/"
fi
shots_wanted=$(awk '$2 == "shot" {print $3}' "$SCRIPT")
fail=0
for ((i = 1; i <= N; i++)); do
  run="$ROOT/game/attempts/m4-accept-$i-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$run/xdg" "$run/shots"
  name="$(basename "$run")"
  line=$(REFROZEN_GAME_DIR="$INSTALL" XDG_DATA_HOME="$run/xdg" REFROZEN_TEST_FOCUS=follow \
    REFROZEN_TEST_INPUT="$SCRIPT" REFROZEN_SHOT_DIR="$run/shots" \
    "$ROOT/scripts/run_attempt.sh" "$name" "$SECS" | head -1)
  log="$ROOT/game/attempts/$name.log"
  fatal=$(grep -c FATAL "$log")
  watchdog=$(grep -c watchdog "$log")
  missing=""
  for s in $shots_wanted; do [ -f "$run/shots/$s.bmp" ] || missing="$missing $s"; done
  quit=no
  [[ "$line" == *": exit 0;"* ]] && quit=yes
  ok=PASS
  if [ "$fatal" != 0 ] || [ "$watchdog" != 0 ] || [ "$quit" != yes ] || [ -n "$missing" ]; then
    ok=FAIL
    fail=1
  fi
  echo "launch $i: $ok  fatal=$fatal watchdog=$watchdog quit_exit0=$quit shots_missing=[${missing# }] run=$name"
done
exit $fail
