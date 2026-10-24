# reFrozen — Roadmap (x86 Win32 → Apple Silicon)

Every milestone is gated, as in ReCarbon. Starting each milestone needs the user's **explicit
approval**, even when the previous one passed. A milestone passes only when its acceptance
criteria are met **and observed**. Each milestone records **Evidence** (what was observed) and
**Verify** (how to reproduce it from a clean checkout plus your own game copy).

States: **Passed**, **Partial** (lists the unmet criteria), **Blocked** (root cause or the
unknown documented). Diagnosing a failure is progress; it does not pass a criterion.

**Order: offline first.** A playable local match comes first, then AI bots, then multiplayer.
Nothing network-facing is needed before M6.

## M0 — Correct input and feasibility *(Passed 2026-10-24, pending the user's sign-off)*
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
- **Carried forward (not M0 blockers):** the CD-key encoding step; DirectShow intro movies (§6);
  which DotA build is the target (decision for the user, §5): a pure-JASS build plays on stock
  1.26a; iCCup plugin builds would add each map's DLL as a further module to recompile.

## M1 — Recompile all modules *(not started; needs approval)*
- Ghidra export + x86recomp lift of `war3.exe`, `game.dll`, `Storm.dll` (and `Mss32.dll` or its
  HLE decided here) in one multi-module run, at their preferred bases.
- **Accept:** 0 unimplemented sites (each new instruction: patch + hand-computed test +
  mutation); structural checks (every Ghidra function and export lifted; jump tables resolved or
  explained); generated code byte-identical across two runs; compiles for arm64.

## M2 — Native link and process start
- A game project (`GameConfig`, `RunProcess`), strict import stubs generated from the imports,
  0 unresolved symbols; the process reaches `GameMain` in `game.dll`.

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
