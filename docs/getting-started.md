---
title: Getting started
description: What you will need to play Warcraft III 1.26a natively on an Apple Silicon Mac with reFrozen, and what the first run will look like once v0.1.0 is released.
order: 1
---

# Getting started

> **There is no release yet** (see [Status and releases](status.md)). There is nothing to download
> today. This page describes what installing will
> look like so you can prepare; it will be replaced with step-by-step instructions when the
> release ships.

## What you will need

- **An Apple Silicon Mac** (M-series). Intel Macs are not targeted.
- **A supported macOS version.** The minimum version is *to be announced*.
- **Your own copy of the game:** the official installers for *Warcraft III: Reign of Chaos* and
  *Warcraft III: The Frozen Throne*, with your own CD keys, plus the official 1.26a patch. See
  [Compatibility](compatibility.md) for the exact versions.
- **Any maps you want to play**, such as a DotA map, which you supply yourself.

reFrozen will never ship any of these. It contains no game code, assets, maps or keys.

## What the first run will look like

1. **Install reFrozen** like any other Mac application.
2. **Point it at your own installers.** reFrozen's native installer unpacks the official
   installers directly on macOS, without Wine. Your CD keys are entered by you and stored the
   way the official installer stores them. They are never sent anywhere.
3. **Build the game modules locally.** reFrozen translates the game code from *your* copy into
   native arm64 code on your Mac. Nothing recompiled is downloaded or shared. See
   [How it works](how-it-works.md).
4. **Play.** Launch to the main menu, open *Single Player → Custom Game*, and pick your map.

The exact steps, disk space and build time will be documented with the release.

## Useful controls

- **Ctrl + Cmd + F** switches between borderless fullscreen and a window.
- The game keeps its original 4:3 interface. On wide or Retina screens the picture is scaled
  sharply and framed with bars instead of being stretched.

## Before you ask

reFrozen is offline-only for v0.1.0. LAN, private servers, iCCup and Battle.net are not part of
it. Read the [FAQ](faq.md) for more.
