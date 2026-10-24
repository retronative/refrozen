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
| `patches/x86recomp/` | Our x86recomp patches, applied by `scripts/setup_tools.sh` | Each with hand-computed tests in x86recomp's `tests/` |
| `scripts/` | `setup_tools.sh`, `mpq_extract.c` | |
| `reference/` | Feasibility, roadmap, research (`research/`) | |

## Commands

```sh
scripts/setup_tools.sh   # x86recomp (refrozen branch) + build/mpq_extract (idempotent)
ctest --test-dir tools/x86recomp/out/build/debug
# Ghidra export (JDK 25), then exports/imports, then lift; per module, e.g. Storm.dll:
JAVA_HOME=/opt/homebrew/opt/openjdk@25 /opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless \
  game/ghidra reFrozen -import game/oracle-1.26a/Storm.dll -overwrite \
  -scriptPath tools/x86recomp/tools/ghidra \
  -postScript ExportFunctions.java game/symbols/storm/functions.tsv \
  -postScript ExportJumpTables.java game/symbols/storm/jumptables.tsv
PATH=/opt/homebrew/opt/llvm/bin:$PATH /opt/homebrew/bin/python3 -I \
  tools/x86recomp/tools/pe_symbols.py game/oracle-1.26a/Storm.dll --out game/symbols/storm
tools/x86recomp/out/build/debug/tools/lifter/recomp_lift --exe game/oracle-1.26a/Storm.dll \
  --symbols game/symbols/storm --manifest game/symbols/storm/lifter.manifest --out game/generated/storm
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
  and after any lifter change.

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
