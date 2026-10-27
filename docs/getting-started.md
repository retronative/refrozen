---
title: Getting started
description: How to install reFrozen 0.1.0 on an Apple silicon Mac and play Warcraft III 1.26a natively, from your own copy of the game.
order: 1
---

# Getting started

> **reFrozen 0.1.0 (alpha)** is available: an offline-only pre-release. Download
> `reFrozen-0.1.0.dmg` from the [release page](https://github.com/retronative/refrozen/releases/tag/v0.1.0), which also has the release notes and
> known limitations.

## What you will need

- **An Apple silicon Mac** (M-series). Intel Macs are not supported.
- **macOS 14 or later.** reFrozen has been tested on macOS 27.0.1.
- **Apple's Command Line Tools.** The setup checks for them and offers Apple's installer if they
  are missing.
- **About 2.5 GB of free disk space** during setup. Once set up, reFrozen uses about 1.2 GB.
- **Your own copy of the game:** the official installers for *Warcraft III: Reign of Chaos* and
  *Warcraft III: The Frozen Throne* 1.21b (English, UK edition), with your own CD keys, plus the
  official 1.26a English patch. See [Compatibility](compatibility.md) for the exact versions.
- **Any maps you want to play**, such as a DotA map, which you supply yourself.

reFrozen never ships any of these. It contains no game code, assets, maps or keys.

## Install

1. **Download** `reFrozen-0.1.0.dmg`. To check it, run `shasum -a 256 reFrozen-0.1.0.dmg` in
   Terminal, in the folder with the download. It must print
   `0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`.
2. **Open the disk image** and drag **reFrozen** to **Applications**. Open it from Applications.
3. **The first open.** reFrozen is ad hoc signed and **not notarized**: Apple has not checked it,
   so macOS blocks it the first time. Opening it anyway is your own decision to make an exception
   for this app; do it only for a download whose checksum matches. On macOS 27:
   - macOS shows **“reFrozen” Not Opened**: "Apple could not verify “reFrozen” is free of malware
     that may harm your Mac or compromise your privacy." Choose **Done**, not Move to Trash.
   - Open **System Settings → Privacy & Security** and scroll to **Security**. It says
     **“reFrozen” was blocked to protect your Mac.** Choose **Open Anyway**.
   - macOS asks **Open “reFrozen”?**: "Apple is not able to verify that it is free from malware
     that could harm your Mac or compromise your privacy. Don’t open this unless you are certain it
     is from a trustworthy source." Choose **Open Anyway** (macOS may ask for your password).
   - After that, reFrozen opens normally.
4. **The first-run setup.** reFrozen checks your Mac, then you choose your installers and the
   patch (each file is checked) and enter your CD keys and name. It installs the game and patches
   it to 1.26a, then builds the game for your Mac from your own copy: about 3 minutes on an M5,
   about 5½ minutes on an M1. Progress is shown, and you can cancel at any time. Your CD keys are
   stored only in the game's own files, as the official installer stores them, and are never sent
   anywhere. See [How it works](how-it-works.md).
5. **Play.** Every later launch opens the Mini Launcher: **Install New Maps** adds your `.w3x` or
   `.w3m` maps (an installed map is never overwritten), and **Start Game** starts the game. Open
   *Single Player → Custom Game* and pick your map.

## Useful controls

- **Ctrl + Cmd + F** switches between borderless fullscreen and a window.
- The game keeps its original 4:3 interface. On wide or Retina screens the picture is scaled
  sharply and framed with bars instead of being stretched.

## Known limitations

v0.1.0 is an alpha. The [release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0) list its known limitations, among them:

- an intermittent crash in long AI matches, whose cause is not known;
- saved games of the DotA v6.83d AI map can't be loaded: the game reports the save as unavailable
  or corrupted, then crashes and closes (saving and loading on standard maps works);
- a short pause before a map starts loading, and a loading bar that freezes for a few seconds on
  large maps.

If the game crashes, a report is written to `~/Library/Application Support/reFrozen/crashes`.

## Uninstall

Quit reFrozen, move it from Applications to the Bin, and delete
`~/Library/Application Support/reFrozen`. That folder holds your installed game, including your
encoded CD keys, so never attach it, or files from it, to a bug report. Your installers and maps
are never changed.

## Before you ask

reFrozen is offline-only for v0.1.0. LAN, private servers, iCCup and Battle.net are not part of
it. Read the [FAQ](faq.md) for more.
