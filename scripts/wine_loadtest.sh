#!/usr/bin/env bash
# Development oracle only (never part of a player's pipeline): load a map in
# the official 1.26a client under Wine and record what happened.
#
#   scripts/wine_loadtest.sh <install dir> <map path inside install> <seconds> <out prefix>
#
# Reports: crash report (Errors/), whether war3.exe is still alive, which
# .w3x/.mpq files it holds open, and a PNG of the game window only
# (scripts/capture_window.swift). Wine is shut down afterwards.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="$1" MAP="$2" SECS="$3" OUT="$4"
WINE="$ROOT/tools/wine/Wine Devel.app/Contents/Resources/wine/bin"
export WINEPREFIX="$ROOT/game/wineprefix" WINEDEBUG=-all

if pgrep -f '[\\]war3\.exe' >/dev/null; then
  echo "a war3.exe is already running; stop it first" >&2
  exit 1
fi
rm -rf "$INSTALL/Errors"
# Detached from this script's stdio, so a pipeline reading the report ends.
(cd "$INSTALL" && "$WINE/wine" war3.exe -opengl -window -loadfile "$MAP" \
  < /dev/null > "$OUT.wine.log" 2>&1 &)
for ((i = 1; i <= SECS; i++)); do
  sleep 1
  [ -d "$INSTALL/Errors" ] && break
done
echo "after ${i}s:"
if [ -d "$INSTALL/Errors" ]; then
  grep -m1 -A1 "^Exception:" "$INSTALL"/Errors/*Crash.txt || true
  cp "$INSTALL"/Errors/*Crash.txt "$OUT.crash.txt"
fi
pids=$(pgrep -f '[\\]war3\.exe' || true)
echo "war3.exe alive: $([ -n "$pids" ] && echo yes || echo no)"
for p in $pids; do
  lsof -n -P -b -p "$p" 2>/dev/null | grep -iE '\.(w3x|w3m|mpq)$' | sed 's|.*/|  open: |' | sort -u
done
if win=$(swift "$ROOT/scripts/capture_window.swift" wine 2>/dev/null); then
  screencapture -x -o -l "$win" "$OUT.png" && echo "window $win -> $OUT.png"
fi
"$WINE/wineserver" -k || true
pkill -f '[\\]war3\.exe' || true
pkill -f 'start\.exe /exec war3' || true
