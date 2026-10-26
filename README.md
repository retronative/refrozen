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

**M5 complete (pending sign-off):** the recompiled Warcraft III 1.26a runs natively on Apple Silicon from an install made natively from your own installers, and plays a local DotA match to the end: menus, Start Game, an in-game hero, the enemy base destroyed, the score screen and a saved replay, with Miles audio, in a Retina-aware window or borderless fullscreen (Ctrl+Cmd+F). AI opponents and long sessions are next (M6). Offline target: DotA 6.85oz LoD. Milestones and their gates are in
[reference/ROADMAP.md](reference/ROADMAP.md); open questions are in
[reference/FEASIBILITY.md](reference/FEASIBILITY.md).

## Approach (proposed)

Statically recompile the game's executable codefor arm64, and run it on a native runtime that 
reimplements the platform it was written for. Here the guest is **x86 Win32** (`war3.exe` + 
`Game.dll` 1.26a and their DLLs), not an Xbox 360, so the runtime replaces Win32, Direct3D 8/9, 
DirectSound and Storm instead of an Xbox kernel. M0 decides whether this is feasible.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). Report security problems privately, as described in
[SECURITY.md](SECURITY.md).

## Licence

reFrozen is free software under the GNU General Public License, version 3 or (at your option) any
later version (GPL-3.0-or-later): see [COPYING](COPYING) and [NOTICE](NOTICE). Third-party
components and their licences are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
