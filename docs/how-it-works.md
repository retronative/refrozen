---
title: How it works
description: Static recompilation explained in plain terms, and why reFrozen is neither an emulator nor Wine.
order: 2
---

# How it works

reFrozen runs Warcraft III: The Frozen Throne 1.26a natively on Apple Silicon by **static
recompilation**: the game's code is translated ahead of time into native arm64 code, and a native
runtime takes the place of the parts of Windows the game expects to find.

## The short version

The original game is a 32-bit Windows program written for x86 processors. A Mac with Apple
Silicon speaks a different machine language (arm64) and has no Windows, no Direct3D and no
DirectSound. reFrozen bridges both gaps:

1. **Translate the code once.** A recompiler (built on *x86recomp*, an MIT-licensed open-source lifter) reads
   the game's x86 machine code from your own copy and turns it into C++, which is then compiled
   into ordinary native arm64 code.
2. **Replace the platform.** A native runtime, built on *SDL3*, provides what the game calls into:
   windows and input (Win32), graphics (the game's rendering, drawn natively on the Mac), sound
   (DirectSound and the game's audio library) and file access.
3. **Run it.** The result is a native Mac process. There is no interpreter running underneath it.

## Static recompilation vs. emulation

| | Emulator | Wine / compatibility layer | reFrozen |
|---|---|---|---|
| Runs the original x86 code | Interpreted or JIT-translated while playing | Needs an x86 CPU (or a translator such as Rosetta) | No: translated ahead of time to arm64 |
| Windows APIs | Emulated whole machine or OS | Reimplemented, general-purpose | Reimplemented, only what this game uses |
| Virtual machine | Often | No | No |
| Just-in-time code generation | Usually | Via the translator | None |

An **emulator** imitates a whole machine while the game runs. **Wine** reimplements Windows for
any program, but still needs x86 code to be executed. reFrozen does the translation work *before*
you play, for this one game version, so what runs is plain arm64 code with a small, purpose-built
runtime.

## Why only one version

Static recompilation works on an exact binary. Every function, jump table and data structure is
mapped for one specific build of the game: Warcraft III 1.26a. A different patch is a different
program. See [Compatibility](compatibility.md).

## Why your own copy

The translated code is derived from Blizzard's executables, so it is never distributed. Instead,
reFrozen produces the native game modules **on your Mac, from your own installers**. The project
itself ships only its own tools: the recompiler, the runtime and the native installer.

## What has been verified

Development is organised in gated milestones, each passed only when its acceptance criteria are
observed: from the first correct analysis of the game code, through native start-up and menus, to
a full local DotA match played to the score screen with sound. The current state of every
milestone is on the [Status and releases](status.md) page.
