#!/bin/bash
# Test fixture of test_errors.sh's focused runs (never used by a build or a release):
#   lift_fixture.sh <lifter> <kit stamp file> <cache dir> <the lifter's arguments...>
# Runs the lifter, or reuses its output for the same inputs from <cache dir>: the key
# is the lifter, the kit's stamp, every argument and the contents of every file and
# folder an argument names (except --out). A failed lift is not kept.
set -uo pipefail
LIFTER=$1 STAMP=$2 CACHE=$3
shift 3
out="" prev=""
for a in "$@"; do [ "$prev" = --out ] && out=$a; prev=$a; done
[ -n "$out" ] || { echo "lift_fixture.sh: no --out" >&2; exit 2; }
key=$( { shasum -a 256 < "$LIFTER"; cat "$STAMP"
  for a in "$@"; do
    if [ "$a" = "$out" ]; then echo "<out>"
    elif [ -d "$a" ]; then echo "<dir>"; (cd "$a" && find . -type f | LC_ALL=C sort | while IFS= read -r f; do
      echo "$f"; shasum -a 256 < "$f"; done)
    elif [ -f "$a" ]; then echo "<file>"; shasum -a 256 < "$a"
    else echo "$a"; fi
  done; } | shasum -a 256 | cut -c1-32)
C="$CACHE/$key"
if [ -d "$C" ]; then
  mkdir -p "$out" && cp -cR "$C/." "$out/"
  exit
fi
"$LIFTER" "$@" || exit
mkdir -p "$CACHE"
cp -cR "$out" "$C.tmp-$$" && mv "$C.tmp-$$" "$C" 2>/dev/null
rm -rf "$C.tmp-$$"
exit 0
