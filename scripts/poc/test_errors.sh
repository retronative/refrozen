#!/bin/bash
# Error handling of the first-run builder and the launcher (proof of concept).
#
#   scripts/poc/test_errors.sh <kit> <install dir> <data dir with a built module>
#
# Each case checks the exit code and message, that build/ holds no temporary
# folder afterwards and that the installed module is unchanged (same hash).
# It works on an APFS clone of the data folder, which is never changed.
# The compile-failure and cancel cases run the lift first (about a minute each).
# REFROZEN_POC_LAUNCHER: the launcher to check (default the kit's). A launcher
# that accepts a module it should refuse starts the game: killed after 20 s.
# REFROZEN_POC_CASES (the mutation gate's focused runs): only these cases, comma-separated:
# clt missing disk compile cancel space launcher; the last line says so.
# REFROZEN_POC_LIFT_CACHE (focused runs only): the cases that lift use a copy of the kit whose
# lifter reuses the real lifter's output from this folder when every input is unchanged
# (lift_fixture.sh); otherwise it lifts. The cases that must stop before the lift (clt, disk) use
# a copy whose lifter fails at once, so a builder that passes its preflight fails in seconds,
# not after a full build; the unchanged builder never reaches it.
set -uo pipefail
KIT=$1 INSTALL=$2
HERE="$(cd "$(dirname "$0")" && pwd)"
CASES=${REFROZEN_POC_CASES:-}
want() { [ -z "$CASES" ] || [[ ",$CASES," == *",$1,"* ]]; }
ENV=(env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin)
BUILD=("${ENV[@]}" /bin/bash "$HERE/build_module.sh")
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
DATA="$SCRATCH/Application Support"  # a space, as in the real default data folder
cp -cR "$3" "$DATA" || { echo "cannot clone $3"; exit 2; }
fails=0
module_hash() { shasum -a 256 "$DATA/build/current/war3.dylib" 2>/dev/null | cut -c1-16; }
BEFORE=$(module_hash)
[ -n "$BEFORE" ] || { echo "no module in $DATA/build/current"; exit 2; }
LKIT=$KIT PKIT=$KIT  # the kits of the cases that lift and of those that stop before it
if [ -n "${REFROZEN_POC_LIFT_CACHE:-}" ]; then
  LKIT="$SCRATCH/lkit"
  cp -cR "$KIT" "$LKIT" || { echo "cannot clone $KIT"; exit 2; }
  printf '#!/bin/bash\nexec /bin/bash "%s" "%s" "%s" "%s" "$@"\n' "$HERE/lift_fixture.sh" "$KIT/bin/recomp_lift" \
    "$KIT/stamp.txt" "$REFROZEN_POC_LIFT_CACHE" > "$LKIT/bin/recomp_lift"
  PKIT="$SCRATCH/pkit"
  cp -cR "$KIT" "$PKIT" || { echo "cannot clone $KIT"; exit 2; }
  printf '#!/bin/bash\necho "test_errors.sh: the build went past its preflight" >&2\nexit 97\n' > "$PKIT/bin/recomp_lift"
fi
check() {  # name, want rc, got rc, want text, output file
  local why=""
  [ "$3" = "$2" ] || why="$why rc $3, want $2;"
  grep -q -- "$4" "$5" || why="$why no '$4' in the output;"
  ls -a "$DATA/build" | grep -q '^\.tmp-' && why="$why a temporary folder left;"
  [ "$(module_hash)" = "$BEFORE" ] || why="$why the installed module changed;"
  pgrep -f "$DATA/build/.tmp-" >/dev/null && why="$why build processes still running;"
  if [ -z "$why" ]; then echo "ok   $1"; else echo "FAIL $1 ($why last line: $(tail -1 "$5"))"; fails=$((fails + 1)); fi
}

if want clt; then
  "${ENV[@]}" REFROZEN_POC_XCODE_SELECT=/usr/bin/false /bin/bash "$HERE/build_module.sh" "$PKIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
  check "no Command Line Tools: stops before writing, says how to install them" 10 $? "xcode-select --install" "$SCRATCH/o"
fi

if want missing; then
  mkdir -p "$SCRATCH/install"
  for f in "$INSTALL"/*; do [ "$(basename "$f")" = game.dll ] || ln -s "$f" "$SCRATCH/install/"; done
  "${BUILD[@]}" "$KIT" "$SCRATCH/install" "$DATA" > "$SCRATCH/o" 2>&1
  check "an installed file missing: named, nothing built" 11 $? "game.dll not found" "$SCRATCH/o"
fi

if want disk; then
  "${ENV[@]}" REFROZEN_POC_NEED_MB=100000000 /bin/bash "$HERE/build_module.sh" "$PKIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
  check "not enough free disk: says how much is needed" 12 $? "MB of free disk needed" "$SCRATCH/o"
fi

if want compile; then
  cp -R "$LKIT" "$SCRATCH/kit"
  echo '#error broken kit (test)' >> "$SCRATCH/kit/include/runtime/lifted.h"
  "${BUILD[@]}" "$SCRATCH/kit" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1
  check "a file does not compile: stops, nothing installed, previous module kept" 14 $? "a file did not compile" "$SCRATCH/o"
fi

if want cancel; then
  "${BUILD[@]}" "$LKIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1 &
  pid=$!
  until pgrep -f "$DATA/build/.tmp-.*cc.sh" >/dev/null; do sleep 1; done
  sleep 20
  kill -TERM $pid  # the builder itself (env execs bash), as a Cancel button would
  wait $pid; rc=$?  # checked at once: the builder reports a cancel only once its workers are gone
  check "cancelled while compiling: workers stopped, nothing installed, previous module kept" 130 $rc "cancelled" "$SCRATCH/o"
fi

if want space; then
  "${BUILD[@]}" "$LKIT" "$INSTALL" "$DATA" > "$SCRATCH/o" 2>&1 &
  pid=$!
  until grep -q "^compiled \|build failed" "$SCRATCH/o" || ! kill -0 $pid 2>/dev/null; do sleep 1; done
  kill -TERM $pid 2>/dev/null
  wait $pid; rc=$?
  check "a data folder with a space in its path: files compile (then cancelled)" 130 $rc "^compiled " "$SCRATCH/o"
fi

# The launcher: a module from another build, a missing one, a swapped library.
LAUNCH=(env -i HOME="$HOME" PATH=/usr/bin:/bin XDG_DATA_HOME="$SCRATCH/xdg" REFROZEN_BACKGROUND=1
  "${REFROZEN_POC_LAUNCHER:-$KIT/bin/refrozen}" --game "$INSTALL" --module)
launch() {  # module, output file; rc 124 if still running after 20 s
  "${LAUNCH[@]}" "$1" > "$2" 2>&1 &
  local p=$! i
  for i in $(seq 200); do kill -0 $p 2>/dev/null || { wait $p; return; }; sleep 0.1; done
  kill -9 $p; wait $p 2>/dev/null; return 124
}
if want launcher; then
  mkdir -p "$SCRATCH/other"
  cp "$DATA/build/current/war3.dylib" "$SCRATCH/other/" && echo "0000-other" > "$SCRATCH/other/stamp.txt"
  launch "$SCRATCH/other/war3.dylib" "$SCRATCH/o"
  check "launcher: a module from another build is refused before it is loaded" 3 $? "from build 0000-other, this reFrozen needs" "$SCRATCH/o"
  launch "$SCRATCH/none/war3.dylib" "$SCRATCH/o"
  check "launcher: no module is refused" 3 $? "missing or unstamped" "$SCRATCH/o"
  mkdir -p "$SCRATCH/swapped" && cp "$KIT/stamp.txt" "$SCRATCH/swapped/"
  echo 'extern "C" const char* const refrozen_module_stamp = "0000-other";' > "$SCRATCH/s.cpp"
  /usr/bin/xcrun clang++ -dynamiclib -o "$SCRATCH/swapped/war3.dylib" "$SCRATCH/s.cpp"
  launch "$SCRATCH/swapped/war3.dylib" "$SCRATCH/o"
  check "launcher: a library that does not match its stamp file is refused" 3 $? "does not match its stamp file" "$SCRATCH/o"
fi

echo "$([ $fails = 0 ] && echo "ALL PASS" || echo "$fails FAILED")${CASES:+ (cases $CASES only)}"
exit $((fails > 0))
