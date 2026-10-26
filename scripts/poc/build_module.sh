#!/bin/bash
# First-run builder, proof of concept (experimental: no release step uses it
# until first-run setup and packaging exist): lifts the player's own installed game
# and compiles it into the game module on this Mac, with Apple's Command
# Line Tools only (no Homebrew, no CMake). Nothing it makes is distributed.
#
#   scripts/poc/build_module.sh <kit> <install dir> [<data dir>] [jobs]
#
# <kit>: what the app carries (scripts/poc/make_kit.sh): the lifter, the
# runtime libraries and headers, the lift configuration and the stamp.
# <data dir> (default ~/Library/Application Support/reFrozen): the module
# goes to build/<stamp>/war3.dylib there and build/current points at it.
# A failed or cancelled build leaves no partial module and keeps the
# previous one; its log stays in logs/. Exit: 0 built, 10 no Command Line
# Tools, 11 an input missing, 12 not enough free disk, 13 lift failed,
# 14 compile failed, 15 link or signing failed, 130 cancelled.
set -uo pipefail
[ $# -ge 2 ] || { echo "usage: $0 <kit> <install dir> [<data dir>] [jobs]" >&2; exit 2; }
KIT=$(cd "$1" && pwd) INSTALL=$2
DATA=${3:-"$HOME/Library/Application Support/reFrozen"}
JOBS=${4:-$(sysctl -n hw.ncpu)}
NEED_MB=${REFROZEN_POC_NEED_MB:-1500}               # measured peak plus a margin
XCODE_SELECT=${REFROZEN_POC_XCODE_SELECT:-/usr/bin/xcode-select}  # tests: a missing CLT
KEEP=${REFROZEN_POC_KEEP:-}  # tests: keep the lifted sources and objects of a successful build
MODULES=(war3.exe:war3 game.dll:game Storm.dll:storm Mss32.dll:mss32 msvcr80.dll:msvcr80
  ijl15.dll:ijl15 redist/miles/Mp3dec.asi:mp3dec_asi redist/miles/Mssfast.m3d:mssfast_m3d
  redist/miles/Msseax2.m3d:msseax2_m3d redist/miles/Mssdolby.m3d:mssdolby_m3d
  redist/miles/Reverb3.flt:reverb3_flt)
FLAGS=(-std=gnu++20 -arch arm64 -O2 -g0 -fno-strict-aliasing -fnon-call-exceptions
  -ffp-contract=off -fno-fast-math -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer)

mkdir -p "$DATA/logs" "$DATA/build"
LOG="$DATA/logs/build-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
fail() { echo "build failed: $2 (log: $LOG)"; exit "$1"; }

# Preflight, before anything is written under build/.
DEV=$("$XCODE_SELECT" -p 2>/dev/null) || DEV=""
if [ -z "$DEV" ] || ! /usr/bin/xcrun --find clang++ >/dev/null 2>&1; then
  fail 10 "Apple's Command Line Tools are needed: run xcode-select --install, then build again"
fi
for m in "${MODULES[@]}"; do
  [ -f "$INSTALL/${m%%:*}" ] || fail 11 "$INSTALL/${m%%:*} not found (install the game first)"
done
STAMP=$(cat "$KIT/stamp.txt")
FREE_MB=$(( $(df -Pk "$DATA" | awk 'NR==2 {print $4}') / 1024 ))
[ "$FREE_MB" -ge "$NEED_MB" ] || fail 12 "$NEED_MB MB of free disk needed, $FREE_MB MB free"

TMP="$DATA/build/.tmp-$STAMP-$$"
OK=0 WORKERS=""
cleanup() {
  # Every worker: xargs, the compile wrappers and their compilers (all name
  # the temporary folder); killing only xargs' children orphans the compilers.
  if [ -n "$WORKERS" ]; then
    pkill -TERM -f "$TMP/" 2>/dev/null
    for _ in $(seq 50); do pgrep -f "$TMP/" >/dev/null || break; sleep 0.1; done
  fi
  [ -n "${SAMPLER:-}" ] && kill "$SAMPLER" 2>/dev/null
  if [ "$OK" = 1 ] && [ -n "$KEEP" ]; then mv "$TMP" "$KEEP"; else rm -rf "$TMP"; fi
  [ "$OK" = 1 ] || echo "nothing installed; the previous module (if any) is unchanged"
}
trap cleanup EXIT
trap 'echo "cancelled"; exit 130' INT TERM
mkdir -p "$TMP"/{symbols,generated,obj,out}
echo "reFrozen game module $STAMP: $JOBS jobs, $($XCODE_SELECT -p), $(/usr/bin/xcrun clang++ --version | head -1)"

SECONDS=0
args=()
for i in "${!MODULES[@]}"; do
  file=${MODULES[$i]%%:*} name=${MODULES[$i]##*:} dir="$TMP/symbols/${MODULES[$i]##*:}"
  mkdir -p "$dir"
  cp "$KIT/config/symbols/$name/functions.tsv" "$dir/"
  /usr/bin/python3 -I "$KIT/scripts/jumptable_corrections.py" "$KIT/config/symbols/$name/jumptables.tsv" \
    "$KIT/config/jumptable_corrections.tsv" "$name" > "$dir/jumptables.tsv" || fail 13 "jump tables of $name"
  /usr/bin/python3 -I "$KIT/scripts/pe_symbols.py" "$INSTALL/$file" --out "$dir" > /dev/null \
    || fail 13 "reading $file"
  [ "$i" = 0 ] && args+=(--exe "$INSTALL/$file") || args+=(--module "$INSTALL/$file")
  args+=(--symbols "$dir" --manifest "$KIT/config/$name.manifest")
done
"$KIT/bin/recomp_lift" "${args[@]}" --out "$TMP/generated" > "$TMP/lift.log" 2>&1 \
  || { tail -20 "$TMP/lift.log"; fail 13 "the lifter stopped"; }
T_LIFT=$SECONDS

printf 'extern "C" const char* const refrozen_module_stamp = "%s";\n' "$STAMP" > "$TMP/generated/stamp.cpp"
cat > "$TMP/cc.sh" <<CC
#!/bin/bash
obj="$TMP/obj/\$(basename "\${1%.cpp}").o"
/usr/bin/time -l /usr/bin/xcrun clang++ ${FLAGS[*]} -I"$KIT/include" -c "\$1" -o "\$obj" 2> "\$obj.log" \
  || { cat "\$obj.log"; exit 255; }
echo "compiled \$(basename "\$1")"
CC
chmod +x "$TMP/cc.sh"
( peak=0; while :; do
    s=$(ps -Ao rss,comm | awk '/clang/ {s += $1} END {print s + 0}')
    [ "$s" -gt "$peak" ] && peak=$s && echo "$peak" > "$TMP/peak_kb"
    sleep 1
  done ) &
SAMPLER=$!
# Progress for the first-run setup: "compiling <n> files", then one "compiled <file>" line each.
echo "compiling $(ls "$TMP"/generated/*.cpp "$KIT/src/lifted_table.cpp" | wc -l | tr -d ' ') files"
ls "$TMP"/generated/*.cpp "$KIT/src/lifted_table.cpp" | xargs -P "$JOBS" -n 1 "$TMP/cc.sh" &
WORKERS=$!
wait "$WORKERS" || { WORKERS=""; fail 14 "a file did not compile"; }
WORKERS=""
T_CC=$SECONDS

"/usr/bin/xcrun" clang++ -dynamiclib -arch arm64 -o "$TMP/out/war3.dylib" "$TMP"/obj/*.o \
  -L"$KIT/lib" -lrecomp_runtime -lrecomp_x87 -lrecomp_image -install_name @rpath/war3.dylib \
  || fail 15 "linking the module"
/usr/bin/codesign -f -s - "$TMP/out/war3.dylib" || fail 15 "signing the module"
T_LINK=$SECONDS
kill "$SAMPLER" 2>/dev/null; SAMPLER=""
TMP_MB=$(( $(du -sk "$TMP" | cut -f1) / 1024 ))
MAX_TU_MB=$(( $(cat "$TMP"/obj/*.log | awk '/maximum resident/ {if ($1 > m) m = $1} END {print m + 0}') / 1048576 ))
echo "$STAMP" > "$TMP/out/stamp.txt"

# Into place: build/<stamp>, then build/current (renames; a rebuild keeps the
# previous module until the new one is in place).
final="$DATA/build/$STAMP"
mv "$TMP/out" "$DATA/build/.$STAMP.ready" || fail 15 "moving the module into place"
[ -e "$final" ] && mv "$final" "$DATA/build/.$STAMP.previous"
mv "$DATA/build/.$STAMP.ready" "$final" && ln -s "$STAMP" "$DATA/build/.current.new" &&
  /usr/bin/python3 -I -c 'import os, sys; os.replace(sys.argv[1], sys.argv[2])' \
    "$DATA/build/.current.new" "$DATA/build/current" || fail 15 "switching build/current"
rm -rf "$DATA/build/.$STAMP.previous"
OK=1
echo "built: $final/war3.dylib ($(( $(stat -f %z "$final/war3.dylib") / 1048576 )) MB); lift ${T_LIFT}s," \
  "compile $(( T_CC - T_LIFT ))s, link+sign $(( T_LINK - T_CC ))s, total ${T_LINK}s; peak disk ${TMP_MB} MB," \
  "peak compiler memory $(( $(cat "$TMP/peak_kb" 2>/dev/null || echo 0) / 1024 )) MB (largest file ${MAX_TU_MB} MB)"
