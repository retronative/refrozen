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
| M4 | Interactive menus and rendering | Passed, sign-off pending | Passed under delegation; final sign-off pending. |
| M5 | Playable local match (offline) | Passed, sign-off pending | Passed under delegation; final sign-off pending. A full local DotA match plays to the score screen. |
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

### Not part of v0.1.0

- LAN and private multiplayer (M7)
- iCCup online (M8)
- Battle.net

A release contains only reFrozen itself: the recompiler, the runtime and the native installer.
The game modules are built on your Mac from your own copy; see [Getting started](getting-started.md).
