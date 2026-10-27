---
title: Status and releases
description: The single public record of reFrozen's milestones and release plans. No releases yet; v0.1.0 (offline) is planned.
order: 2
release_headline: No releases yet
release_planned: v0.1.0 (offline) planned
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
| M4 | Interactive menus and rendering | Passed, sign-off pending | Passed under delegation; final sign-off pending. |
| M5 | Playable local match (offline) | Passed, sign-off pending | Passed under delegation; final sign-off pending. A full local DotA match plays to the score screen. |
| M6 | AI bots and long sessions | Passed, signed off | Full DotA AI matches with computer players: three 30-minute runs and one 65-minute match won by the Scourge, with stable frame pacing and memory. An intermittent crash seen in earlier long runs is a known alpha limitation (not fixed). |
| M7 | LAN and private multiplayer | Future work | Not part of v0.1.0. |
| M8 | iCCup online | Future work | Only with iCCup's official cooperation. Not part of v0.1.0. |

## Releases

**No releases yet.** There is nothing to download. The first release, **v0.1.0**, is planned as
an offline-only release once M6 has passed and been signed off and human playtesting is complete.
No date has been announced.

### Planned for v0.1.0

- Offline custom games from the Custom Game screen, with maps you supply
- DotA AI maps with computer allies and opponents
- Audio, mouse and keyboard
- Borderless fullscreen and Retina / HiDPI, with the 4:3 interface preserved
- Replays written after each match (in-game playback is not yet verified)

### Not part of v0.1.0

- LAN and private multiplayer (M7)
- iCCup online (M8)
- Battle.net

A release will contain only reFrozen itself: the recompiler, the runtime and the native installer.
The game modules are built on your Mac from your own copy; see [Getting started](getting-started.md).
