# reFrozen v0.1.0 — release plan (first public, offline-only release)

**Status: PLANNED, not started** (the user's request, 2026-10-25). Nothing here is implemented,
tagged, published or pushed until the user explicitly approves each step. This plan does not change
any milestone gate; M6's acceptance criteria stay as written in ROADMAP.

## What v0.1.0 is
A native Apple silicon build of Warcraft III: The Frozen Throne 1.26a for offline play, produced on
the player's Mac from the player's own game files:
- offline custom games (single player, the Custom Game screen), including DotA maps the player
  supplies and DotA AI maps with computer players (M5, M6);
- audio (Miles on SDL), mouse and keyboard, native fullscreen and Retina/HiDPI (M5 work item);
- replays (`Replay\LastReplay.w3g` written; playback of the player's own replays in-game).

**Not in v0.1.0, and not prerequisites:** LAN and private multiplayer (M7), iCCup (M8), Battle.net.
Network-facing menus stay as the game has them but are not supported or tested for this release.

## Prerequisites (both required before release work starts)
1. **M6 passed and signed off by the user** (three 65-minute AI matches under the unchanged criteria,
   ROADMAP M6), with M0–M5 signed off.
2. **Human playtesting completed** (gate G1 below), by the user or testers the user names.

## What is distributed, and what never is
- **Shipped:** the reFrozen application (launcher, runtime libraries, the recompiler and the native
  installer), its licences and notices, documentation.
- **Never shipped** (AGENTS.md, "CD keys and distribution"): Blizzard binaries or installers, lifted
  or recompiled game code, game assets or MPQs, maps (DotA or any other), CD keys, iCCup components
  (launcher, `dota.dll`, anti-hack), Wine.
- **Consequence:** the game modules are produced on the player's machine, from the player's own
  installers or install, by the shipped recompiler (lift + compile there, or an equivalent the user
  approves). The player never needs Wine; the native installer already extracts the official
  installers without it (M2).

## Release gates
Each gate records Evidence and Verify like a milestone. All must pass for v0.1.0.

| Gate | What must be shown |
|---|---|
| **G1 Manual gameplay QA** | A written test plan executed by a human on the packaged build: install, menus, custom game with a player-supplied DotA map, a full AI match (DotA AI map), hero selection by mouse in a tavern (unexercised so far), audio heard, keyboard/mouse incl. hotkeys and chat, fullscreen ↔ windowed (Ctrl+Cmd+F) on a Retina and an external display, minimise/restore, save/load of replays and playback, quit/relaunch. Every defect triaged; none open at severity "blocks play". |
| **G2 Clean installation from player-owned files** | On a clean supported Mac (no developer tools, no Wine, no prior reFrozen data): first run asks for the player's own installers or install, runs the native installer (CD keys entered by the player and stored only as the official installer stores them, never transmitted), builds the game modules locally, and launches to the main menu. Install, update and uninstall paths documented and tried; disk use and build time measured. |
| **G3 macOS `.app` packaging** | An arm64 `.app` with `Info.plist` (bundle id, version 0.1.0, icon, minimum macOS, `LSApplicationCategoryType` games, `LSSupportsGameMode`); every nested dylib inside the bundle; an automated content check proving the artifact holds none of the never-shipped items (no PE files, MPQs, maps, key-like strings, generated code). |
| **G4 Game Mode verification** | On macOS 14+ Apple silicon: Game Mode activates when the game is frontmost and fullscreen (menu-bar indicator and system log), deactivates when windowed or in the background; the game runs correctly with it on and off. |
| **G5 Signing and notarization** | Developer ID Application signature with the hardened runtime, minimal entitlements (no JIT entitlement; ahead-of-time code), every nested binary signed; `codesign --verify --deep --strict`, notarized (`notarytool`) and stapled, `spctl --assess` passes on a clean machine; the locally built game modules load under the hardened runtime (how they are signed on the player's machine is an open question, below). |
| **G6 Regression and mutation tests** | On the release commit: all suites and ctest pass; the mutation gate has every mutant KILLED or documented EQUIVALENT; two lifts byte-identical and `validate_lift.py` HARD PASS; patches reapply; M4, M5 and M6 acceptance re-run on the packaged build and pass. |
| **G7 Distribution and licensing review** | A written review, done by the user (and counsel if the user chooses; this plan is not legal advice): Blizzard's EULA/Terms for the player's use of their own copy and for distributing a recompiler that operates on it; third-party licences and notices for everything shipped (SDL3 zlib, FFmpeg LGPL and its dynamic-linking terms, SoftFloat BSD, x86recomp and its patches, LLVM if a toolchain is bundled, any others found by an inventory); trademarks (no Blizzard or iCCup marks or logos used as branding); the README's statement of what players must own. |
| **G8 Release artifacts** | A signed, notarized DMG (or installer package) of the `.app`, its SHA-256, release notes listing scope, known issues and non-goals (no M7/M8), reproducible-build evidence for what is shipped. Tagging and publishing only on the user's explicit approval. |

## Open questions (to resolve before G2/G5)
1. **Building the game modules without a developer toolchain on the player's Mac.** Options:
   bundle a minimal LLVM/clang (licence review, size, notarization of the toolchain); a different
   ahead-of-time path the user approves. Build time (242 generated files today) and disk use must be
   measured on the slowest supported Mac.
2. **Signing code built on the player's machine** (ad-hoc signing of the locally compiled game
   modules and library validation under the hardened runtime).
3. **Which installers are accepted** (1.21b + 1.26a patch as today; other retail releases) and what
   the first-run flow says when an unsupported version is given.
4. **Minimum macOS version** and supported hardware (Apple silicon only; macOS 14+ for Game Mode).
5. **Update path** when reFrozen's recompiler or runtime changes (rebuild the game modules locally).

## Known items carried into QA (from milestone records)
- Hero selection by mouse in a tavern is unexercised (M5 used `-ar`).
- Replay determinism against the original client is unchecked (headers and sizes only).
- M4's open rendering items (the pale-lit ice spike, isotropic filtering, no Direct3D 8 renderer).
- 300 strict stubs in the import layer.
- Why DotA's scoreboard was shown expanded mid-match in M6 run 1 is unresolved (FEASIBILITY §13).
