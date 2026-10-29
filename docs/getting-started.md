---
title: Getting started
description: How to install reFrozen 0.2.0 Beta on an Apple silicon Mac and play Warcraft III 1.26a natively, offline and over LAN between Macs, from your own copy of the game.
order: 1
---

# Getting started

> **reFrozen 0.2.0 Beta** is available: the offline game of 0.1.0, plus LAN multiplayer between
> Macs. Download `reFrozen-0.2.0.dmg` from the [release page](https://github.com/retronative/refrozen/releases/tag/v0.2.0), which
> also has the release notes and known issues.

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

1. **Download** `reFrozen-0.2.0.dmg`. To check it, run `shasum -a 256 reFrozen-0.2.0.dmg` in
   Terminal, in the folder with the download. It must print
   `db1ff96c3e839bb7c2450db525f37ceca8ff08ba367fe200cb0a7af550685643`.
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

## LAN games between Macs

- **Every Mac runs reFrozen 0.2.0** on the same local network.
- In the game, open **Local Area Network** from the multiplayer menu, then host a game or join
  one. If you don't have a game's custom map, it downloads from the host when you join.
- **The local network permission.** The first time you join a game, macOS asks *Allow "refrozen"
  to find devices on local networks?* Choose **Allow**. Until it is allowed, joining fails
  silently: the game appears in the list, but **Join** does nothing. The question appears at the
  first join, not when hosting.
- **The original Windows 1.26a client** is experimental: playing with it has not yet been
  officially verified, and official testing is planned for v0.2.1. Community reports are welcome,
  including successful connections, disconnections and synchronization issues.

## Known issues

v0.2.0 is a beta. The [release notes](https://github.com/retronative/refrozen/releases/tag/v0.2.0) list its known issues:

- **An intermittent crash in long AI matches** (as in 0.1.0). It happens occasionally in long
  matches with many computer players. Its mechanism has been identified; a fix is not verified
  yet and is planned for 0.2.1.
- **Terror of the Tides** (The Frozen Throne's Sentinel campaign) stops the game when you start
  it: the game plays its opening cinematic through DirectShow, which reFrozen does not provide.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded.** Saving
  works; saves load on Booty Bay and DotA v6.78c AI 1.4e.
- **The game opens on the Mac's main display** and can't be moved to another display. To play on
  an external monitor, make it the main display in System Settings → Displays before you start
  the game.
- A short pause before a map starts loading, and a loading bar that freezes for a few seconds on
  large maps.
- reFrozen is not notarized: macOS blocks the first open until you choose **Open Anyway** (see
  [Install](#install)).

If the game crashes, a report is written to `~/Library/Application Support/reFrozen/crashes`.
Please report it with that crash report.

## Uninstall

Quit reFrozen, move it from Applications to the Bin, and delete
`~/Library/Application Support/reFrozen`. That folder holds your installed game, including your
encoded CD keys, so never attach it, or files from it, to a bug report. Your installers and maps
are never changed.

## Before you ask

v0.2.0 plays offline and over LAN between Macs. Private servers, iCCup and Battle.net are not
part of it. Read the [FAQ](faq.md) for more.
