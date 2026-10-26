#!/bin/bash
# Error handling of the first-run builder and the launcher (proof of concept).
#
#   scripts/poc/test_errors.sh <kit> <install dir> <data dir with a built module>
#
# Each case checks the exit code and message, that build/ holds no temporary
# folder afterwards and that the installed module is unchanged (same hash).
# The compile-failure and cancel cases run the lift first (about a minute each).
set -uo pipefail
KIT=$1 INSTALL=$2 DATA=$3
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV=(env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin)
BUILD=("${ENV[@]}" /bin/bash "$HERE/build_module.sh")
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
fails=0
module_hash() { shasum -a 256 "$DATA/build/current/war3.dylib" 2>/dev/null | cut -c1-16; }
BEFORE=$(module_hash)
[ -n "$BEFORE" ] || { echo "no module in $DATA/build/current"; exit 2; }
check() {  # name, want rc, got rc, want text, output file
  local ok=1
  [ "$3" = "$2" ] || ok=0
  grep -q -- "$4" "$5" || ok=0
  ls -a "$DATA/build" | grep -q '^\.tmp-' && ok=0
  [ "$(module_hash)" = "$BEFORE" ] || ok=0
  pgrep -f "$DATA/build/.tmp-" >/dev/null && ok=0
  if [ $ok = 1 ]; then echo "ok   $1"; else echo "FAIL $1 (rc $3, want $2; $(tail -1 "$5"))"; fails=$((fails + 1)); fi
}

"${ENV[@]}" REFROZEN_POC_XCODE_SELECT=/usr/bin/false /bin/bash "$HERE/build_module.sh" "$KIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
check "no Command Line Tools: stops before writing, says how to install them" 10 $? "xcode-select --install" "$SCRATCH/o"

mkdir -p "$SCRATCH/install"
for f in "$INSTALL"/*; do [ "$(basename "$f")" = game.dll ] || ln -s "$f" "$SCRATCH/install/"; done
"${BUILD[@]}" "$KIT" "$SCRATCH/install" "$DATA" > "$SCRATCH/o" 2>&1
check "an installed file missing: named, nothing built" 11 $? "game.dll not found" "$SCRATCH/o"

"${ENV[@]}" REFROZEN_POC_NEED_MB=100000000 /bin/bash "$HERE/build_module.sh" "$KIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
check "not enough free disk: says how much is needed" 12 $? "MB of free disk needed" "$SCRATCH/o"

cp -R "$KIT" "$SCRATCH/kit"
echo '#error broken kit (test)' >> "$SCRATCH/kit/include/runtime/lifted.h"
"${BUILD[@]}" "$SCRATCH/kit" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
check "a file does not compile: stops, nothing installed, previous module kept" 14 $? "a file did not compile" "$SCRATCH/o"

"${BUILD[@]}" "$KIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1 &
pid=$!
until pgrep -f "$DATA/build/.tmp-.*cc.sh" >/dev/null; do sleep 1; done
sleep 20
pkill -TERM -f "^/bin/bash $HERE/build_module.sh"
wait $pid; rc=$?
sleep 3
check "cancelled while compiling: workers stopped, nothing installed, previous module kept" 130 $rc "cancelled" "$SCRATCH/o"

# The launcher: a module from another build, a missing one, a swapped library.
LAUNCH=(env -i HOME="$HOME" PATH=/usr/bin:/bin "$KIT/bin/refrozen" --game "$INSTALL" --module)
mkdir -p "$SCRATCH/other"
cp "$DATA/build/current/war3.dylib" "$SCRATCH/other/" && echo "0000-other" > "$SCRATCH/other/stamp.txt"
"${LAUNCH[@]}" "$SCRATCH/other/war3.dylib" > "$SCRATCH/o" 2>&1
check "launcher: a module from another build is refused before it is loaded" 3 $? "from build 0000-other, this reFrozen needs" "$SCRATCH/o"
"${LAUNCH[@]}" "$SCRATCH/none/war3.dylib" > "$SCRATCH/o" 2>&1
check "launcher: no module is refused" 3 $? "missing or unstamped" "$SCRATCH/o"
mkdir -p "$SCRATCH/swapped" && cp "$KIT/stamp.txt" "$SCRATCH/swapped/"
echo 'extern "C" const char* const refrozen_module_stamp = "0000-other";' > "$SCRATCH/s.cpp"
/usr/bin/xcrun clang++ -dynamiclib -o "$SCRATCH/swapped/war3.dylib" "$SCRATCH/s.cpp"
"${LAUNCH[@]}" "$SCRATCH/swapped/war3.dylib" > "$SCRATCH/o" 2>&1
check "launcher: a library that does not match its stamp file is refused" 3 $? "does not match its stamp file" "$SCRATCH/o"

echo "$([ $fails = 0 ] && echo "ALL PASS" || echo "$fails FAILED")"
exit $((fails > 0))
