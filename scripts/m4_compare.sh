#!/usr/bin/env bash
# Side-by-side and SSIM of native shots against the Wine oracle's (development
# evidence; scripts/oracle_menus.sh makes the oracle shots).
#
#   scripts/m4_compare.sh <native shot dir> <oracle d3d run dir> <oracle opengl run dir> <out dir>
#
# For every shot name the native dir has as <name>.bmp and the d3d oracle as
# <name>.png: the oracle captures (800x600 client at Retina scale under a
# 64-pixel title bar) are cropped to the client and scaled to 800x600, and
# <out>/<name>.png shows native | d3d | opengl. Prints ffmpeg's SSIM (All) of
# native against each oracle and of the two oracles against each other. The
# menus' 3D backgrounds animate, so the numbers rank screens rather than
# pass them: a difference counts as a port defect only where the two oracle
# renderers agree with each other and native does not.
set -euo pipefail
NATIVE="$1" D3D="$2" GL="$3" OUT="$4"
mkdir -p "$OUT"
crop='crop=1600:1200:0:64,scale=800:600:flags=area'
ssim() {  # <a> <b> [filter for b]
  ffmpeg -nostats -loglevel info -i "$1" -i "$2" \
    -filter_complex "[0]scale=800:600:flags=area,format=rgb24[a];[1]${3:-null},format=rgb24[b];[a][b]ssim" \
    -f null - 2>&1 | sed -n 's/.*All:\([0-9.]*\).*/\1/p'
}
printf '%-12s %10s %10s %10s\n' shot native/d3d native/gl d3d/gl
for oracle in "$D3D"/*.png; do
  name="$(basename "$oracle" .png)"
  native="$NATIVE/$name.bmp"
  [ -f "$native" ] || continue
  gl="$GL/$name.png"
  if [ -f "$gl" ]; then
    ffmpeg -loglevel error -y -i "$native" -i "$oracle" -i "$gl" -filter_complex \
      "[0]scale=800:600[a];[1]$crop[b];[2]$crop[c];[a][b][c]hstack=3" -frames:v 1 "$OUT/$name.png"
    gs="$(ssim "$native" "$gl" "$crop")"
    og="$(ffmpeg -nostats -loglevel info -i "$oracle" -i "$gl" -filter_complex \
      "[0]$crop,format=rgb24[a];[1]$crop,format=rgb24[b];[a][b]ssim" -f null - 2>&1 |
      sed -n 's/.*All:\([0-9.]*\).*/\1/p')"
  else
    ffmpeg -loglevel error -y -i "$native" -i "$oracle" -filter_complex \
      "[0]scale=800:600[a];[1]$crop[b];[a][b]hstack=2" -frames:v 1 "$OUT/$name.png"
    gs=- og=-
  fi
  printf '%-12s %10s %10s %10s\n' "$name" "$(ssim "$native" "$oracle" "$crop")" "$gs" "$og"
done
