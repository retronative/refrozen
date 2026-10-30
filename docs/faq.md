---
title: FAQ
description: Answers to common questions about reFrozen, the native Warcraft III 1.26a port for Apple Silicon Macs.
order: 4
---

# Frequently asked questions

## Is reFrozen an emulator?

No. An emulator imitates a computer while the game runs. reFrozen translates the game's x86 code
into native arm64 code *before* you play, and pairs it with a native runtime that replaces the
Windows, Direct3D and DirectSound functions the game uses. There is no virtual machine and no
just-in-time code generation. See [How it works](how-it-works.md).

## Do I need Wine, CrossOver or a virtual machine?

No. reFrozen does not use Wine at any point, not even for installing: its native installer unpacks
the official installers directly on macOS.

## Can you give me the game, or a pre-built copy?

No, and please don't ask. reFrozen never distributes Blizzard's binaries or installers, translated
game code, game assets, maps, CD keys or iCCup components. You need your own legally obtained copy
of *Warcraft III: Reign of Chaos* and *The Frozen Throne*; the native game modules are generated on
your Mac from that copy.

## Will it work online, on iCCup or on Battle.net?

Not online. v0.2.1 plays offline and over LAN between Macs on the same local network (see
[Getting started](getting-started.md#lan-games-between-macs)); LAN games with the original Windows
1.26a client are experimental and not yet officially verified. Private servers that players run
themselves are a later step (M7b). iCCup support (M8) would only ever happen with iCCup's
official cooperation and within its anti-cheat requirements; nothing is bypassed. Battle.net is not
supported. See [Status and releases](status.md).

## Is there a release?

Yes. **reFrozen 0.2.1**, a maintenance release of the 0.2.0 Beta with LAN multiplayer between
Macs, was published on 30 October 2026. See [Getting started](getting-started.md) to install it, and the
[release page](https://github.com/retronative/refrozen/releases/tag/v0.2.1) for its notes and known issues. 0.2.0 Beta was
published on 30 October 2026, and the first release, 0.1.0 (alpha, offline only), on 27 October 2026. The current state is on the [Status and releases](status.md) page.

## Is it legal?

reFrozen is designed so that it never distributes anything that belongs to Blizzard: you must own
the game, you supply your own installers and keys, and every game-derived file is produced on your
own Mac. The project ships only its own code. That said, this is not legal advice, and laws and
licence terms differ by country. If you are unsure, read the game's licence terms and seek
independent advice. See the [Disclaimer](disclaimer.md).

## Why version 1.26a?

Static recompilation translates one exact build of the game, so that the recompiled code matches
it instruction for instruction. reFrozen targets Warcraft III 1.26a (build 1.26.0.6401), installed
from the 1.21b retail installers plus Blizzard's official 1.26a patch. The DotA maps tested on it,
the 6.85-series LoD build and the 6.83d AI builds, load and play, and the LoD build's map script
checks with zero errors against 1.26a's own game scripts.

## Does it run on Intel Macs?

Intel Macs are not targeted. reFrozen is built for Apple Silicon.

## Which DotA maps work?

Pure-JASS maps such as the 6.85-series LoD builds and the 6.83d AI builds. iCCup's native-plugin
builds do not. Details are on the [Compatibility](compatibility.md) page.
