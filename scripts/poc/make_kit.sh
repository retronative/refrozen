#!/bin/bash
# Stages what the app would carry for the first-run builder (proof of
# concept): the launcher and lifter, the runtime libraries, the headers the
# lifted code includes, the lift configuration and scripts, and the stamp.
# reFrozen's own files only: no game code, data or keys.
#
#   scripts/poc/make_kit.sh <build dir, configured with REFROZEN_DYNAMIC_MODULE=ON> <kit dir>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD=$(cd "$1" && pwd) KIT=$2
X86="$ROOT/tools/x86recomp"
rm -rf "$KIT" && mkdir -p "$KIT"/{bin,lib,include/runtime,src,config,scripts}
cp "$BUILD/refrozen" "$BUILD/x86recomp/tools/lifter/recomp_lift" "$KIT/bin/"
cp "$BUILD"/x86recomp/*.dylib "$KIT/lib/"
for h in ctx lifted simd64 sse x87; do cp "$X86/src/runtime/$h.h" "$KIT/include/runtime/"; done
cp "$X86/src/runtime/lifted_table.cpp" "$KIT/src/"
cp -R "$ROOT/config/symbols" "$ROOT"/config/*.manifest "$ROOT/config/jumptable_corrections.tsv" "$KIT/config/"
cp "$X86/tools/pe_symbols.py" "$ROOT/scripts/jumptable_corrections.py" "$KIT/scripts/"
sed -n 's/^REFROZEN_MODULE_STAMP:STRING=//p' "$BUILD/CMakeCache.txt" > "$KIT/stamp.txt"
# Libraries are found next to the executables, never in the build tree.
for f in "$KIT"/bin/*; do
  for r in $(otool -l "$f" | awk '/LC_RPATH/ {getline; getline; print $2}'); do
    install_name_tool -delete_rpath "$r" "$f"
  done
  install_name_tool -add_rpath @executable_path/../lib "$f"
done
codesign -f -s - "$KIT"/bin/* "$KIT"/lib/*.dylib 2>/dev/null
echo "kit: $KIT ($(du -sh "$KIT" | cut -f1)), stamp $(cat "$KIT/stamp.txt")"
