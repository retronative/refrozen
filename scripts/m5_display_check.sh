#!/usr/bin/env bash
# M5 work item: fullscreen, Retina/HiDPI and pointer mapping, checked end to
# end without ever taking over the display (background runs; "fullscreen" is
# simulated on a screen of REFROZEN_TEST_SCREEN points: the window is resized
# to it, so scaling, bars and input mapping run as in real fullscreen).
#
#   scripts/m5_display_check.sh
#
#   base  the default window; click Single Player -> the profile dialog
#         (reference shot)
#   fs    a 1512x982-point screen: the game's maximized popup goes fullscreen
#         (window 1512x982 points, the 800x600 frame pillarboxed: bars of 101
#         points), Ctrl+Cmd+F twice (windowed 800x600 points, then fullscreen
#         again), then click Single Player (virtual cursor) -> the same screen
#   win   -window on a 640x400-point screen: the 640x480 client's window is
#         scaled down to 533x400 points; an absolute pointer click at Single
#         Player's scaled position (455,95) -> the same screen
#
# Pass: the expected log lines, window captures of the expected sizes with
# black bars where FitRect puts them, game frames still 800x600 (base, fs),
# and each clicked screen matching the reference far better (SSIM on the
# dialog, +0.4) than the screen before the click.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="$ROOT/game/attempts/m4-accept-install"
CAP="$ROOT/build/oracle_keys/capture_window"
OUT="$ROOT/game/attempts/m5-display-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
if [ ! -x "$CAP" ]; then
  mkdir -p "$(dirname "$CAP")"
  swiftc -O -o "$CAP" "$ROOT/scripts/capture_window.swift"
fi
fail=0
check() {  # <name> <condition result 0/1> <detail>
  if [ "$2" = 0 ]; then echo "ok   $1 ($3)"; else echo "FAIL $1 ($3)"; fail=1; fi
}

# <case> <secs> <input file> <capture times...> -- [game args]
run() {
  local name="$1" secs="$2" input="$3"
  shift 3
  local caps=()
  while [ $# -gt 0 ] && [ "$1" != -- ]; do caps+=("$1"); shift; done
  [ $# -gt 0 ] && shift
  mkdir -p "$OUT/$name/xdg" "$OUT/$name/shots"
  REFROZEN_GAME_DIR="$INSTALL" XDG_DATA_HOME="$OUT/$name/xdg" REFROZEN_TEST_FOCUS=follow \
    REFROZEN_TEST_INPUT="$input" REFROZEN_SHOT_DIR="$OUT/$name/shots" \
    "$ROOT/scripts/run_attempt.sh" "$(basename "$OUT")-$name" "$secs" "$@" > /dev/null &
  local pid=$! t0=$SECONDS
  for t in ${caps[@]+"${caps[@]}"}; do
    while [ $((SECONDS - t0)) -lt "$t" ]; do sleep 0.2; done
    if w=$("$CAP" refrozen 2>/dev/null); then screencapture -x -o -l "$w" "$OUT/$name/win$t.png"; fi
  done
  wait "$pid"
}

px() {  # <png> <x> <y>: "r g b" of one pixel
  ffmpeg -loglevel error -i "$1" -vf "crop=1:1:$2:$3" -f rawvideo -pix_fmt rgb24 - | od -An -tu1 | xargs
}
size() { sips -g pixelWidth -g pixelHeight "$1" 2>/dev/null | awk '/pixel/{printf "%s ", $2}'; }
ssim() {  # dialog region of two frames, both as 800x600 (the -window client is smaller)
  ffmpeg -nostats -i "$1" -i "$2" -filter_complex \
    "[0]scale=800:600,crop=340:340:0:40,format=rgb24[a];[1]scale=800:600,crop=340:340:0:40,format=rgb24[b];[a][b]ssim" \
    -f null - 2>&1 | sed -n 's/.*All:\([0-9.]*\).*/\1/p'
}

printf '%s\n' '8 goto 683 142' '10 click' '15 shot sp' > "$OUT/base.txt"
run base 25 "$OUT/base.txt"

printf '%s\n' '8 chord ctrl+gui F' '12 chord ctrl+gui F' '14 goto 683 142' '15.5 shot before' \
  '16 click' '21 shot sp' > "$OUT/fs.txt"
REFROZEN_TEST_SCREEN=1512x982 run fs 30 "$OUT/fs.txt" 6 10 14 --

# The -window client's size (the game's frame) and the window's scale are
# measured first, then Single Player (683,142 of an 800x600 screen, scaled
# to the client) is clicked at its position in the scaled-down window.
printf '%s\n' '6 shot size' > "$OUT/win0.txt"
REFROZEN_TEST_SCREEN=640x400 run win0 10 "$OUT/win0.txt" 6 -- -window
read -r cw ch <<< "$(size "$OUT/win0/shots/size.bmp")"
read -r ww wh <<< "$(size "$OUT/win0/win6.png")"
read -r hx hy <<< "$(/opt/homebrew/bin/python3 -c "
cw, ch, ww = $cw, $ch, $ww / 2
s = ww / cw
print(round(683 / 800 * cw * s), round(142 / 600 * ch * s))")"
printf '%s\n' "10 pointer $hx $hy" '10.5 shot before' '11 click' '16 shot sp' > "$OUT/win.txt"
REFROZEN_TEST_SCREEN=640x400 run win 25 "$OUT/win.txt" 6 -- -window

base_log="$ROOT/game/attempts/$(basename "$OUT")-base.log"
fs_log="$ROOT/game/attempts/$(basename "$OUT")-fs.log"
win_log="$ROOT/game/attempts/$(basename "$OUT")-win.log"
check "no fatal stop" "$(cat "$base_log" "$fs_log" "$win_log" | grep -c FATAL | sed 's/^0$/0/;s/^[1-9].*/1/')" \
  "base, fs, win"
n=$(grep -c "simulated fullscreen 1512x982" "$fs_log")
check "fs: fullscreen entered at start and after the second toggle" "$([ "$n" -ge 2 ] && echo 0 || echo 1)" "$n times"
check "fs: Ctrl+Cmd+F made it windowed" "$(grep -q "windowed (Ctrl+Cmd+F)" "$fs_log"; echo $?)" "log"
# Window captures are Retina pixels under a title bar: fullscreen 3024 wide,
# windowed 1600 wide; the bars are FitRect's 101 points (202 pixels).
s6=$(size "$OUT/fs/win6.png"); s10=$(size "$OUT/fs/win10.png"); s14=$(size "$OUT/fs/win14.png")
check "fs: fullscreen window 1512 points wide" "$([[ "$s6" == 3024\ * ]] && echo 0 || echo 1)" "$s6"
check "fs: windowed 800 points wide" "$([[ "$s10" == 1600\ * ]] && echo 0 || echo 1)" "$s10"
check "fs: fullscreen again" "$([[ "$s14" == 3024\ * ]] && echo 0 || echo 1)" "$s14"
bar=$(px "$OUT/fs/win14.png" 100 900); mid=$(px "$OUT/fs/win14.png" 1512 900)
check "fs: left bar black" "$([ "$bar" = "0 0 0" ] && echo 0 || echo 1)" "$bar"
check "fs: frame inside the bars" "$([ "$mid" != "0 0 0" ] && echo 0 || echo 1)" "$mid"
fsz=$(size "$OUT/fs/shots/sp.bmp")
check "fs: the game's frame still 800x600" "$([ "$fsz" = "800 600 " ] && echo 0 || echo 1)" "$fsz"
# The window fits the 640x400 screen: scaled by min(640/cw, 400/ch).
want_w=$(/opt/homebrew/bin/python3 -c "print(2 * round($cw * min(1, 640 / $cw, 400 / $ch)))")
check "win: window scaled to fit the screen" "$([ "$ww" = "$want_w" ] && echo 0 || echo 1)" \
  "client ${cw}x${ch}, window ${ww} px, want ${want_w}; click at ($hx,$hy)"
# The clicked screen must match the reference far better than the screen
# just before the click did (a different client aspect, as in -window,
# changes the layout a little, so no absolute threshold).
for c in fs win; do
  after=$(ssim "$OUT/base/shots/sp.bmp" "$OUT/$c/shots/sp.bmp" 2>/dev/null)
  before=$(ssim "$OUT/base/shots/sp.bmp" "$OUT/$c/shots/before.bmp" 2>/dev/null)
  ok=$(/opt/homebrew/bin/python3 -c "print(0 if float('${after:-0}' or 0) - float('${before:-0}' or 0) > 0.4 else 1)")
  check "$c: the click opened the reference's screen" "$ok" "SSIM after ${after:-none}, before ${before:-none}"
done
echo "evidence: $OUT"
exit $fail
