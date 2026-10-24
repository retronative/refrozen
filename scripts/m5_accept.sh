#!/usr/bin/env bash
# M5 acceptance: N consecutive local DotA matches played to the end screen
# (tests/m5/match_path.txt: DotA v6.85oz LoD started from the Custom Game
# screen, a hero by -ar, the Scourge base destroyed, F10 > End Game > Quit
# Mission, the score screen).
#
#   scripts/m5_accept.sh [launches] [seconds]     # defaults: 3, 240
#
# Each launch: a fresh per-user tree on the APFS install clone of
# scripts/m4_accept.sh (with the DotA map in Maps\Download), wave output
# dumped (REFROZEN_AUDIO_DUMP; background runs are silent, SDL's dummy
# driver). Shots: game/attempts/m5-accept-<n>-<time>/shots/<name>.bmp. A
# launch passes iff every shot was saved (the last ones are the score
# screen), the log has no FATAL and no watchdog report, Replay\LastReplay.w3g
# was written by this run with a Warcraft III replay header, and the audio
# dump holds sound (RMS of its 16-bit samples over 100). The victory and the
# score screen are checked on the shots ("won", "score"). Exit 0 iff every
# launch passes.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-3}" SECS="${2:-240}"
SCRIPT="$ROOT/tests/m5/match_path.txt"
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
  run="$ROOT/game/attempts/m5-accept-$i-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$run/xdg" "$run/shots"
  name="$(basename "$run")"
  REFROZEN_GAME_DIR="$INSTALL" XDG_DATA_HOME="$run/xdg" REFROZEN_TEST_FOCUS=follow \
    REFROZEN_TEST_INPUT="$SCRIPT" REFROZEN_SHOT_DIR="$run/shots" REFROZEN_AUDIO_DUMP="$run/audio.pcm" \
    "$ROOT/scripts/run_attempt.sh" "$name" "$SECS" > /dev/null
  log="$ROOT/game/attempts/$name.log"
  fatal=$(grep -c FATAL "$log")
  watchdog=$(grep -c watchdog "$log")
  missing=""
  for s in $shots_wanted; do [ -f "$run/shots/$s.bmp" ] || missing="$missing $s"; done
  replay="$run/xdg/refrozen/install/Replay/LastReplay.w3g"
  replay_ok=no
  if [ -f "$replay" ] && [ "$(head -c 26 "$replay")" = "Warcraft III recorded game" ]; then
    replay_ok="yes($(wc -c < "$replay" | tr -d ' ') B)"
  fi
  rms=$(/opt/homebrew/bin/python3 -I - "$run/audio.pcm" <<'EOF'
import math, os, struct, sys
p = sys.argv[1]
if not os.path.exists(p):
    print(0); sys.exit()
d = open(p, "rb").read()
n = len(d) // 2
s = struct.unpack(f"<{n}h", d[:2 * n]) if n else ()
print(int(math.sqrt(sum(x * x for x in s) / n)) if n else 0)
EOF
)
  ok=PASS
  if [ "$fatal" != 0 ] || [ "$watchdog" != 0 ] || [ -n "$missing" ] || [ "$replay_ok" = no ] ||
     [ "$rms" -le 100 ]; then
    ok=FAIL
    fail=1
  fi
  echo "launch $i: $ok  fatal=$fatal watchdog=$watchdog shots_missing=[${missing# }] replay=$replay_ok audio_rms=$rms run=$name"
done
exit $fail
