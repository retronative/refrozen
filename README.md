# reFrozen

Native recompilation of Warcraft III: The Frozen Throne (1.26a) for Apple Silicon, so that
*DotA Allstars* (v6.83) plays on macOS without Wine or a VM.

> [!IMPORTANT]
> **reFrozen is an unofficial fan project. It is not affiliated with, endorsed by or sponsored
> by Blizzard Entertainment, Inc.** *Warcraft* and *The Frozen Throne* are trademarks of
> Blizzard Entertainment, Inc. and are used here only to describe the game. *DotA Allstars* is
> a community map by its respective authors.
>
> **No game files are included or distributed.** You need your own legally obtained copy of
> Warcraft III: Reign of Chaos and The Frozen Throne. The repository contains no game code,
> assets, maps or executables. It does contain metadata from analysing the game's executables:
> function and jump-table addresses with auto-generated names (`config/symbols/`), lifter
> manifests (`config/*.manifest`) and the names of the system functions the game imports.
> Recompiled code is generated on your Mac from your own copy and is never committed. Please
> don't ask for, or share, game files.

## Status

**[reFrozen 0.1.0 (alpha)](https://github.com/retronative/refrozen/releases/tag/v0.1.0) is available**, an offline-only pre-release for Apple silicon
Macs (macOS 14 or later). It installs Warcraft III 1.26a from your own installers, builds the game
for your Mac, and plays offline custom games, including full DotA matches with computer players,
with audio, Retina displays and borderless fullscreen (Ctrl+Cmd+F). To install it, follow
[Getting started](docs/getting-started.md); the [release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0) list its known
limitations. LAN, iCCup and Battle.net are not part of it.

The public status of each milestone is in [docs/status.md](docs/status.md). Milestones and their
gates are in [reference/ROADMAP.md](reference/ROADMAP.md), the release's gates in
[reference/RELEASE_PLAN.md](reference/RELEASE_PLAN.md), and open questions in
[reference/FEASIBILITY.md](reference/FEASIBILITY.md).

## Approach

reFrozen statically recompiles the game's executable code for arm64 and runs it on a native
runtime that reimplements the platform it was written for. Here the guest is **x86 Win32**
(`war3.exe` + `Game.dll` 1.26a and their DLLs), so the runtime replaces Win32, Direct3D 8/9,
DirectSound and Storm. The release ships only reFrozen's own tools (the recompiler, the runtime and
the native installer): the game is installed and recompiled on your Mac, from your own copy. See
[How it works](docs/how-it-works.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). Report security problems privately, as described in
[SECURITY.md](SECURITY.md).

## Licence

reFrozen is free software under the GNU General Public License, version 3 or (at your option) any
later version (GPL-3.0-or-later): see [COPYING](COPYING) and [NOTICE](NOTICE). Third-party
components and their licences are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
