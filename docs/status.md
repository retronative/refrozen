---
title: Status and releases
description: The single public record of reFrozen's milestones and releases. reFrozen 0.2.0 Beta, with LAN multiplayer between Macs, is available.
order: 2
release_headline: reFrozen 0.2.0 Beta available
release_planned: LAN multiplayer between Macs, published 30 October 2026
release_url: https://github.com/retronative/refrozen/releases/download/v0.2.0/reFrozen-0.2.0.dmg
release_version: v0.2.0
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
| M6 | AI bots and long sessions | Passed, signed off | Full DotA AI matches with computer players: three 30-minute runs and one 65-minute match won by the Scourge, with stable frame pacing and memory. An intermittent crash in long AI matches remains a known issue: its mechanism has been identified; a fix is not verified yet and is planned for 0.2.1. |
| M7 | LAN and private multiplayer | Passed, signed off | LAN games between Macs are delivered in v0.2.0: hosting, finding and joining games, lobby and chat, custom map download. Private servers (M7b) are future work. |
| M8 | iCCup online | Future work | Only with iCCup's official cooperation. Not part of v0.2.0. |

## Releases

**reFrozen 0.2.0 Beta** adds LAN multiplayer between Macs to the offline game of 0.1.0. It was
published on 30 October 2026:
[download and release notes](https://github.com/retronative/refrozen/releases/tag/v0.2.0), including the known issues. The SHA-256 of
`reFrozen-0.2.0.dmg` is `db1ff96c3e839bb7c2450db525f37ceca8ff08ba367fe200cb0a7af550685643`. To install it, follow [Getting started](getting-started.md).

### In v0.2.0

- LAN games between Macs: host a game, find games on your local network, join, the lobby and chat
  (in the lobby and in game). Every Mac runs reFrozen 0.2.0 on the same local network
- Custom map download: joining a game whose map you don't have downloads it from the host
- Hosting with a VPN on: the game's LAN announcements go to each local network
- Original timing: the game's clock follows Windows' standard 64 Hz system timer, as the original
  client does
- Everything in 0.1.0: offline custom games and DotA AI maps with computer players, audio, mouse
  and keyboard, borderless fullscreen and Retina / HiDPI, and replays
- Experimental: LAN games with the original Windows 1.26a client are not yet officially verified;
  official testing is planned for v0.2.1

### Known issues in v0.2.0

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
  [Getting started](getting-started.md)).

### Not part of v0.2.0

- Private servers (M7b)
- iCCup online (M8), only with iCCup's official cooperation
- Battle.net

A release contains only reFrozen itself: the recompiler, the runtime and the native installer.
The game modules are built on your Mac from your own copy; see [Getting started](getting-started.md).

**Earlier release.** reFrozen 0.1.0 (alpha), the offline-only first pre-release, was published on
27 October 2026 ([release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0)). The
SHA-256 of `reFrozen-0.1.0.dmg` is `0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`.
