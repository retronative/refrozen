#!/bin/bash
# reFrozen release candidate: one commit, from a clean clone, offline.
#
#   scripts/release/release_candidate.sh <repo> <commit> <out dir> <deps prefix> <x86recomp mirror> <fetchcontent dir>
#
# Clones <commit>, applies the x86recomp patches to the pinned upstream commit
# (from the mirror), builds the launcher, lifter and runtime against the
# source-built dependencies (never Homebrew's; the build's configuration as
# tested: Debug with the hot paths at -O2, debug symbols stripped), stages the
# kit (no game code: the game module is built on the player's Mac),
# assembles reFrozen.app, checks it (scripts/release/check_release.py), makes
# the dmg and writes SHA256SUMS and a manifest. Stops at the first failure.
set -euo pipefail
REPO=$1 COMMIT=$2 OUT=$3 DEPS=$(cd "$4" && pwd) MIRROR=$5 FC=$(cd "$6" && pwd)
X86_BASE=ad1b16b30b3cc049e47a1ebbf96e8066b32191e1
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
SRC="$OUT/src"
step() { echo "== $(TZ=Asia/Bangkok date +%H:%M:%S) $*"; }

step "clone $COMMIT"
rm -rf "$SRC"
git clone -q "$REPO" "$SRC"
git -C "$SRC" checkout -q "$COMMIT"
SHA=$(git -C "$SRC" rev-parse HEAD)
VERSION=$(cat "$SRC/VERSION")
[ -z "$(git -C "$SRC" status --porcelain)" ] || { echo "clone not clean"; exit 1; }

step "x86recomp $X86_BASE + patches/x86recomp (from the mirror)"
git clone -q "$MIRROR" "$SRC/tools/x86recomp"
git -C "$SRC/tools/x86recomp" checkout -q -b refrozen "$X86_BASE"
for p in "$SRC"/patches/x86recomp/*.patch; do git -C "$SRC/tools/x86recomp" apply "$p"; done
git -C "$SRC/tools/x86recomp" add -A
git -C "$SRC/tools/x86recomp" -c user.name="reFrozen setup" -c user.email=setup@refrozen.invalid commit -q -m "reFrozen patches"
X86_TREE=$(git -C "$SRC/tools/x86recomp" rev-parse --short HEAD^{tree})
echo "x86recomp tree $X86_TREE"

step "configure (source-built dependencies only)"
export PKG_CONFIG_LIBDIR="$DEPS/lib/pkgconfig"  # no Homebrew FFmpeg
cmake -S "$SRC" -B "$SRC/build/main" -G Ninja -DCMAKE_BUILD_TYPE=Debug -DREFROZEN_DYNAMIC_MODULE=ON \
  -DRECOMP_LLVM_ROOT="$DEPS" -DCMAKE_PREFIX_PATH="$DEPS" -DCMAKE_PROGRAM_PATH="$DEPS/bin" \
  -DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0 \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DFETCHCONTENT_SOURCE_DIR_SOFTFLOAT="$FC/softfloat" \
  -DFETCHCONTENT_SOURCE_DIR_ZYDIS="$FC/zydis" \
  "-DCMAKE_C_FLAGS=-ffile-prefix-map=$SRC=refrozen -ffile-prefix-map=$FC=deps" \
  "-DCMAKE_CXX_FLAGS=-ffile-prefix-map=$SRC=refrozen -ffile-prefix-map=$FC=deps" > "$OUT/configure.log"
grep -q "REFROZEN_MODULE_STAMP:STRING=${SHA:0:12}-$X86_TREE" "$SRC/build/main/CMakeCache.txt" || {
  echo "stamp is not ${SHA:0:12}-$X86_TREE"; exit 1; }

step "build launcher, lifter, runtime"
ninja -C "$SRC/build/main" refrozen recomp_lift > "$OUT/build.log"
mkdir -p "$SRC/build"
/usr/bin/xcrun clang -O2 -Wall -Wextra -arch arm64 -mmacosx-version-min=14.0 "$SRC/scripts/bnupdate_patch.c" \
  -o "$SRC/build/bnupdate_patch"

step "kit and app"
STORMLIB="$DEPS/lib/libstorm.dylib" "$SRC/scripts/release/make_release_app.sh" "$SRC" "$DEPS" "$FC" "$OUT"
APP="$OUT/reFrozen.app"

step "release checks"
/usr/bin/python3 -I "$SRC/scripts/release/check_release.py" "$APP" | tee "$OUT/check_release.txt"

step "dmg"
/usr/bin/python3 -I "$SRC/scripts/release/make_dmg.py" "$SRC" "$APP" "$OUT/reFrozen-$VERSION.dmg"

step "checksums and manifest"
(cd "$OUT" && shasum -a 256 "reFrozen-$VERSION.dmg" > SHA256SUMS)
{
  echo "reFrozen $VERSION release candidate"
  echo "commit $SHA"
  echo "x86recomp $X86_BASE + patches, tree $X86_TREE"
  echo "kit stamp $(cat "$APP/Contents/Resources/kit/stamp.txt")"
  echo "built $(date -u +%Y-%m-%dT%H:%M:%SZ) on $(sw_vers -productName) $(sw_vers -productVersion), $(/usr/bin/xcrun clang --version | head -1)"
  echo "dependencies:"; ls "$DEPS/licenses"
  echo "files:"; (cd "$APP/.." && find reFrozen.app -type f | sort | while read -r f; do
    echo "$(shasum -a 256 "$f" | cut -c1-64) $(stat -f %z "$f") $f"; done)
} > "$OUT/MANIFEST.txt"
cat "$OUT/SHA256SUMS"
step "release candidate done: $OUT"
