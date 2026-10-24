# reFrozen — Roadmap (x86 Win32 → Apple Silicon)

Every milestone is gated, as in ReCarbon. Starting each milestone needs the user's **explicit
approval**, even when the previous one passed. A milestone passes only when its acceptance
criteria are met **and observed**. Each milestone records **Evidence** (what was observed) and
**Verify** (how to reproduce it from a clean checkout plus your own game copy).

States: **Passed**, **Partial** (lists the unmet criteria), **Blocked** (root cause or the
unknown documented). Diagnosing a failure is progress; it does not pass a criterion.

**Order: offline first.** A playable local match comes first, then AI bots, then multiplayer.
Nothing network-facing is needed before M6.

## M0 — Correct input and feasibility *(Passed 2026-10-24, signed off by the user)*
- **Accept → Evidence** (details and commands in FEASIBILITY §1–6):
  - Hashes and header facts of every input binary → VERIFIED (§1, §2).
  - Native install + 1.26a patch reproduce the official installers + patcher (Wine oracle) →
    VERIFIED: `scripts/native_install.py --verify` PASS. 204 loose files byte-identical (incl.
    `war3.exe`, `game.dll`, `Storm.dll`); every file inside `war3.mpq`, `War3x.mpq`,
    `War3xLocal.mpq`, `War3Patch.mpq` identical except the 5 CD-key `font\font.*` entries (key step
    not implemented, see §6). Two runs byte-identical. `tests/test_bnupdate_patch.py` passes and
    fails under two mutations (§1).
  - Imports by DLL, classified → VERIFIED (§2).
  - Approach decision → approved by the user (fork x86recomp); `Storm.dll` falsification test
    passed (§3).
  - DotA on 1.26a → VERIFIED with actual loads in the official 1.26a client (§5): DotA 6.85oz LoD
    (pure JASS, 0 pjass errors) loads on 3/3 launches and reaches a running match; IMBA 3.86b
    loads. `DotA v6.83se.w3x` (and 6.83s) are iCCup native-plugin builds (`dota.dll` inside the
    map, 365-byte stub script): stock 1.26a crashes loading them, identically for both.
- **Verify:** `scripts/setup_tools.sh`; `python3 -I tests/test_bnupdate_patch.py`;
  `python3 -I scripts/native_install.py … --verify <oracle>`; `python3 -I scripts/map_check.py
  <map> game/native-install`; `scripts/wine_loadtest.sh` (dev oracle only).
- **Carried forward (not M0 blockers):** the CD-key encoding step; DirectShow intro movies (§6).
  DotA target decided by the user: **DotA 6.85oz LoD** (pure JASS); iCCup native-plugin maps,
  including 6.83se, deferred.

## M1 — Recompile all modules *(Passed 2026-10-24, signed off by the user)*
- **Scope:** war3.exe, game.dll, Storm.dll, Mss32.dll and the five Miles providers (Mp3dec.asi,
  Mssfast/Msseax2/Mssdolby.m3d, Reverb3.flt) in one lift at their preferred bases. Miles is
  recompiled rather than HLE'd (FEASIBILITY §8).
- **Accept → Evidence** (FEASIBILITY §7):
  - 0 unimplemented sites → **0 reachable**; 738 3DNow! sites in 4 Mp3dec functions shown
    unreachable on any CPU with WC3's Mss32 (`config/unreachable.tsv`), still fatal if reached.
    New instructions and lifter defects → patches 0001–0005, each with hand-computed end-to-end
    tests that fail under mutation (15 mutations).
  - Structural checks → `scripts/validate_lift.py` HARD PASS: every Ghidra function and export
    lifted; every relocated pointer into code and every unlifted Ghidra instruction explained
    (entries, labels, table data, operands of inline tables, or provably unreferenced code);
    jump tables resolved, completed (8) or recovered (8).
  - Byte-identical across two runs → tree hash `8a2a898d…de288`, end to end: Ghidra's analysis
    of game.dll varies between runs (2 dead functions, even single-threaded), so the lift input
    (function/jump-table address lists) is pinned in `config/symbols/` (user's decision); lifts
    from it, with or without Ghidra on the machine, are byte-identical.
  - Compiles for arm64 → all 220 files, 0 errors, 0 warnings, 238 s; objects define all
    90,974 lifted functions (not linked: M2).
- **Verify:** `scripts/setup_tools.sh`; `ctest --test-dir tools/x86recomp/out/build/debug`;
  `python3 -I tests/test_lifter_patches.py`; `scripts/lift.sh`;
  `python3 -I scripts/validate_lift.py --generated game/generated/war3 --unreachable
  config/unreachable.tsv --module … ` (all nine; AGENTS.md has the full command).
- **Risks carried to M2** (FEASIBILITY §7): static imports between lifted modules (Storm by
  ordinal, Mss32) must bind to the lifted DLLs, not HLE thunks; `DirectSoundCreate` HLE for
  Miles; run-time indirect jumps (2,535 `jmp reg` in game.dll) not checked statically; lock-free
  memory ordering not audited.

## M2 — Native link and process start *(Passed 2026-10-24, pending the user's sign-off)*
- **Scope:** a game project (`GameConfig`, `RunProcess`), strict import stubs generated from the
  imports, 0 unresolved symbols; the process reaches `GameMain` in `game.dll`. msvcr80.dll
  (the CRT war3.exe, game.dll and Storm import) is lifted as a 10th module.
- **Accept → Evidence** (FEASIBILITY §9):
  - Links natively → `build/main/refrozen`, one arm64 executable (lifted code + runtime), 0
    undefined symbols.
  - Cross-module imports → x86recomp patch 0007: static imports bind to the lifted exports by
    name or ordinal; all 675 resolve (`scripts/import_coverage.py` exit 0), including 163 Storm
    ordinals and 318 Mss32/Miles functions. A missing export or a misordered module stops at load.
  - Original addresses, conventions, initialization order → every module at its lifted
    (preferred) base; DllMains run dependencies-first before the EXE entry (traced: msvcr80,
    Storm, Mss32, then game.dll on war3.exe's LoadLibrary); static loads pinned; calls go through
    the lifted functions with their original stack conventions.
  - Strict stubs → 359 Win32 imports without a handler stop the process with
    `unimplemented import <dll>!<name>` when called; nothing returns a made-up success. Five
    functions met before GameMain were implemented to their Win32 behaviour (patch 0008).
  - Indirect jump validation → `Dispatch` stops on a target outside lifted code or not a function
    entry, naming `module+offset` of both ends, the enclosing lifted function and the manifest fix.
  - Reaches GameMain → **OBSERVED** on the final tree in two launches (`m2-final-1/2`):
    `probe: GameMain (6F009850) ecx 6F000000 args 6F000000 …`, called by war3.exe after
    `GetProcAddress(game.dll, "GameMain")`. Guest output identical between launches.
  - Tests → `tests/test_loader.py` (synthetic EXE + 3 DLLs through lifter, runtime and loader;
    10 mutations caught); SSE2 checks in `tests/test_lifter_patches.py` (4 mutations caught);
    ctest, `test_bnupdate_patch.py` still pass. Lift byte-identical twice (tree hash
    `5da168f8…79f85`), `validate_lift.py` HARD PASS on all ten modules.
- **Verify:** FEASIBILITY §9 (`setup_tools.sh`, `test_loader.py`, `lift.sh`, `cmake`/`ninja`,
  `import_coverage.py`, `run_attempt.sh`).
- **Not done in M2 (by scope):** `DirectSoundCreate` is not reached before GameMain; Mss32 asks
  for it with GetProcAddress, which returns NULL (explicit failure). The first stop after GameMain
  is `kernel32!GetDiskFreeSpaceA` from Storm: M3.
- **Risks carried to M3** (FEASIBILITY §9): 359 strict stubs, some on the M3 path; accepted
  GetProcAddress NULLs (FLS, Encode/DecodePointer, TryEnterCriticalSection) and their CRT
  fallbacks; no DLL_THREAD_ATTACH/DETACH; indirect targets validated only when taken;
  DirectSoundCreate, CD-key data, DirectShow movies, memory ordering.

## M3 — Runtime initialization
- CRT, threads, registry seed (the installer's values), file I/O and Storm's MPQ access on the
  native install; the CD-key data the game reads at startup (installer encoding, §6); intro
  movies skipped or played (DirectShow / `blizzard.ax` path, §6).
- **Accept:** reaches the main menu loop without a fatal stop, 3 consecutive launches.

## M4 — Menus on screen
- D3D8 or the `-opengl` renderer on x86recomp's `gfx::Device` (Metal), input, the main menu
  and the custom game screen rendered; frame dumps checked.

## M5 — Playable local match (offline)
- Load a DotA map in single player (custom game), select a hero, play a full match to the end
  screen: terrain/models/UI rendered, Miles audio, mouse and keyboard.
- **Accept:** a full local match on the chosen DotA build, 3 runs, no fatal stop; replay saved.

## M6 — AI bots
- A DotA AI map (e.g. an "AI" build, or the map's own computer players) playing a full match
  with computer opponents and allies; frame pacing and long-session stability (60+ minutes).

## M7 — Multiplayer
- LAN (UDP 6112, W3GS) between two reFrozen instances, then against a Windows 1.26a client
  (bit-exact x87/SSE lockstep, no desyncs over a full match); then PvPGN/iCCup-style servers
  (the w3l logon-hash behaviour), only with the user's approval for anything network-facing.

Following `../game-port-knowledge/general/bring-up-checklist.md` throughout.
