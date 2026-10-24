#!/usr/bin/env bash
# Lift every Warcraft III 1.26a module in one recomp_lift run (M1; msvcr80.dll added in M2).
#
#   scripts/lift.sh [install dir] [out dir]   # defaults: game/native-install game/generated/war3
#
# Inputs per module, assembled in game/symbols-lift/<module>/:
#   - functions.tsv, jumptables.tsv: pinned in config/symbols/<module>/ (addresses and flags from
#     a Ghidra 12.2 analysis; Ghidra's analysis of game.dll varies between runs, so the lift
#     input is fixed here, see FEASIBILITY §7). Players need no Ghidra.
#   - exports.tsv, imports.tsv: from the player's own binary (tools/x86recomp/tools/pe_symbols.py).
#   - instructions.tsv, noncode.tsv: copied from game/symbols/<module>/ when present (development
#     only, for scripts/validate_lift.py).
# Manifests are config/<module>.manifest. The output is generated from the player's own files:
# git-ignored, never committed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="${1:-$ROOT/game/native-install}"
OUT="${2:-$ROOT/game/generated/war3}"
PINNED="$ROOT/config/symbols"
LIFTSYM="$ROOT/game/symbols-lift"
DEVSYM="$ROOT/game/symbols"
CFG="$ROOT/config"
PYTHON=/opt/homebrew/bin/python3

# module file (relative to the install) : symbols/config name
MODULES=(
  "war3.exe:war3" "game.dll:game" "Storm.dll:storm" "Mss32.dll:mss32" "msvcr80.dll:msvcr80"
  "redist/miles/Mp3dec.asi:mp3dec_asi" "redist/miles/Mssfast.m3d:mssfast_m3d"
  "redist/miles/Msseax2.m3d:msseax2_m3d" "redist/miles/Mssdolby.m3d:mssdolby_m3d"
  "redist/miles/Reverb3.flt:reverb3_flt"
)
args=()
for i in "${!MODULES[@]}"; do
  file="${MODULES[$i]%%:*}" name="${MODULES[$i]##*:}"
  dir="$LIFTSYM/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  cp "$PINNED/$name/functions.tsv" "$PINNED/$name/jumptables.tsv" "$dir/"
  PATH="/opt/homebrew/opt/llvm/bin:$PATH" "$PYTHON" -I "$ROOT/tools/x86recomp/tools/pe_symbols.py" \
    "$INSTALL/$file" --out "$dir" > /dev/null
  for f in instructions.tsv noncode.tsv; do
    if [ -f "$DEVSYM/$name/$f" ]; then cp "$DEVSYM/$name/$f" "$dir/"; fi
  done
  [ "$i" = 0 ] && args+=(--exe "$INSTALL/$file") || args+=(--module "$INSTALL/$file")
  args+=(--symbols "$dir" --manifest "$CFG/$name.manifest")
done
rm -rf "$OUT"
mkdir -p "$OUT"
"$ROOT/tools/x86recomp/out/build/debug/tools/lifter/recomp_lift" "${args[@]}" --out "$OUT"
