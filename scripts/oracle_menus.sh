#!/usr/bin/env bash
# Development oracle only (never part of a player's pipeline): walk the menus
# of the official 1.26a client under Wine with a key script and capture the
# game window at each "shot" line, for comparison with the native port.
#
#   scripts/oracle_menus.sh <name> <d3d|opengl> <key script> [seconds]   # default 60
#
# Each run starts from APFS clones of game/wine-oracle and game/wineprefix
# (the originals are never written: the oracle install is also the native
# installer's --verify reference), set to an 800x600 window with the intro
# seen. d3d is the client's default Direct3D 8 renderer (wined3d), opengl
# its -opengl renderer. The script is scripts/oracle_keys.c's format; keys
# are posted to the game window, so the host pointer is never moved, but
# the Wine window does appear (and take focus) on the desktop.
# Captures: game/attempts/oracle-<name>/<shot>.png (window only, Retina scale,
# with its title bar; scripts/m4_compare.sh crops and scales it). Wine is shut down afterwards.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$1" RENDER="$2" SCRIPT="$3" SECS="${4:-60}"
# ORACLE_NO_AUDIO=1: Wine's audio driver disabled, so the client sees no
# sound device (the native port's M3 sound model).
WINE_BIN="$ROOT/tools/wine/Wine Devel.app/Contents/Resources/wine/bin"
LLVM=/opt/homebrew/opt/llvm/bin
RUN="$ROOT/game/attempts/oracle-$NAME"
case "$RENDER" in d3d) ARGS=(-window) ;; opengl) ARGS=(-window -opengl) ;; *) echo "renderer: d3d or opengl" >&2; exit 2 ;; esac

if pgrep -f '[\\]war3\.exe' >/dev/null; then
  echo "a war3.exe is already running; stop it first" >&2
  exit 1
fi

# The key helper: freestanding i686 PE, import libraries from .def files.
B="$ROOT/build/oracle_keys"
mkdir -p "$B"
if [ ! -f "$B/oracle_keys.exe" ] || [ "$ROOT/scripts/oracle_keys.c" -nt "$B/oracle_keys.exe" ]; then
  printf 'LIBRARY kernel32.dll\nEXPORTS\nSleep@4\nGetTickCount@0\nGetCommandLineA@0\nCreateFileA@28\nReadFile@20\nWriteFile@20\nGetStdHandle@4\nExitProcess@4\nCloseHandle@4\n' > "$B/kernel32.def"
  printf 'LIBRARY user32.dll\nEXPORTS\nFindWindowA@8\nPostMessageA@16\nMapVirtualKeyA@8\nGetWindowRect@8\nGetClientRect@8\nSetWindowPos@28\n' > "$B/user32.def"
  for l in kernel32 user32; do "$LLVM/llvm-dlltool" -m i386 -d "$B/$l.def" -l "$B/$l.lib" -k; done
  "$LLVM/clang" --target=i686-pc-windows-msvc -O2 -ffreestanding -fno-builtin -fno-stack-protector \
    -mno-stack-arg-probe -c "$ROOT/scripts/oracle_keys.c" -o "$B/oracle_keys.obj"
  lld-link /nologo /entry:start /subsystem:console /nodefaultlib /out:"$B/oracle_keys.exe" \
    "$B/oracle_keys.obj" "$B/kernel32.lib" "$B/user32.lib"
fi

# Window lookup for screencapture, compiled once (swift's script mode costs
# about a second per call).
if [ ! -x "$B/capture_window" ] || [ "$ROOT/scripts/capture_window.swift" -nt "$B/capture_window" ]; then
  swiftc -O -o "$B/capture_window" "$ROOT/scripts/capture_window.swift"
fi

if [ -e "$RUN" ]; then
  echo "$RUN exists; pick a new name" >&2
  exit 1
fi
mkdir -p "$RUN"
cp -cR "$ROOT/game/wine-oracle" "$RUN/install"
cp -cR "$ROOT/game/wineprefix" "$RUN/prefix"
cp "$SCRIPT" "$RUN/keys.txt"
export WINEPREFIX="$RUN/prefix" WINEDEBUG=-all
KEY='HKCU\Software\Blizzard Entertainment\Warcraft III'
"$WINE_BIN/wine" reg add "$KEY\\Video" /v reswidth /t REG_DWORD /d 800 /f >/dev/null
"$WINE_BIN/wine" reg add "$KEY\\Video" /v resheight /t REG_DWORD /d 600 /f >/dev/null
"$WINE_BIN/wine" reg add "$KEY\\Misc" /v seenintromovie /t REG_DWORD /d 1 /f >/dev/null
if [ "${ORACLE_NO_AUDIO:-0}" = 1 ]; then
  "$WINE_BIN/wine" reg add 'HKCU\Software\Wine\Drivers' /v Audio /t REG_SZ /d "" /f >/dev/null
fi

(cd "$RUN/install" && "$WINE_BIN/wine" war3.exe "${ARGS[@]}" < /dev/null > "$RUN/wine.log" 2>&1 &)
cp "$B/oracle_keys.exe" "$RUN/oracle_keys.exe"
(cd "$RUN" && "$WINE_BIN/wine" oracle_keys.exe keys.txt > keys.log 2>&1 &)
# The helper creates <shot>.req when a shot is due (capture, then remove
# it) and __done.req or __fail.req at the end.
deadline=$((SECONDS + SECS))
status=deadline
while [ $SECONDS -lt $deadline ]; do
  for req in "$RUN"/*.req; do
    [ -e "$req" ] || continue
    shot="$(basename "$req" .req)"
    case "$shot" in __done) status=done; continue ;; __fail) status=failed; continue ;; esac
    if win=$("$B/capture_window" wine 2>/dev/null); then
      screencapture -x -o -l "$win" "$RUN/$shot.png" && echo "shot $shot"
    else
      echo "shot $shot: no window"
    fi
    rm "$req"
  done
  [ "$status" != deadline ] && break
  sleep 0.1
done
echo "key script: $status"
grep -a "oracle_keys:" "$RUN/keys.log" || true
alive=no
pgrep -f '[\\]war3\.exe' >/dev/null && alive=yes
echo "war3.exe alive at the end: $alive"
if [ -d "$RUN/install/Errors" ]; then grep -m1 -A1 "^Exception:" "$RUN"/install/Errors/*Crash.txt || true; fi
"$WINE_BIN/wineserver" -k || true
