# reFrozen v0.2.0 Beta: release notes (draft)

Draft, not published. Scope, requirements and the release decision are in `M7_READINESS.md`;
the text below is reviewed by the owner before publication.

---

reFrozen 0.2.0 Beta adds LAN multiplayer between Macs to the offline game of 0.1.0: Warcraft III:
The Frozen Throne 1.26a recompiled to run natively on Apple silicon Macs with macOS 14 or later,
built on your Mac from your own game files.

## What's new

- **LAN games between Macs:** host a game, find games on your local network, join, the lobby and
  chat (in the lobby and in game). Both host directions are tested between two Macs, and the two
  Macs' games stay in sync turn for turn.
- **Custom map download:** joining a game whose map you don't have downloads it from the host.
- **Hosting with a VPN on:** the game's LAN announcements go to each local network, so a Mac with
  a VPN as its main connection can host.
- **Local network permission:** macOS asks once whether reFrozen may find devices on your local
  network. Allow it; until you do, joining a game fails.
- **Original timing:** the game's clock follows Windows' standard 64 Hz system timer, as the
  original client does (up to 64 frames a second, timers at the original cadence).
- **Installer:** a refined progress bar (still when Reduce Motion is on).

## Requirements

As for 0.1.0: an Apple silicon Mac with macOS 14 or later, Apple's Command Line Tools (the first
run offers to install them), your own Reign of Chaos and The Frozen Throne installers with their CD
keys and the official 1.26a English patch, and maps you supply. For LAN games, every Mac runs
reFrozen 0.2.0 on the same local network.

## Known issues

- **An intermittent crash in long AI matches** (as in 0.1.0). It happens occasionally in long
  matches with many computer players, and has also occurred on the dedicated test Mac. Its
  mechanism has been identified: a unit that a map's script still refers to across a wait can
  be removed during that wait, and the script's next lookup of it then fails. A fix is not
  verified yet; it is planned for 0.2.1. If it happens to you, please report it with the crash
  report from `~/Library/Application Support/reFrozen/crashes`.
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

Mac-to-Mac LAN multiplayer has been tested and verified.

Compatibility with the original Windows Warcraft III 1.26a client has not yet been officially
verified. Community testing is welcome, and we encourage players to share their results,
including successful connections, disconnections, and synchronization issues.

Official cross-platform LAN compatibility testing is planned for v0.2.1.

## Not in this release

- Private servers (M7b), iCCup online (M8, only with iCCup's official cooperation), Battle.net.

## Verification

To be completed from `M7_READINESS.md` before publication: the two-Mac sessions, the regression
runs on the release candidate, the clean install and the owner's playtest.
