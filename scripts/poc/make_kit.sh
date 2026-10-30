#!/bin/bash
# Stages what the app would carry for its first-run setup: the launcher and
# lifter, the runtime libraries, the headers the lifted code includes, the
# lift configuration and scripts, the stamp, and the installer (its scripts,
# bnupdate_patch and StormLib; StormLib is Homebrew's until release
# dependencies are built from pinned sources).
# reFrozen's own files only: no game code, data or keys.
#
#   scripts/poc/make_kit.sh <build dir, configured with REFROZEN_DYNAMIC_MODULE=ON> <kit dir>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD=$(cd "$1" && pwd) KIT=$2
X86="$ROOT/tools/x86recomp"
rm -rf "$KIT" && mkdir -p "$KIT"/{bin,lib,include/runtime,src,config,scripts}
cp "$BUILD/refrozen" "$BUILD/x86recomp/tools/lifter/recomp_lift" "$ROOT/build/bnupdate_patch" "$KIT/bin/"
cp "$(realpath /opt/homebrew/opt/stormlib/lib/libstorm.dylib)" "$KIT/lib/libstorm.dylib"
cp "$BUILD"/x86recomp/*.dylib "$KIT/lib/"
for h in ctx lifted simd64 sse x87; do cp "$X86/src/runtime/$h.h" "$KIT/include/runtime/"; done
cp "$X86/src/runtime/lifted_table.cpp" "$ROOT/src/replaced.cpp" "$KIT/src/"
cp -R "$ROOT/config/symbols" "$ROOT"/config/*.manifest "$ROOT/config/jumptable_corrections.tsv" "$KIT/config/"
cp "$X86/tools/pe_symbols.py" "$ROOT/scripts/jumptable_corrections.py" "$ROOT/scripts/native_install.py" \
  "$ROOT/scripts/font_keydata.py" "$KIT/scripts/"
sed -n 's/^REFROZEN_MODULE_STAMP:STRING=//p' "$BUILD/CMakeCache.txt" > "$KIT/stamp.txt"
cp "$ROOT/scripts/poc/build_module.sh" "$KIT/scripts/"
# The setup window's identity: the site's typefaces (with their licences) and the app icon.
mkdir -p "$KIT/resources"
cp "$ROOT"/.website/public/fonts/{cinzel-latin-wght-normal,cormorant-garamond-latin-wght-normal,cormorant-garamond-latin-wght-italic,inter-latin-wght-normal}.woff2 \
  "$ROOT"/.website/public/fonts/OFL-*.txt "$KIT/resources/"
cp "$ROOT/.website/public/icon-512.png" "$KIT/resources/icon.png"
# Libraries are found next to the executables, never in the build tree.
for f in "$KIT/bin/refrozen" "$KIT/bin/recomp_lift"; do  # bnupdate_patch: no rpath
  for r in $(otool -l "$f" | awk '/LC_RPATH/ {getline; getline; print $2}'); do
    install_name_tool -delete_rpath "$r" "$f"
  done
  install_name_tool -add_rpath @executable_path/../lib "$f"
done
codesign -f -s - "$KIT"/bin/* "$KIT"/lib/*.dylib 2>/dev/null
echo "kit: $KIT ($(du -sh "$KIT" | cut -f1)), stamp $(cat "$KIT/stamp.txt")"
