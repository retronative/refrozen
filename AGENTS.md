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
| `game/` | Extracted tomes, 1.26a oracle binaries (`oracle-1.26a/`), Ghidra project, symbols, generated code, launch logs (`attempts/`), reports | git-ignored, proprietary-derived |
| `tools/` | x86recomp (pinned + patches), Wine (dev oracle only) | git-ignored |
| `patches/x86recomp/` | Our x86recomp patches 0001–0028, applied in order by `scripts/setup_tools.sh` | Each with tests that fail under mutation: lifter patches in `tests/test_lifter_patches.py` (hand-computed) and x86recomp's `lift_atomic_test`; runtime/loader/HLE patches in `tests/test_loader.py` and `tests/test_win32.py`. A patch is a diff against the tree with the earlier ones applied. |
| `CMakeLists.txt`, `src/` | The game project: `refrozen` = lifted code + x86recomp runtime (`GameConfig` in `src/main.cpp`) | Lifted DLLs listed in dependency order. Win32 functions are added to the runtime (a patch), never stubbed to succeed. |
| `config/` | Lifter manifests per module (`<module>.manifest`), `unreachable.tsv`, `jumptable_corrections.tsv`, and the pinned lift input `symbols/<module>/functions.tsv`, `jumptables.tsv` | Addresses, flags and evidence only, no game bytes. Every manifest entry and correction says why. Refresh `symbols/` only deliberately (Ghidra varies between runs) and record the new lift hash. |
| `scripts/` | Install/patch (incl. the CD-key step, `font_keydata.py`), lift (`lift.sh`, `jumptable_corrections.py`), audit (`validate_lift.py`), import coverage (`import_coverage.py`), launches (`run_attempt.sh`, `m3_accept.sh`, `m4_accept.sh`), Wine oracle (`oracle_menus.sh`, `oracle_keys.c`, `m4_compare.sh`, `wine_loadtest.sh`), Ghidra scripts (`ghidra/`), map checks | |
| `tests/` | Regression tests and the mutation gate (`mutate.py`, registry `mutants.py`) | See "Mutation gate". |
| `reference/` | Feasibility, roadmap, research (`research/`) | |

## Commands

```sh
scripts/setup_tools.sh   # x86recomp (refrozen branch) + build/mpq_extract, bnupdate_patch (idempotent)
ctest --test-dir tools/x86recomp/out/build/debug   # "pacing" is a known timing flake (FEASIBILITY §7)
/opt/homebrew/bin/python3 -I tests/test_lifter_patches.py
/opt/homebrew/bin/python3 -I tests/test_loader.py
/opt/homebrew/bin/python3 -I tests/test_win32.py              # mode N broadcasts on the LAN: run attached
/opt/homebrew/bin/python3 -I tests/test_gl_context.py         # x86recomp's gl_fog/gl_texture tests
/opt/homebrew/bin/python3 -I tests/test_font_keydata.py       # needs game/wine-oracle + the readme
/opt/homebrew/bin/python3 -I tests/test_jumptable_corrections.py
/opt/homebrew/bin/python3 -I tests/test_run_on_stack.py      # patch 0022: the main guest stack's end frame
/opt/homebrew/bin/python3 -I tests/mutate.py [--milestone M3]  # the mutation gate (scratch tree): sign-off
/opt/homebrew/bin/python3 -I tests/mutate.py --changed main --focused  # focused gate while working
/opt/homebrew/bin/python3 -I tests/test_mutate.py            # the gate's own rules
/opt/homebrew/bin/python3 -I tests/test_lan_broadcast.py     # patch 0025: LAN discovery broadcast targets
# Per module (symbols dir names: war3 game storm mss32 msvcr80 ijl15 mp3dec_asi mssfast_m3d
# msseax2_m3d mssdolby_m3d reverb3_flt), e.g. game.dll: Ghidra analysis + exports (JDK 25, ~4 min for game.dll),
JAVA_HOME=/opt/homebrew/opt/openjdk@25 MAXMEM=8G /opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless \
  game/ghidra reFrozen -import game/native-install/game.dll -overwrite \
  -scriptPath tools/x86recomp/tools/ghidra \
  -postScript ExportFunctions.java game/symbols/game/functions.tsv \
  -postScript ExportJumpTables.java game/symbols/game/jumptables.tsv
# ... the instruction listing for the audit (read-only, after analysis),
JAVA_HOME=/opt/homebrew/opt/openjdk@25 /opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless \
  game/ghidra reFrozen -process game.dll -noanalysis -readOnly \
  -scriptPath scripts/ghidra -postScript ExportInstructions.java game/symbols/game
# game/symbols/ (Ghidra output) is development-only: the audit's instructions.tsv/noncode.tsv,
# and the source when refreshing config/symbols/ on purpose. lift.sh runs pe_symbols.py itself.
scripts/lift.sh          # all eleven modules from config/symbols + pe_symbols -> game/generated/war3
/opt/homebrew/bin/python3 -I scripts/validate_lift.py --generated game/generated/war3 \
  --unreachable config/unreachable.tsv \
  --module game/native-install/war3.exe game/symbols-lift/war3 \
  --module game/native-install/game.dll game/symbols-lift/game \
  --module game/native-install/Storm.dll game/symbols-lift/storm \
  --module game/native-install/Mss32.dll game/symbols-lift/mss32 \
  --module game/native-install/msvcr80.dll game/symbols-lift/msvcr80 \
  --module game/native-install/ijl15.dll game/symbols-lift/ijl15 \
  --module game/native-install/redist/miles/Mp3dec.asi game/symbols-lift/mp3dec_asi \
  --module game/native-install/redist/miles/Mssfast.m3d game/symbols-lift/mssfast_m3d \
  --module game/native-install/redist/miles/Msseax2.m3d game/symbols-lift/msseax2_m3d \
  --module game/native-install/redist/miles/Mssdolby.m3d game/symbols-lift/mssdolby_m3d \
  --module game/native-install/redist/miles/Reverb3.flt game/symbols-lift/reverb3_flt
# Build and launch (re-run cmake after lift.sh; runtime-only rebuilds take seconds):
cmake -S . -B build/main -G Ninja -DCMAKE_BUILD_TYPE=Debug -DRECOMP_LLVM_ROOT=/opt/homebrew/opt/llvm
ninja -C build/main refrozen
/opt/homebrew/bin/python3 -I scripts/import_coverage.py --tsv game/reports/import_coverage.tsv
scripts/run_attempt.sh <name> [secs]   # log in game/attempts/<name>.log; exit 0 iff GameMain reached
REFROZEN_TRACE=1 scripts/run_attempt.sh <name>-trace 120   # every HLE call, DllMain order
scripts/m3_accept.sh [launches] [secs]  # M3: main menu loop, no fatal, frames presented (defaults 3, 60)
# Background runs never get host focus: REFROZEN_TEST_FOCUS=follow activates the game guest-side.
# REFROZEN_SHOT_EVERY=N REFROZEN_SHOT_DIR=<dir> saves every Nth presented frame (local only: game imagery).
# REFROZEN_TEST_INPUT=<file> replays scripted input (key, click, dblclick, goto, move, focus, minimize,
# restore, resize, and "shot <name>": the next frame as <SHOT_DIR>/<name>.bmp, independent of host load).
scripts/m4_accept.sh [launches] [secs]  # M4: tests/m4/native_path.txt, fresh profile each (defaults 3, 110)
# Development oracle (Wine): the same menu path by keys on both of the client's renderers, compared.
scripts/oracle_menus.sh <name> d3d|opengl tests/m4/oracle_path.txt [secs]   # game/attempts/oracle-<name>/
scripts/m4_compare.sh <native shots> <oracle d3d dir> <oracle gl dir> <out dir>
```

- Scripted menu runs never open Battle.net or Local Area Network (network-facing: M7, the user's
  approval first) and never press Start Game or Return on the Custom Game screen (loading a map
  is gameplay: M5). Oracle runs work on APFS clones; `game/wine-oracle` is the native installer's
  `--verify` reference and is never written.

```sh
# Native install + 1.26a patch (the player's path; no Wine), optional check against the oracle.
# Asks for the two CD keys as the installer does (stdin when not a terminal); --owner is the name.
/opt/homebrew/bin/python3 -I scripts/native_install.py --roc "<RoC installer>" --tft "<TFT installer>" \
  --patch "<War3TFT_126a_English.exe>" --out game/native-install --owner "<name>" [--verify "<oracle install>"]
/opt/homebrew/bin/python3 -I tests/test_bnupdate_patch.py
/opt/homebrew/bin/python3 -I scripts/map_check.py "<map.w3x>" game/native-install   # pjass in tools/pjass
scripts/wine_loadtest.sh game/wine-oracle 'Maps\Download\<map>.w3x' 60 game/loadtest/<name>  # dev oracle
```

- Embedded executables found in maps (e.g. iCCup's `dota.dll`) are inspected statically only:
  never run them, under Wine or otherwise.
- iCCup (M8): no work without the user's approval and iCCup's official cooperation; never bypass,
  disable or work around its anti-cheat or client-integrity checks; no network tests against its
  services before M8 is approved.
- After changing a patch, delete the `refrozen` branch in `tools/x86recomp` and re-run
  `setup_tools.sh`. Lifter output must not change unintentionally: diff `game/generated/` before
  and after any lifter change, and keep two lifts byte-identical.
- `validate_lift.py` must stay HARD PASS. Unimplemented sites may only remain in functions listed
  in `config/unreachable.tsv` with evidence that they cannot run; they stay fatal at run time.

## Mutation gate (mandatory from M3; ReCarbon's practice)

- Every new or changed runtime behaviour (Win32 semantics, error handling, memory operations,
  module loading, threading, synchronization, game initialization; lifter and install steps too)
  gets a focused test whose expected values are derived independently: manuals and MSDN, Wine's
  conformance tests or ReactOS where named, published vectors, the original tools' output. Never
  from our own code.
- Each such change gets mutants in `tests/mutants.py` (file, exact old/new text, the test, the
  check expected to fail). `tests/mutate.py` plants them in a scratch copy (`build/mutate/`, never
  the real tree), checks the baseline passes first, and classifies each mutant KILLED,
  KILLED-OTHER, TIMEOUT, SURVIVED, EQUIVALENT (documented, with the reason it cannot differ) or
  INVALID (does not apply or does not build: never a kill).
- A milestone is not signed off until the gate passes for its mutants (all KILLED or documented
  EQUIVALENT; survivors fixed by better tests, not weaker mutants) and `reference/TEST_COVERAGE.md`
  records each mutant, its expected failure, the observed result and any survivors. Earlier
  milestones' mutants stay in the registry and are re-run.
- While working, `tests/mutate.py --changed <ref> --focused` runs only the mutants the changes can
  affect (their files, patched files, changed or importing tests, changed registry entries,
  `CHANGE_SCOPE`), each test_win32 mutant on the `--modes` group that prints its expected check
  (`WIN32_GROUPS`; the group's unmutated run must print that check) with the compiled test
  program reused while its inputs are unchanged. Only a kill by the expected check counts there;
  anything else is decided by the whole test. Run it attached (mode N). It does not replace the
  default run, which signs off milestones and releases. A new check-name prefix goes into
  `WIN32_GROUPS`, a new indirect dependency into `CHANGE_SCOPE` or `TEST_IMPORTS`.
- Tests stay deterministic; never weaken an assertion, suppress a failure or change production
  behaviour only to satisfy a test.

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
