#!/usr/bin/env bash
# Lift every Warcraft III 1.26a module in one recomp_lift run (M1).
#
#   scripts/lift.sh [install dir] [out dir]   # defaults: game/native-install game/generated/war3
#
# Needs scripts/setup_tools.sh and the Ghidra exports in game/symbols/<module>/
# (functions.tsv, jumptables.tsv; pe_symbols.py's exports.tsv, imports.tsv; see
# AGENTS.md). Manifests are config/<module>.manifest. The output is generated
# from the player's own files: git-ignored, never committed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="${1:-$ROOT/game/native-install}"
OUT="${2:-$ROOT/game/generated/war3}"
SYM="$ROOT/game/symbols"
CFG="$ROOT/config"

# module file (relative to the install) : symbols/config name
MODULES=(
  "war3.exe:war3" "game.dll:game" "Storm.dll:storm" "Mss32.dll:mss32"
  "redist/miles/Mp3dec.asi:mp3dec_asi" "redist/miles/Mssfast.m3d:mssfast_m3d"
  "redist/miles/Msseax2.m3d:msseax2_m3d" "redist/miles/Mssdolby.m3d:mssdolby_m3d"
  "redist/miles/Reverb3.flt:reverb3_flt"
)
args=()
for i in "${!MODULES[@]}"; do
  file="${MODULES[$i]%%:*}" name="${MODULES[$i]##*:}"
  [ "$i" = 0 ] && args+=(--exe "$INSTALL/$file") || args+=(--module "$INSTALL/$file")
  args+=(--symbols "$SYM/$name" --manifest "$CFG/$name.manifest")
done
rm -rf "$OUT"
mkdir -p "$OUT"
"$ROOT/tools/x86recomp/out/build/debug/tools/lifter/recomp_lift" "${args[@]}" --out "$OUT"
