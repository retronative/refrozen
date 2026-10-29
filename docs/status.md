---
title: Status and releases
description: The single public record of reFrozen's milestones and releases. reFrozen 0.1.0 (alpha, offline) is available.
order: 2
release_headline: reFrozen 0.1.0 (alpha) available
release_planned: Offline-only pre-release, published 27 October 2026
release_url: https://github.com/retronative/refrozen/releases/download/v0.1.0/reFrozen-0.1.0.dmg
release_version: v0.1.0
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
| M6 | AI bots and long sessions | Passed, signed off | Full DotA AI matches with computer players: three 30-minute runs and one 65-minute match won by the Scourge, with stable frame pacing and memory. An intermittent crash seen in earlier long runs is a known alpha limitation (not fixed). |
| M7 | LAN and private multiplayer | Future work | Not part of v0.1.0. |
| M8 | iCCup online | Future work | Only with iCCup's official cooperation. Not part of v0.1.0. |

## Releases

**reFrozen 0.1.0 (alpha)**, an offline-only pre-release, was published on 27 October 2026:
[download and release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0), including the known limitations. The SHA-256 of
`reFrozen-0.1.0.dmg` is `0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`. To install it, follow [Getting started](getting-started.md).

### In v0.1.0

- Offline custom games from the Custom Game screen, with maps you supply
- DotA AI maps with computer allies and opponents
- Audio, mouse and keyboard
- Borderless fullscreen and Retina / HiDPI, with the 4:3 interface preserved
- Replays written after each match, and played back in the game

### Known limitations in v0.1.0

- **An intermittent crash in long AI matches.** Its cause is not known and it is not fixed. If it
  happens, please report it with the crash report from `~/Library/Application Support/reFrozen/crashes`.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded.** Saving works,
  but loading such a save shows "The save file is unavailable or corrupted", and then the game
  crashes and closes. This is specific to that map version, not to DotA AI maps in general: saving
  and loading work on a standard map (Booty Bay) and on DotA v6.78c AI 1.4e. How the original
  Warcraft III client behaves with this map's saves has not been checked yet.
- **A short pause before loading starts** (about half a second) when you select a map and when you
  press Start Game. This comes from the game itself.
- **The loading bar freezes for a few seconds** while a large map loads, and audio may stutter during
  match loading. Gameplay itself runs smoothly.
- The scoreboard may show expanded during a match.
- reFrozen is not notarized: macOS blocks the first open until you choose **Open Anyway** (see
  [Getting started](getting-started.md)).

### Not part of v0.1.0

- LAN and private multiplayer (M7)
- iCCup online (M8)
- Battle.net

### Known issues in v0.2.0 Beta (in preparation)

- **An intermittent crash in long AI matches** (as in 0.1.0). It happens occasionally in long
  matches with many computer players, and has also occurred on the dedicated test Mac. Its
  mechanism has been identified: a unit that a map's script still refers to across a wait can
  be removed during that wait, and the script's next lookup of it then fails. A fix is not
  verified yet; it is planned for 0.2.1. If it happens to you, please report it with the crash
  report from `~/Library/Application Support/reFrozen/crashes`.
- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game plays its opening cinematic through DirectShow, which reFrozen does not provide, and
  does not recover when that fails. A known compatibility limitation, not blocking v0.2.0; planned for after
  it. The Founding of Durotar starts and its opening sequence plays (the rest of that campaign is
  not verified); the other campaigns are not verified yet.
- **The game opens on the Mac's main display** and can't be moved to another display. To play
  on an external monitor, make it the main display in System Settings → Displays before you
  start the game.

A release contains only reFrozen itself: the recompiler, the runtime and the native installer.
The game modules are built on your Mac from your own copy; see [Getting started](getting-started.md).
