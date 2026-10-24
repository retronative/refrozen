#!/usr/bin/env bash
# Build the toolchain into tools/ and build/ (git-ignored). Safe to re-run.
#
#   scripts/setup_tools.sh
#
# - x86recomp at a pinned upstream commit + patches/x86recomp/*.patch
#   (branch "refrozen"): recomp_lift and the runtime libraries.
# - build/mpq_extract (scripts/mpq_extract.c on StormLib).
#
# Needs (Homebrew): git cmake ninja pkgconf llvm sdl3 ffmpeg glslang
# spirv-cross stormlib. Ghidra (brew install ghidra) for the function export.
# After changing a patch, delete the "refrozen" branch in tools/x86recomp and
# re-run: patches are applied only when the branch is missing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
LLVM_ROOT="${LLVM_ROOT:-/opt/homebrew/opt/llvm}"
X86RECOMP_BASE=ad1b16b30b3cc049e47a1ebbf96e8066b32191e1   # JTM-rootstorm/x86recomp main, 2026-10-19

mkdir -p "$TOOLS" "$ROOT/build"

if [ ! -d "$TOOLS/x86recomp" ]; then
  git clone -q https://github.com/JTM-rootstorm/x86recomp.git "$TOOLS/x86recomp"
fi
cd "$TOOLS/x86recomp"
if ! git rev-parse -q --verify refrozen >/dev/null; then
  git checkout -q -b refrozen "$X86RECOMP_BASE"
  for p in "$ROOT"/patches/x86recomp/*.patch; do git apply "$p"; done
  git add -A
  git -c user.name="reFrozen setup" -c user.email=setup@refrozen.invalid \
    commit -q -m "reFrozen patches"
fi
cmake --preset debug -DRECOMP_LLVM_ROOT="$LLVM_ROOT" > /dev/null
cmake --build --preset debug

clang -O2 -Wall -I/opt/homebrew/opt/stormlib/include "$ROOT/scripts/mpq_extract.c" \
  -L/opt/homebrew/opt/stormlib/lib -lstorm -o "$ROOT/build/mpq_extract"
clang -O2 -Wall -Wextra "$ROOT/scripts/bnupdate_patch.c" -o "$ROOT/build/bnupdate_patch"
