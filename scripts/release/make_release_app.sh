#!/bin/bash
# reFrozen.app for a release: the first-run setup (app/setup) as the app,
# the kit in Contents/Resources/kit (launcher, lifter, runtime libraries,
# SDL3 and StormLib from the source-built dependencies, the lifted code's
# headers, the lift configuration, the installer and builder scripts, the
# typefaces, the stamp), the icon, and reFrozen's licence with every
# dependency's. No game code or data: the game is installed and built on the
# player's Mac.
#
#   scripts/release/make_release_app.sh <repo with build/main> <deps prefix> <fetchcontent dir> <out dir>
#
# Every binary loads its libraries from the kit (@executable_path/../lib),
# loses its debug symbols (no build paths) and is ad hoc signed, then the app.
set -euo pipefail
ROOT=$(cd "$1" && pwd) DEPS=$(cd "$2" && pwd) FC=$(cd "$3" && pwd) OUT=$4
VERSION=$(cat "$ROOT/VERSION")  # the release version, one setting
BUILD="$ROOT/build/main"
X86="$ROOT/tools/x86recomp"
APP="$OUT/reFrozen.app"
KIT="$APP/Contents/Resources/kit"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$KIT"/{bin,lib,include/runtime,src,config,scripts,resources}

# The kit.
cp "$BUILD/refrozen" "$BUILD/x86recomp/tools/lifter/recomp_lift" "$ROOT/build/bnupdate_patch" "$KIT/bin/"
cp "$BUILD"/x86recomp/*.dylib "$KIT/lib/"
cp "$DEPS/lib/libSDL3.0.dylib" "$DEPS/lib/libstorm.dylib" "$KIT/lib/" 2>/dev/null || {
  cp "$(ls "$DEPS"/lib/libSDL3*.dylib | head -1)" "$KIT/lib/libSDL3.0.dylib"
  cp "$(ls "$DEPS"/lib/libstorm*.dylib | head -1)" "$KIT/lib/libstorm.dylib"
}
for h in ctx lifted simd64 sse x87; do cp "$X86/src/runtime/$h.h" "$KIT/include/runtime/"; done
cp "$X86/src/runtime/lifted_table.cpp" "$ROOT/src/replaced.cpp" "$KIT/src/"
cp -R "$ROOT/config/symbols" "$ROOT"/config/*.manifest "$ROOT/config/jumptable_corrections.tsv" "$KIT/config/"
cp "$X86/tools/pe_symbols.py" "$ROOT/scripts/jumptable_corrections.py" "$ROOT/scripts/native_install.py" \
  "$ROOT/scripts/font_keydata.py" "$ROOT/scripts/poc/build_module.sh" "$KIT/scripts/"
sed -n 's/^REFROZEN_MODULE_STAMP:STRING=//p' "$BUILD/CMakeCache.txt" > "$KIT/stamp.txt"
cp "$ROOT"/.website/public/fonts/{cinzel-latin-wght-normal,cormorant-garamond-latin-wght-normal,cormorant-garamond-latin-wght-italic,inter-latin-wght-normal}.woff2 \
  "$ROOT"/.website/public/fonts/OFL-*.txt "$KIT/resources/"
cp "$ROOT/.website/public/icon-512.png" "$KIT/resources/icon.png"

# The app: the setup, its icon, Info.plist.
/usr/bin/xcrun swiftc -O -swift-version 5 -target arm64-apple-macos14.0 -parse-as-library -module-name reFrozenSetup \
  -file-prefix-map "$ROOT=refrozen" "$ROOT"/app/setup/*.swift -o "$APP/Contents/MacOS/reFrozen"
cp "$ROOT/assets/icon/reFrozen.icns" "$APP/Contents/Resources/"
STAMP=$(cat "$KIT/stamp.txt")
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>reFrozen</string>
  <key>CFBundleIdentifier</key><string>org.retronative.refrozen</string>
  <key>CFBundleName</key><string>reFrozen</string>
  <key>CFBundleDisplayName</key><string>reFrozen</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$STAMP</string>
  <key>CFBundleIconFile</key><string>reFrozen</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.games</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSLocalNetworkUsageDescription</key><string>reFrozen uses your local network to find, host and join Warcraft III LAN games with other Macs on the same network.</string>
  <key>NSHumanReadableCopyright</key><string>reFrozen is free software under the GNU GPL v3 or later. Not affiliated with Blizzard Entertainment.</string>
</dict>
</plist>
PLIST

# Licences: reFrozen's and every dependency the app ships or links.
L="$APP/Contents/Resources/licenses"
mkdir -p "$L/third-party"
cp "$ROOT/COPYING" "$ROOT/NOTICE" "$ROOT/THIRD_PARTY_NOTICES.md" "$L/"
cp -R "$ROOT/LICENSES" "$L/LICENSES"
cp -R "$DEPS"/licenses/* "$L/third-party/"
mkdir -p "$L/third-party/SoftFloat" "$L/third-party/Zydis"
cp "$FC"/softfloat/COPYING* "$L/third-party/SoftFloat/"
cp "$FC/zydis/LICENSE" "$L/third-party/Zydis/LICENSE"
cp "$FC/zydis/dependencies/zycore/LICENSE" "$L/third-party/Zydis/LICENSE-zycore"

# Libraries from the kit only; no debug symbols (they name build paths).
for f in "$KIT/bin/refrozen" "$KIT/bin/recomp_lift"; do
  for r in $(otool -l "$f" | awk '/LC_RPATH/ {getline; getline; print $2}'); do install_name_tool -delete_rpath "$r" "$f"; done
  install_name_tool -add_rpath @executable_path/../lib "$f"
done
for f in "$KIT"/lib/*.dylib; do
  for r in $(otool -l "$f" | awk '/LC_RPATH/ {getline; getline; print $2}'); do install_name_tool -delete_rpath "$r" "$f"; done
done
install_name_tool -id @rpath/libstorm.dylib "$KIT/lib/libstorm.dylib"
strip -S "$KIT"/bin/* "$KIT"/lib/*.dylib "$APP/Contents/MacOS/reFrozen" 2>/dev/null || true

# Ad hoc signatures, inside out. The game launcher gets a stable identifier
# (its embedded Info.plist's): macOS keys local network permission to it.
codesign --force -s - "$KIT"/lib/*.dylib
for f in "$KIT"/bin/*; do
  if [ "$(basename "$f")" = refrozen ]; then
    codesign --force -s - --identifier org.retronative.refrozen.game "$f"
  else
    codesign --force -s - "$f"
  fi
done
codesign --force -s - "$APP"
codesign --verify --deep --strict "$APP"
echo "app: $APP ($(du -sh "$APP" | cut -f1)), kit stamp $STAMP"
