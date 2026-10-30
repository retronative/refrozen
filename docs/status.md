---
title: Status and releases
description: The single public record of reFrozen's milestones and releases. reFrozen 0.2.1, a maintenance release of the 0.2.0 Beta with LAN multiplayer between Macs, is available.
order: 2
release_headline: reFrozen 0.2.1 available
release_planned: A maintenance release of the 0.2.0 Beta, published 30 October 2026
release_url: https://github.com/retronative/refrozen/releases/download/v0.2.1/reFrozen-0.2.1.dmg
release_version: v0.2.1
---

# Status and releases

This page is the one public source for where reFrozen stands. The website's status displays,
release page and documentation all read it. Development is organised in gated milestones: a
milestone passes only when its acceptance criteria have been met and observed.

## Milestones

| ID | Milestone | State | Notes |
|---|---|---|---|
| M0 | Correct input and feasibility | Passed, signed off | |
| M1 | Recompile all modules | Passed, signed off | |
| M2 | Native link and process start | Passed, signed off | |
| M3 | Runtime initialisation | Passed, signed off | |
| M4 | Interactive menus and rendering | Passed, signed off | |
| M5 | Playable local match (offline) | Passed, signed off | A full local DotA match plays to the score screen. |
| M6 | AI bots and long sessions | Passed, signed off | Full DotA AI matches with computer players: three 30-minute runs and one 65-minute match won by the Scourge, with stable frame pacing and memory. The intermittent crash in long AI matches is guarded in 0.2.1 (verified on its release candidate with three 30-minute runs and one 65-minute match); a related handle-reference issue is not fixed yet. |
| M7 | LAN and private multiplayer | Passed, signed off | LAN games between Macs are delivered in v0.2.0: hosting, finding and joining games, lobby and chat, custom map download. Private servers (M7b) are future work. |
| M8 | iCCup online | Future work | Only with iCCup's official cooperation. Not part of v0.2.1. |

## Releases

**reFrozen 0.2.1** is a maintenance release of the 0.2.0 Beta. It guards against the intermittent
crash in long AI matches; everything else is as in 0.2.0. It was published on 30 October 2026:
[download and release notes](https://github.com/retronative/refrozen/releases/tag/v0.2.1), including the known issues. The SHA-256 of
`reFrozen-0.2.1.dmg` is `576a1e5836251c23b9751c7dded8922faf280c81de4f56b0fae820990a47a3cc`. To install it, follow [Getting started](getting-started.md). To
upgrade from 0.2.0, replace reFrozen in Applications; on the first launch it builds the game again
from your installed game files (a few minutes), and your installed game files and maps are kept.

### In v0.2.1

- The intermittent crash in long AI matches: a map's trigger that waited, then asked which unit
  attacked, could find that the game had discarded the event's information during the wait, and
  the game stopped. reFrozen now answers "no unit" in that case, as the game does for a unit that
  has left the game, and play continues
- Everything in 0.2.0: LAN games between Macs (hosting, finding and joining games, lobby and chat,
  custom map download), the original 64 Hz timing, and the offline game of 0.1.0. For LAN games,
  every Mac runs reFrozen 0.2.1
- Experimental: LAN games with the original Windows 1.26a client are not yet officially verified;
  official testing is planned for v0.2.2

### Known issues in v0.2.1

- **A related handle-reference issue is not fixed.** In the same situation (a trigger that waits,
  then asks for its event's unit), the game may have reused the reference the trigger still holds,
  so the answer can in rare cases be a different unit instead of none. It does not stop the game,
  but a map's script may then act on the wrong unit. It is unresolved and under investigation; this
  release does not fix every issue related to the crash. If the game crashes, please report it
  with the crash report from `~/Library/Application Support/reFrozen/crashes`.
- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game plays its opening cinematic through DirectShow, which reFrozen does not provide, and
  does not recover when that fails. The Founding of Durotar starts and its opening sequence plays
  (the rest of that campaign is not verified); the other campaigns are not verified yet.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded** (as in 0.1.0).
  Saving works; saves load on Booty Bay and DotA v6.78c AI 1.4e.
- **The game opens on the Mac's main display** and can't be moved to another display. To play
  on an external monitor, make it the main display in System Settings → Displays before you
  start the game.
- Short pauses while the game loads: before a map loads, a loading bar that freezes for a few
  seconds on large maps, a pause of a few seconds when the match first appears, and on the way
  back to the menu. During a match the game can occasionally freeze for about a second. These
  pauses are the same as in earlier versions.
- reFrozen is not notarized: macOS blocks the first open until you choose **Open Anyway** (see
  [Getting started](getting-started.md)).

### Not part of v0.2.1

- Private servers (M7b)
- iCCup online (M8), only with iCCup's official cooperation
- Battle.net

A release contains only reFrozen itself: the recompiler, the runtime and the native installer.
The game modules are built on your Mac from your own copy; see [Getting started](getting-started.md).

**Earlier releases.** reFrozen 0.2.0 Beta, which added LAN multiplayer between Macs, was published
on 30 October 2026 ([release notes](https://github.com/retronative/refrozen/releases/tag/v0.2.0)). The SHA-256 of
`reFrozen-0.2.0.dmg` is `db1ff96c3e839bb7c2450db525f37ceca8ff08ba367fe200cb0a7af550685643`. reFrozen 0.1.0 (alpha), the offline-only first pre-release, was published on
27 October 2026 ([release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0)). The
SHA-256 of `reFrozen-0.1.0.dmg` is `0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`.
