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
> assets, maps or executables. Recompiled code is generated on your Mac from your own copy and
> is never committed. Please don't ask for, or share, game files.

## Status

**M0 complete (pending sign-off):** native install + 1.26a patch reproduce the official result, approach chosen (x86recomp), DotA compatibility tested. No game code is recompiled into a running port yet. Milestones and their gates are in
[reference/ROADMAP.md](reference/ROADMAP.md); open questions are in
[reference/FEASIBILITY.md](reference/FEASIBILITY.md).

## Approach (proposed)

Statically recompile the game's executable codefor arm64, and run it on a native runtime that 
reimplements the platform it was written for. Here the guest is **x86 Win32** (`war3.exe` + 
`Game.dll` 1.26a and their DLLs), not an Xbox 360, so the runtime replaces Win32, Direct3D 8/9, 
DirectSound and Storm instead of an Xbox kernel. M0 decides whether this is feasible.
