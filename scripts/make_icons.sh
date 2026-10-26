#!/usr/bin/env bash
# Builds every icon from the two committed sources with the macOS tools sips and iconutil, plus
# stdlib python3 for the .ico container:
#   assets/icon/refrozen-app-icon-master.png  the approved artwork (never modified)
#   assets/icon/refrozen-icon-small.svg       its simplified drawing for 16 and 32 px
# Outputs (all committed; tests/test_brand_assets.py checks they match a fresh run):
#   assets/icon/reFrozen.icns                  macOS app icon on Apple's icon grid
#   .website/public/favicon.ico                16 and 32 px from the small drawing, 48 px from the master
#   .website/public/favicon-32.png             small drawing
#   .website/public/icon-{192,512}.png, apple-touch-icon.png (180), brand/mark-{96,144}.png  master
#
# The .icns follows the macOS (Big Sur and later) template: the master's frame is centred and
# scaled to an 824 px body on a 1024 px canvas (about 80%), on a transparent margin. The master's
# frame measures 1117 x 1077 px with its centre at (625, 602) of 1254 (alpha >= 250), so the art is
# cropped to the 1204 px square centred on the frame (offset x 23, y 0) and scaled to
# 1204 * 824 / 1117 = 888 px of every 1024. The 16 and 32 px sizes (icon_16x16, icon_16x16@2x and
# icon_32x32) use the small drawing with a slightly larger body (14 of 16 px) so it stays legible;
# icon_32x32@2x (64 px) and up use the master. Web icons keep the full crop (browsers and iOS
# add no margin of their own around a favicon, and iOS masks touch icons itself).
#
# Every size is resampled directly from its source, never from another size. For a given macOS
# version the outputs are byte-identical between runs.
#
# Usage: scripts/make_icons.sh [--out-dir DIR]
#   --out-dir DIR  write reFrozen.icns and the web files under DIR instead of the repository
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
master=$root/assets/icon/refrozen-app-icon-master.png
small=$root/assets/icon/refrozen-icon-small.svg
icns=$root/assets/icon/reFrozen.icns
web=$root/.website/public

case "${1:-}" in
  --out-dir)
    [ -n "${2:-}" ] || { echo "usage: $0 [--out-dir DIR]" >&2; exit 2; }
    mkdir -p "$2"
    icns=$(cd "$2" && pwd)/reFrozen.icns
    web=$(cd "$2" && pwd)/web
    ;;
  "") ;;
  *) echo "usage: $0 [--out-dir DIR]" >&2; exit 2 ;;
esac

for f in "$master" "$small"; do [ -f "$f" ] || { echo "missing source: $f" >&2; exit 1; }; done
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# full <src> <px> <out>: the whole source, resampled to a square.
full() { sips -s format png -z "$2" "$2" "$1" --out "$3" >/dev/null; }

# padded <src> <inner px> <canvas px> <out>: resampled to inner, centred on a transparent canvas.
padded() {
  sips -s format png -z "$2" "$2" "$1" --out "$tmp/inner.png" >/dev/null
  sips -p "$3" "$3" "$tmp/inner.png" --out "$4" >/dev/null
}

# The master's frame, centred: a 1204 px square crop (see above).
sips -s format png -c 1204 1204 --cropOffset 0 23 "$master" --out "$tmp/master-centred.png" >/dev/null

grid() { padded "$tmp/master-centred.png" $(( ($1 * 888 + 512) / 1024 )) "$1" "$2"; }

iconset=$tmp/reFrozen.iconset
mkdir "$iconset"
padded "$small" 14 16 "$iconset/icon_16x16.png"
padded "$small" 28 32 "$iconset/icon_16x16@2x.png"
cp "$iconset/icon_16x16@2x.png" "$iconset/icon_32x32.png"
grid 64 "$iconset/icon_32x32@2x.png"
for pt in 128 256 512; do
  grid "$pt" "$iconset/icon_${pt}x${pt}.png"
  grid $((pt * 2)) "$iconset/icon_${pt}x${pt}@2x.png"
done
mkdir -p "$(dirname "$icns")"
iconutil -c icns "$iconset" -o "$icns"

mkdir -p "$web/brand"
full "$small" 16 "$tmp/favicon-16.png"
full "$small" 32 "$web/favicon-32.png"
full "$master" 48 "$tmp/favicon-48.png"
full "$master" 192 "$web/icon-192.png"
full "$master" 512 "$web/icon-512.png"
full "$master" 180 "$web/apple-touch-icon.png"
full "$master" 96 "$web/brand/mark-96.png"
full "$master" 144 "$web/brand/mark-144.png"

# favicon.ico: an ICONDIR with PNG-compressed entries (supported by every current browser).
/usr/bin/python3 -I - "$web/favicon.ico" "$tmp/favicon-16.png" "$web/favicon-32.png" "$tmp/favicon-48.png" <<'PY'
import struct, sys
out, pngs = sys.argv[1], sys.argv[2:]
blobs = [open(p, 'rb').read() for p in pngs]
offset = 6 + 16 * len(blobs)
head = struct.pack('<HHH', 0, 1, len(blobs))
entries = b''
for blob in blobs:
    w, h = struct.unpack('>II', blob[16:24])
    entries += struct.pack('<BBBBHHII', w % 256, h % 256, 0, 0, 1, 32, len(blob), offset)
    offset += len(blob)
open(out, 'wb').write(head + entries + b''.join(blobs))
PY

echo "icns: $icns ($(stat -f %z "$icns") bytes)"
for f in favicon.ico favicon-32.png icon-192.png icon-512.png apple-touch-icon.png brand/mark-96.png brand/mark-144.png; do
  echo "web:  $web/$f ($(stat -f %z "$web/$f") bytes)"
done
