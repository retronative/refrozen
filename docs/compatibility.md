---
title: Compatibility
description: Which Warcraft III version, which DotA maps, which Macs and which game modes reFrozen supports, and which it does not.
order: 3
---

# Compatibility

## Game version

| Item | Status |
|---|---|
| Warcraft III: The Frozen Throne **1.26a** | Supported, the only target |
| Installed from the 1.21b retail installers + the official 1.26a patch | Supported |
| Other patch versions (older or newer) | Not supported |
| *Reforged* | Not supported |

reFrozen is built for one exact version of the game. Other versions are different programs and
will not work.

## DotA maps

| Map family | Status |
|---|---|
| Pure-JASS DotA maps, e.g. the 6.85-series LoD builds | Works: a full local match has been played to the score screen |
| DotA AI builds, e.g. the 6.83d AI maps | Works: full matches with computer players, tested with the 6.83d AI map up to 65 minutes. Saved games: see below |
| iCCup native-plugin builds (6.83s, 6.83se, 6.85.308) | Not supported |

The iCCup builds load a native plugin through iCCup's own Windows loader. They are not supported.
Support could only come with the iCCup milestone (M8), and only with iCCup's official
cooperation.

You supply the maps yourself; reFrozen does not include or distribute any.

## Macs

| Mac | Status |
|---|---|
| Apple Silicon (M-series) | Target platform |
| Intel Macs | Not targeted |
| Minimum macOS version | macOS 14 (tested on macOS 27.0.1) |

Retina and scaled displays are supported: the game renders at its own resolution and the frame is
scaled to the window with its 4:3 shape preserved. Borderless fullscreen toggles with
**Ctrl + Cmd + F**.

## Game modes

| Mode | Status |
|---|---|
| Single player, Custom Game | Supported (verified) |
| AI opponents and allies on DotA AI maps | Supported (verified: full matches up to 65 minutes) |
| Replays | Written after each match and played back in the game (verified) |
| Saved games | Saving and loading verified on Booty Bay (melee) and DotA v6.78c AI 1.4e. One map version, DotA v6.83d AI (PMV 1.42 EN), saves but its saves can't be loaded: the game reports an error, then crashes (a known limitation, specific to that version; not yet compared with the original client) |
| LAN and private servers | Not supported yet (M7); not in v0.1.0 |
| iCCup online | Not supported (M8), only ever with iCCup's official cooperation |
| Battle.net | Not supported |
