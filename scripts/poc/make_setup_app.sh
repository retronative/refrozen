#!/bin/bash
# A development reFrozen.app for trying the first-run setup (experimental;
# not the release packaging: no dmg, ad hoc signature, the kit's libraries
# still use Homebrew's SDL3, glslang and SPIRV-Tools).
#
#   scripts/poc/make_setup_app.sh <kit> <out dir>   # -> <out dir>/reFrozen.app
#
# Contents/MacOS/reFrozen is the setup (app/setup); Contents/Resources/kit
# is the kit (scripts/poc/make_kit.sh), where it looks for everything else.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
KIT=$(cd "$1" && pwd) OUT=$2
APP="$OUT/reFrozen.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
/usr/bin/xcrun swiftc -O -swift-version 5 -target arm64-apple-macos14.0 -parse-as-library \
  -module-name reFrozenSetup "$ROOT"/app/setup/*.swift -o "$APP/Contents/MacOS/reFrozen"
cp "$ROOT/assets/icon/reFrozen.icns" "$APP/Contents/Resources/"
cp -R "$KIT" "$APP/Contents/Resources/kit"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>reFrozen</string>
  <key>CFBundleIdentifier</key><string>org.retronative.refrozen.dev</string>
  <key>CFBundleName</key><string>reFrozen</string>
  <key>CFBundleDisplayName</key><string>reFrozen</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.1.0-dev</string>
  <key>CFBundleVersion</key><string>$(cat "$KIT/stamp.txt")</string>
  <key>CFBundleIconFile</key><string>reFrozen</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.games</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST
codesign --force --deep -s - "$APP" 2>/dev/null
codesign --verify --deep --strict "$APP"
echo "app: $APP ($(du -sh "$APP" | cut -f1)), kit stamp $(cat "$KIT/stamp.txt")"
