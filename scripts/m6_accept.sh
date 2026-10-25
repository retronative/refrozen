#!/usr/bin/env bash
# M6 acceptance: N consecutive full DotA matches decided by the map's computer
# players, each a session of 60+ minutes in the match.
#
#   REFROZEN_M6_MAP=<map.w3x> scripts/m6_accept.sh [launches] [minutes]   # defaults: 3, 65
#
# The map lives outside the repository (default: "DotA v6.83dAI PMV 1.42
# EN.w3x" beside it, in ../DOTA); it is copied (APFS clone) into
# Maps\Download of an install clone holding only that map. Each launch: a
# fresh profile, M4's menus to the map, the nine other lobby slots set to
# Computer (Normal) with the slot menus, Start Game, any key, "-ar" (every
# player gets a random hero). The player's own hero is never ordered (it
# stays at the fountain): the bots of both teams decide the match, no
# cheat. After <minutes> in the match: F10 > End Game > Quit Mission, the
# score screen. Frame pacing (REFROZEN_FPS_REPORT=60) and the process's
# resident memory (ps, every 60 s) are logged for the whole session.
#
# Periodic shots (every 15 s in the match) are read with macOS's Vision OCR
# (scripts/ocr_text.swift) as they are saved, kept as small JPEGs and their
# BMPs removed (disk); named shots stay BMPs.
# Evidence: game/attempts/m6-accept-<n>-<time>/{shots,ocr.txt,rss.txt}.
#
# A launch passes iff:
#   - the log has no FATAL and no watchdog report, and every shot was saved;
#   - a periodic shot shows the victory announcement ("has won"), i.e. the
#     match ended by a destroyed throne before Quit Mission;
#   - the score screen's Overview lists all 10 players (rows after the column
#     headers), and its elapsed time is recorded;
#   - pacing, over the match after its first 5 minutes: every report's median
#     frame interval at most 20 ms (50 fps), and the median of the last 10
#     reports at most 15 % above that of minutes 5-15 (no drift);
#   - memory: the largest RSS of the last 15 minutes at most 20 % above the
#     RSS at minute 15 of the match (no unbounded growth);
#   - Replay\LastReplay.w3g written with a Warcraft III replay header.
# Exit 0 iff every launch passes.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-3}" MIN="${2:-65}"
MAP="${REFROZEN_M6_MAP:-$ROOT/../DOTA/DotA v6.83dAI PMV 1.42 EN.w3x}"
INSTALL="$ROOT/game/attempts/m6-install"
OCR="$ROOT/build/oracle_keys/ocr_text"
PY=/opt/homebrew/bin/python3
[ -f "$MAP" ] || { echo "map not found: $MAP (set REFROZEN_M6_MAP)" >&2; exit 2; }
if [ ! -d "$INSTALL" ]; then
  cp -cR "$ROOT/game/native-install" "$INSTALL"
  mkdir -p "$INSTALL/Maps/Download"
  cp -c "$MAP" "$INSTALL/Maps/Download/"
fi
if [ ! -x "$OCR" ] || [ "$ROOT/scripts/ocr_text.swift" -nt "$OCR" ]; then
  mkdir -p "$(dirname "$OCR")"
  swiftc -O -o "$OCR" "$ROOT/scripts/ocr_text.swift" || exit 2
fi

# The match script: M5's menus (tests/m5/match_path.txt) up to the map, the
# slots, then the timed part (match start M0 = 112 s since the first event
# pump; the loading screen waits for a key from about 100 s).
M0=112
END=$((M0 + MIN * 60))
script() {
  sed -n '/^12 shot main/,/^45 shot dota/p' "$ROOT/tests/m5/match_path.txt"
  "$PY" -I - "$M0" "$END" <<'EOF'
import sys
m0, end = int(sys.argv[1]), int(sys.argv[2])
# Lobby slots 2-5 (Sentinel) and 6-10 (Scourge): each slot's menu at
# (128, y), "Computer (Normal)" 70 points below it.
t = 47.0
for y in (236, 261, 286, 311, 350, 375, 400, 425, 450):
    print(f"{t:.1f} goto 128 {y}\n{t + 0.6:.1f} click\n{t + 1.4:.1f} goto 128 {y + 70}\n{t + 2.0:.1f} click")
    t += 3
print(f"{t:.1f} shot slots")
print(f"{t + 1:.1f} goto 688 492\n{t + 2.5:.1f} click")       # Start Game
print("100 shot loaded\n105 key Space")
t = 106.0
for k in ("Return", "-", "A", "R", "Return"):
    print(f"{t:.1f} key {k}")
    t += 0.3
print(f"{m0} shot match_start")
for i, s in enumerate(range(m0 + 15, end, 15)):
    print(f"{s} shot m{i:04d}")
print(f"{end} shot match_end\n{end + 2} key F10\n{end + 5} shot menu\n{end + 6} key E")
print(f"{end + 9} shot endgame\n{end + 10} key Q\n{end + 25} shot score\n{end + 40} shot score2")
EOF
}

fail=0
for ((i = 1; i <= N; i++)); do
  run="$ROOT/game/attempts/m6-accept-$i-$(date +%Y%m%d-%H%M%S)"
  name="$(basename "$run")"
  mkdir -p "$run/xdg" "$run/shots"
  script > "$run/match.txt"
  shots_wanted=$(awk '$2 == "shot" {print $3}' "$run/match.txt")
  REFROZEN_GAME_DIR="$INSTALL" XDG_DATA_HOME="$run/xdg" REFROZEN_TEST_FOCUS=follow \
    REFROZEN_TEST_INPUT="$run/match.txt" REFROZEN_SHOT_DIR="$run/shots" REFROZEN_FPS_REPORT=60 \
    "$ROOT/scripts/run_attempt.sh" "$name" $((END + 60)) > /dev/null &
  runner=$!
  t0=$SECONDS
  : > "$run/ocr.txt"
  : > "$run/rss.txt"
  next_rss=0
  # While it runs: memory every 60 s; periodic shots read, compacted.
  while kill -0 "$runner" 2>/dev/null; do
    if [ $((SECONDS - t0)) -ge "$next_rss" ]; then
      pid=$(pgrep -n -f "$ROOT/build/main/refrozen" || true)
      [ -n "$pid" ] && echo "$((SECONDS - t0)) $(ps -o rss= -p "$pid" | tr -d ' ')" >> "$run/rss.txt"
      next_rss=$((next_rss + 60))
    fi
    for b in "$run"/shots/m[0-9]*.bmp; do
      [ -e "$b" ] || continue
      [ $(($(date +%s) - $(stat -f %m "$b"))) -ge 2 ] || continue
      "$OCR" "$b" | sed "s|^|$(basename "$b" .bmp): |" >> "$run/ocr.txt"
      sips -s format jpeg -Z 400 "$b" --out "${b%.bmp}.jpg" > /dev/null && rm "$b"
    done
    sleep 2
  done
  wait "$runner"
  for b in "$run"/shots/m[0-9]*.bmp; do
    [ -e "$b" ] || continue
    "$OCR" "$b" | sed "s|^|$(basename "$b" .bmp): |" >> "$run/ocr.txt"
    sips -s format jpeg -Z 400 "$b" --out "${b%.bmp}.jpg" > /dev/null && rm "$b"
  done
  for s in score score2; do
    [ -f "$run/shots/$s.bmp" ] && "$OCR" "$run/shots/$s.bmp" | sed "s|^|$s: |" >> "$run/ocr.txt"
  done

  log="$ROOT/game/attempts/$name.log"
  fatal=$(grep -c FATAL "$log")
  watchdog=$(grep -c watchdog "$log")
  missing=""
  for s in $shots_wanted; do
    [ -f "$run/shots/$s.bmp" ] || [ -f "$run/shots/$s.jpg" ] || missing="$missing $s"
  done
  replay="$run/xdg/refrozen/install/Replay/LastReplay.w3g"
  replay_ok=no
  if [ -f "$replay" ] && [ "$(head -c 26 "$replay")" = "Warcraft III recorded game" ]; then
    replay_ok="yes($(wc -c < "$replay" | tr -d ' ') B)"
  fi
  verdict=$("$PY" -I - "$log" "$run/ocr.txt" "$run/rss.txt" "$M0" "$END" <<'EOF'
import re, sys
log, ocr, rss, m0, end = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
bad = []
lines = open(ocr, errors="replace").read().splitlines()
won = [l for l in lines if re.match(r"m\d{4}: ", l) and "has won" in l]
if not won:
    bad.append("no victory announcement")
first_won = won[0].split(":")[0] if won else "-"
team = next((t for t in ("Sentinel", "Scourge") for l in won if t in l), "?")
score = [l.split(": ", 1)[1] for l in lines if l.startswith("score: ")]
# The Overview lists one row per player after the column headers, then the
# numbers; only the player's own row names its hero.
rows = score[score.index("Total Score") + 1:] if "Total Score" in score else []
players = []
for s in rows:
    if re.fullmatch(r"[\d ,.]+", s):
        break
    if len(re.findall(r"[A-Za-z]", s)) >= 3:
        players.append(s)
elapsed = next((s.split(":", 1)[1].strip() for s in score if s.startswith("Elapsed Time")), "?")
if len(players) < 10:
    bad.append(f"score screen lists {len(players)} players")
# fps reports: t is seconds since the first frame, close to the input clock.
reps = [(float(t), float(med)) for t, med in
        re.findall(r"fps: [\d.]+ at t=([\d.]+) s \(interval ms: min [\d.]+ p1 [\d.]+ median ([\d.]+)", open(log, errors="replace").read())]
match = [(t, m) for t, m in reps if m0 + 300 <= t <= end]
slow = [f"{m:.1f}@{t:.0f}" for t, m in match if m > 20.0]
if len(match) < 10:
    bad.append(f"{len(match)} pacing reports in the match")
if slow:
    bad.append("median over 20 ms: " + ",".join(slow[:5]))
early = [m for t, m in match if t <= m0 + 900]
late = [m for t, m in match][-10:]
med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
drift = med(late) / med(early) if early and late else 0
if drift > 1.15:
    bad.append(f"pacing drift x{drift:.2f}")
mem = [tuple(map(int, l.split())) for l in open(rss) if len(l.split()) == 2]
at15 = next((r for t, r in mem if t >= m0 + 900), 0)
last = [r for t, r in mem if t >= end - 900]
growth = max(last) / at15 if at15 and last else 0
if not at15 or growth > 1.2:
    bad.append(f"memory growth x{growth:.2f}")
print(f"{'PASS' if not bad else 'FAIL'}|won={first_won}({team}) players={len(players)} elapsed={elapsed} "
      f"pacing_median={med([m for _, m in match]):.2f}ms drift=x{drift:.2f} "
      f"rss15={at15 // 1024}MB growth=x{growth:.2f}|{'; '.join(bad)}")
EOF
)
  ok="${verdict%%|*}"
  rest="${verdict#*|}"
  if [ "$fatal" != 0 ] || [ "$watchdog" != 0 ] || [ -n "$missing" ] || [ "$replay_ok" = no ] || [ "$ok" != PASS ]; then
    ok=FAIL
    fail=1
  fi
  echo "launch $i: $ok  fatal=$fatal watchdog=$watchdog shots_missing=[$(echo $missing | cut -c1-80)] replay=$replay_ok ${rest%%|*} run=$name"
  [ -n "${rest#*|}" ] && echo "  failed: ${rest#*|}"
done
exit $fail
