# reFrozen — Roadmap (x86 Win32 → Apple Silicon)

Every milestone is gated, as in ReCarbon. Starting each milestone needs the user's **explicit
approval**, even when the previous one passed. A milestone passes only when its acceptance
criteria are met **and observed**. Each milestone records **Evidence** (what was observed) and
**Verify** (how to reproduce it from a clean checkout plus your own game copy).

States: **Passed**, **Partial** (lists the unmet criteria), **Blocked** (root cause or the
unknown documented). Diagnosing a failure is progress; it does not pass a criterion.

**Mutation gate (from M3, every milestone):** a milestone is not signed off until every behaviour
it adds or changes has focused tests with independently derived expected values, its mutants in
`tests/mutants.py` are all KILLED or documented EQUIVALENT by `tests/mutate.py` (survivors fixed
by better tests), earlier milestones' mutants still pass, and `reference/TEST_COVERAGE.md` records
each mutant, its expected failure and the observed result (AGENTS.md, "Mutation gate").

**Order: offline first.** A playable local match comes first, then AI bots, then LAN and private
multiplayer (M7), and only then the iCCup online community (M8), which also depends on iCCup's
official cooperation. Nothing network-facing is needed before M7.

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

## M2 — Native link and process start *(Passed 2026-10-24, signed off by the user)*
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

## M3 — Runtime initialization *(Passed 2026-10-24, signed off by the user 2026-10-25)*
- **Scope:** CRT, threads, registry seed, file I/O and Storm's MPQ access on the native install;
  the CD-key data the game reads at startup; intro movies skipped (`seenintromovie`).
- **Accept → Evidence** (FEASIBILITY §10):
  - Main menu loop, 3 consecutive launches, no fatal stop → `scripts/m3_accept.sh 3 60`: 3/3 PASS
    (no FATAL, no watchdog report, alive at 60 s, frames saved); the frames show the TFT main menu
    with the game's "sound is disabled" dialog. A foreground launch (no test hook) likewise.
  - CD keys per the installer → the cipher of `font\font.*` recovered from game.dll; the native
    installer's files are byte-identical to the official installer's for the same keys and name;
    `--verify` PASS except `font.ccd` (not reproduced; the game rejects both versions). The game's
    own key check runs unchanged.
  - Win32 implemented from observed stops, strict elsewhere → 9 stops fixed to documented
    behaviour; unneeded forms stop explicitly; 327 strict stubs remain. ijl15.dll lifted
    (11 modules) with ~40 new MMX/SSE2 forms. Loader fix: static DllMains get a non-NULL
    `lpReserved` (Storm's MPQ access depended on it). Windows' `WM_SIZE`/`WM_MOVE` sequences
    (the last blocker: the GL device never learnt its size).
  - Renderer → the game's own OpenGL setting on x86recomp's GL HLE (Direct3D 8 is M4). Sound →
    no wave device (Windows' error codes); audio output is M5.
  - CRT fallbacks and thread synchronization → investigated where reached (FEASIBILITY §10);
    named-object type checks, I/O completion ports, TryEnterCriticalSection implemented and tested.
  - Mutation gate → 87 mutants (M2 + M3): 86 KILLED, 1 documented EQUIVALENT, 0 survivors;
    249 checks; ctest 16/16; lift byte-identical twice (`e9333df8…95b7e7`), validator HARD PASS.
- **Verify:** FEASIBILITY §10.
- **Risks carried to M4:** rendering correctness unverified (texgen enabling unsupported in the GL
  HLE; Direct3D 8 absent); input untested; upstream fake-success no-ops (`InvalidateRect`,
  `UpdateWindow`, `FillRect`, `DrawTextA`); `font.ccd`; game.dll's threads' memory ordering.

## M4 — Interactive menus and rendering correctness *(Passed 2026-10-25; progression to M5 approved under the user's overnight delegation, final sign-off with the user)*
- **Scope (the user's 2026-10-25 request):** main menu and Custom Game interface fully interactive
  and visually correct: mouse, keyboard, focus, resize, minimize/restore, menu navigation;
  rendering compared with the official 1.26a Wine oracle; observed GL defects fixed;
  `InvalidateRect`/`UpdateWindow`/`FillRect`/`DrawTextA` audited, no fake successes; the existing
  OpenGL path preferred, Direct3D 8 deferred unless required. Audio stays M5.
- **Accept → Evidence** (FEASIBILITY §11):
  - Interactive menus → `scripts/m4_accept.sh 3 110`: 3/3 PASS. Each launch (fresh profile)
    walks main menu → new profile → Single Player → Custom Game → next map → Download folder
    (mouse) → DotA 6.85oz LoD selected → Cancel → Options → Video → Cancel → focus out/in →
    minimize/restore → Quit: all 14 shots saved, no FATAL, no watchdog report, Quit exits 0.
  - Rendering against the oracle → both oracle renderers (Direct3D 8/wined3d and `-opengl`)
    walk the same path by keys; UI, text, layout and previews match. Fixed: GL fog (absent), the
    lifter's PUSH/POP slot size (a crash at Quit; ~1,900 sites), 16-bit texel precision. The
    oracle's longer thin chains come from macOS GL's default anisotropic filtering, which the
    game does not request: documented, not copied.
  - Win32 audit → real painting (update regions, WM_PAINT order and validation, UpdateWindow,
    BeginPaint/EndPaint, WM_ERASEBKGND); GDI drawing a strict stop (only movie/dialog paths
    use it); minimize/restore/resize/focus per Wine's message sequences; DllMain exceptions
    caught as Wine's loader does; execute faults through the guest SEH chain.
  - Tests and mutation gate → 361 checks (lifter 122, loader 23, Win32 151, GL 37, key files 23,
    jump-table corrections 5); mutation gate 120 mutants (M2–M4): 119 KILLED, 1 documented EQUIVALENT, 0 survivors; lift byte-identical twice (`416c0514…7688d`),
    validator HARD PASS; ctest 18/18 (`pacing` passes on a quiet host, 3/3; it fails under heavy load).
- **Verify:** FEASIBILITY §11.
- **Risks carried to M5:** a menu-scene object lit pale natively vs dark in both oracles
  (unexplained, lighting-related); isotropic vs macOS's anisotropic filtering; Start Game
  initialises winsock (first stop `wsock32!htons`); Direct3D 8 absent; 315 strict stubs.

## M5 — Playable local match (offline)
- Load a DotA map in single player (custom game), select a hero, play a full match to the end
  screen: terrain/models/UI rendered, Miles audio, mouse and keyboard.
- **Accept:** a full local match on the chosen DotA build, 3 runs, no fatal stop; replay saved.
- **Work item (the user's request, 2026-10-25): native macOS fullscreen and Retina/HiDPI**, verified
  separately, not a change to M5's gate:
  - fullscreen ↔ windowed switching, borderless fullscreen first (macOS's native Spaces fullscreen
    later if needed);
  - logical (points) versus physical (pixels) sizing on Retina and scaled displays; the game keeps
    its own resolution and the frame is scaled to the window;
  - mouse coordinates mapped through the same scaled, letterboxed rectangle;
  - the original 4:3 UI never stretched: aspect preserved with letter/pillarboxing; gameplay
    correctness unaffected (the game sees only its own resolution);
  - the existing 800×600 test mode unchanged;
  - regression and mutation tests for fullscreen transitions, resizing and input mapping.
  - **Status (2026-10-25): implemented and verified, in patch 0013.** Fullscreen is borderless
    on the current Space (`SDL_HINT_VIDEO_MAC_FULLSCREEN_SPACES=0`; `GameConfig::fullscreen`
    defaults to desktop); Ctrl+Cmd+F, or the window's own control, switches to windowed and back
    (the player's choice overrides the policy); windows are one point per game pixel, scaled down
    to fit the screen; the frame is fitted with bars (`gfx::FitRect`) and pointer positions map
    back through the same rectangle (`gfx::FramePoint`, clamped over the bars; the game's
    clipped virtual cursor is unchanged); background runs simulate a screen
    (`REFROZEN_TEST_SCREEN`) instead of taking over the display. Evidence:
    `scripts/m5_display_check.sh` all checks pass (fullscreen 1512×982 with 101-point bars,
    two toggles, `-window` scaled onto a 640×400 screen, clicks landing on the reference screen);
    `test_win32.py` mode F and `fit_map_test` pass; mutants M5-F1–F10 10/10 KILLED; M4 3/3 and
    M5 3/3 acceptance re-run on the same build, pass; 800×600 test mode unchanged.

## M6 — AI bots
- A DotA AI map (e.g. an "AI" build, or the map's own computer players) playing a full match
  with computer opponents and allies; frame pacing and long-session stability (60+ minutes).

## M7 — LAN and private multiplayer
- LAN (UDP 6112, W3GS) between two reFrozen instances, then against a Windows 1.26a client
  (bit-exact x87/SSE lockstep, no desyncs over a full match); then private servers the players
  run themselves (PvPGN-style, the w3l logon-hash behaviour), only with the user's approval for
  anything network-facing. Public online services, iCCup included, are M8.

## M8 — iCCup online compatibility
- **Goal:** native macOS players can join the existing iCCup DotA community, within iCCup's
  anti-cheat and client-integrity requirements.
- **Depends on:** M7 passed and signed off, and official cooperation from iCCup. Without iCCup's
  agreement this milestone does not start. Anti-cheat is never bypassed, disabled or emulated
  around; integration happens only in the form iCCup approves.
- **Scope:**
  - Research the iCCup launcher, its authentication, network protocols and native plugin
    dependencies, including the `dota.dll` embedded in its maps (statically, as for M0; FEASIBILITY
    §5). Network-facing research only with the user's approval and within iCCup's terms.
  - iCCup-compatible map loading and gameplay (the native-plugin builds deferred in M0: 6.83se,
    6.83s, 6.85.308).
  - Compatibility with existing Windows iCCup players (lockstep, as M7 for LAN).
  - A modular iCCup integration layer, separate from the game port, that LAN, private and offline
    play neither load nor depend on.
  - Signed builds, reproducible build evidence and client-integrity verification, in the form
    iCCup's anti-cheat needs.
  - Seek iCCup's official approval of a native macOS client and of its anti-cheat compatibility.
- **Accept:**
  - The client and protocol compatibility iCCup requires, demonstrated.
  - A full online match with Windows iCCup players, no desync.
  - iCCup's official anti-cheat approval, and its integration requirements met.
  - No regression in offline or LAN play (their acceptance tests re-run).

## Release packaging *(future work item; not a milestone gate, not started)*
- **Goal (the user's request, 2026-10-25):** a native macOS application players install and launch
  like any other game, compatible with macOS Game Mode. It doesn't interrupt the milestones or
  change their gates.
- **Constraint that shapes it:** a distribution never includes a CD key, game code (original or
  recompiled), assets or maps (AGENTS.md). The lifted C++ and its compiled form derive from the
  player's own Warcraft III binaries, so the release ships the recompiler, the runtime and the
  native installer only, and produces the game modules on the player's machine from their own
  install (lift + compile there, or an equivalent the user approves). How that works without a
  developer toolchain on the player's Mac is the first open question.
- **Scope:**
  - A native `.app` bundle: `Info.plist` with `LSApplicationCategoryType`
    `public.app-category-games` (or a game subcategory) and `LSSupportsGameMode`; bundle id,
    version, icon; minimum macOS version; arm64.
  - Proper fullscreen (M5's fullscreen/HiDPI work item) and Retina/HiDPI handling.
  - macOS Game Mode: verify that it activates on supported systems (macOS 14+ on Apple silicon)
    when the game is frontmost and fullscreen (the menu-bar Game Mode indicator, and the system
    log), and that the game runs correctly with it on and off.
  - Code signing with a Developer ID Application certificate and the hardened runtime, every
    nested dylib signed, minimal entitlements (no JIT is needed: the code is recompiled ahead of
    time); notarization (`notarytool`) and stapling; Gatekeeper check on a clean machine.
  - Distribution packaging: a signed, notarized DMG (or installer package) containing only
    reFrozen; first-run flow that points at the player's own installers or install, runs the
    native installer (CD keys as the official installer stores them, never transmitted), and
    builds the game modules locally; uninstall and update paths; checksums and reproducible-build
    evidence for what is shipped.
- **Accept (when scheduled):** the bundle passes `codesign --verify --deep --strict` and
  `spctl --assess`, is notarized and stapled; installs and launches on a clean supported Mac from
  the player's own files; Game Mode activates in fullscreen; the shipped artifact contains no game
  code, data, keys or maps (an automated content check); the offline and LAN acceptance tests pass
  on the packaged build.

Following `../game-port-knowledge/general/bring-up-checklist.md` throughout.
