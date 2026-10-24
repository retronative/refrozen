# AGENTS.md

reFrozen: a static recompilation of *Warcraft III: The Frozen Throne* 1.26a (x86 Win32) to
native arm64 macOS, aimed at playing *DotA Allstars* v6.83. The method and conventions follow
ReCarbon (`../recarbon`); reusable lessons are in `../game-port-knowledge`.

## Workspace

| Path | Role | Rules |
|---|---|---|
| `../recarbon/` | Precedent port (Xbox 360 → arm64) | **Read-only.** Learn from its process, docs and validation; never copy its title-specific hooks or addresses. |
| `../game-port-knowledge/` | Port knowledge base | Read `INDEX.md` and `general/bring-up-checklist.md` before each stage. Follow its `AGENTS.md` to add knowledge. |
| `../DOTA/` | The player's own game installers, client pack and maps | **Read-only.** Never commit anything from it. |
| `game/` | Extracted tomes, 1.26a oracle binaries (`oracle-1.26a/`), Ghidra project, symbols, generated code | git-ignored, proprietary-derived |
| `tools/` | x86recomp (pinned + patches), Wine (dev oracle only) | git-ignored |
| `patches/x86recomp/` | Our x86recomp patches 0001–0005, applied in order by `scripts/setup_tools.sh` | Each with hand-computed tests (`tests/test_lifter_patches.py`, x86recomp's `lift_atomic_test`) that fail under mutation. A patch is a diff against the tree with the earlier ones applied. |
| `config/` | Lifter manifests per module (`<module>.manifest`) and `unreachable.tsv` | Addresses and evidence only, no game bytes. Every entry says why. |
| `scripts/` | Install/patch, lift (`lift.sh`), audit (`validate_lift.py`), Ghidra scripts (`ghidra/`), map checks | |
| `reference/` | Feasibility, roadmap, research (`research/`) | |

## Commands

```sh
scripts/setup_tools.sh   # x86recomp (refrozen branch) + build/mpq_extract, bnupdate_patch (idempotent)
ctest --test-dir tools/x86recomp/out/build/debug   # "pacing" is a known timing flake (FEASIBILITY §7)
/opt/homebrew/bin/python3 -I tests/test_lifter_patches.py
# Per module (symbols dir names: war3 game storm mss32 mp3dec_asi mssfast_m3d msseax2_m3d
# mssdolby_m3d reverb3_flt), e.g. game.dll: Ghidra analysis + exports (JDK 25, ~4 min for game.dll),
JAVA_HOME=/opt/homebrew/opt/openjdk@25 MAXMEM=8G /opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless \
  game/ghidra reFrozen -import game/native-install/game.dll -overwrite \
  -scriptPath tools/x86recomp/tools/ghidra \
  -postScript ExportFunctions.java game/symbols/game/functions.tsv \
  -postScript ExportJumpTables.java game/symbols/game/jumptables.tsv
# ... the instruction listing for the audit (read-only, after analysis),
JAVA_HOME=/opt/homebrew/opt/openjdk@25 /opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless \
  game/ghidra reFrozen -process game.dll -noanalysis -readOnly \
  -scriptPath scripts/ghidra -postScript ExportInstructions.java game/symbols/game
# ... and exports/imports.
PATH=/opt/homebrew/opt/llvm/bin:$PATH /opt/homebrew/bin/python3 -I \
  tools/x86recomp/tools/pe_symbols.py game/native-install/game.dll --out game/symbols/game
scripts/lift.sh          # all nine modules, one run -> game/generated/war3
/opt/homebrew/bin/python3 -I scripts/validate_lift.py --generated game/generated/war3 \
  --unreachable config/unreachable.tsv \
  --module game/native-install/war3.exe game/symbols/war3 \
  --module game/native-install/game.dll game/symbols/game \
  --module game/native-install/Storm.dll game/symbols/storm \
  --module game/native-install/Mss32.dll game/symbols/mss32 \
  --module game/native-install/redist/miles/Mp3dec.asi game/symbols/mp3dec_asi \
  --module game/native-install/redist/miles/Mssfast.m3d game/symbols/mssfast_m3d \
  --module game/native-install/redist/miles/Msseax2.m3d game/symbols/msseax2_m3d \
  --module game/native-install/redist/miles/Mssdolby.m3d game/symbols/mssdolby_m3d \
  --module game/native-install/redist/miles/Reverb3.flt game/symbols/reverb3_flt
```

```sh
# Native install + 1.26a patch (the player's path; no Wine), optional check against the oracle:
/opt/homebrew/bin/python3 -I scripts/native_install.py --roc "<RoC installer>" --tft "<TFT installer>" \
  --patch "<War3TFT_126a_English.exe>" --out game/native-install [--verify "<oracle install>"]
/opt/homebrew/bin/python3 -I tests/test_bnupdate_patch.py
/opt/homebrew/bin/python3 -I scripts/map_check.py "<map.w3x>" game/native-install   # pjass in tools/pjass
scripts/wine_loadtest.sh game/wine-oracle 'Maps\Download\<map>.w3x' 60 game/loadtest/<name>  # dev oracle
```

- Embedded executables found in maps (e.g. iCCup's `dota.dll`) are inspected statically only:
  never run them, under Wine or otherwise.
- After changing a patch, delete the `refrozen` branch in `tools/x86recomp` and re-run
  `setup_tools.sh`. Lifter output must not change unintentionally: diff `game/generated/` before
  and after any lifter change, and keep two lifts byte-identical.
- `validate_lift.py` must stay HARD PASS. Unimplemented sites may only remain in functions listed
  in `config/unreachable.tsv` with evidence that they cannot run; they stay fatal at run time.

## Conventions

- Milestones (`reference/ROADMAP.md`) are gated. Don't start the next one without the user's
  approval. A criterion passes only when observed, never inferred.
- Label claims in reference docs as in game-port-knowledge: VERIFIED, OBSERVED, HYPOTHESIS,
  FALSIFIED, UNRESOLVED.
- Fix recompiler problems with real fixes (config, function bounds, documented tool patches).
  Never suppress errors.
- Every new instruction gets hand-computed tests, with expected values from the ISA manual,
  never from the recompiler's output.
- Python runs with `/opt/homebrew/bin/python3 -I` on anything that reads game files.

## CD keys and distribution

- The game's CD/install-key flow stays as the original implements it; the port doesn't bypass it.
- Development uses the test keys from the player's readme in `../DOTA/`. Never copy any key into
  this repository, a log, a commit or a doc.
- A distribution never includes a CD key, game code (original or recompiled), assets or maps.
- The player's pipeline is native macOS only: no Wine, VM or Windows tools to install, extract or
  patch their game. Wine (`tools/wine/`) is a development oracle only, e.g. to produce reference
  1.26a binaries that the native installer must reproduce byte for byte.

## Git

- One atomic commit per verified logical change; Conventional Commits, single-line messages,
  no co-author trailers. Review `git status`/`git diff` first.
- Never commit game data, maps (`*.w3x`, `*.w3m`), MPQs, executables, generated code, `game/`,
  `tools/` or build output.
- Commit locally only. Never push, amend or rewrite history without approval.
- Record debugging attempts and findings in `WORKLOG.local.md` (untracked, git-ignored).
