# reFrozen v0.2.1: release notes (draft)

Draft, not published. Scope, requirements and the release decision are in `READINESS_v0.2.1.md`;
the text below is reviewed by the owner before publication.

reFrozen 0.2.1 is a maintenance release of 0.2.0 Beta. It guards against the intermittent crash in
long AI matches, the main known issue of 0.1.0 and 0.2.0. Everything else is as in 0.2.0: Warcraft
III: The Frozen Throne 1.26a recompiled to run natively on Apple silicon Macs with macOS 14 or later,
built on your Mac from your own game files, with LAN games between Macs.

## What's fixed

- **The intermittent crash in long AI matches.** A map's trigger can wait, then ask which unit
  attacked or damaged (`GetAttacker` and the damage-source response). If the game had discarded
  that event's information during the wait, the game stopped. reFrozen now answers "no unit" in
  that case, as the game does for a unit that has left the game, and play continues. In testing,
  the guard took effect on `GetAttacker` during a real DotA AI match and the game continued
  without a crash; the damage-source path is covered by the regression tests.

## Upgrading from 0.2.0

Replace reFrozen in Applications with the new version. On the first launch it builds the game
module again from your installed game files (a few minutes, as on the first install); your
installed game files and maps are kept. For LAN games, every Mac runs reFrozen 0.2.1.

## Requirements

As for 0.2.0: an Apple silicon Mac with macOS 14 or later, Apple's Command Line Tools (the first
run offers to install them), your own Reign of Chaos and The Frozen Throne installers with their CD
keys and the official 1.26a English patch, and maps you supply.

## Known issues

- **A related handle-reference issue is not fixed.** In the same situation (a trigger that waits,
  then asks for its event's unit), the game may have reused the reference the trigger still holds,
  so the answer can in rare cases be a different unit instead of none. It does not stop the game,
  but a map's script may then act on the wrong unit. It is unresolved and under investigation; this
  release does not fix every issue related to the crash.
- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game plays its opening cinematic through DirectShow, which reFrozen does not provide, and
  does not recover when that fails. The Founding of Durotar starts and its opening sequence plays
  (the rest of that campaign is not verified); the other campaigns are not verified yet.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded** (as in 0.1.0).
  Saving works; saves load on Booty Bay and DotA v6.78c AI 1.4e.
- **The game opens on the Mac's main display** and can't be moved to another display. To play
  on an external monitor, make it the main display in System Settings → Displays before you
  start the game.
- As in 0.1.0: a short pause before a map starts loading, and a loading bar that freezes for a
  few seconds on large maps.
- reFrozen is not notarized: macOS blocks the first open until you choose **Open Anyway** (see
  Getting started).

## Cross-platform multiplayer (experimental)

Mac-to-Mac LAN multiplayer is tested and verified, as in 0.2.0.

Compatibility with the original Windows Warcraft III 1.26a client is still experimental: it has
not been officially verified. A preliminary check with the original client running under Wine
joined a reFrozen 0.2.0 game and stayed in sync; that is not a test on Windows. Community reports
are welcome, including successful connections, disconnections and synchronization issues.

Official testing with Windows is planned for v0.2.2.

## Not in this release

- Private servers (M7b), iCCup online (M8, only with iCCup's official cooperation), Battle.net.

## Verification

On release candidate 2 (`23c28ec`; `reFrozen-0.2.1.dmg`, SHA-256
`576a1e5836251c23b9751c7dded8922faf280c81de4f56b0fae820990a47a3cc`), details in `READINESS_v0.2.1.md`:

- The crash guard: a regression test, mutation testing, a test map that forces the condition (the
  game no longer stops), and a real DotA AI match in which the guard took effect and the game
  continued without a crash (a test build with logging; the guard's code is the same).
- Release checks, the dmg read back, signature, a clean install in a fresh data folder (the
  installers, cancel, the first build), an upgrade over a 0.2.0 installation (the game module
  rebuilt, maps kept), suites and ctest, two identical lifts, M4 3/3, M5 3/3, and the full mutation
  gate (362 mutants: 360 killed, 2 equivalent).
- One 30-minute AI match on the release candidate: no crash, stable frame pacing and memory.
- LAN play between Macs: verified for 0.2.0; 0.2.1 changes no network code.
