# Third-party notices

reFrozen is free software under the GNU General Public License, version 3 or (at your option) any
later version (GPL-3.0-or-later; [`COPYING`](COPYING), [`NOTICE`](NOTICE)). It is built from
software by others under their own licences, listed here. Licence texts are in
[`LICENSES/`](LICENSES).

reFrozen has not made a release yet. This repository contains no third-party source code except
the modifications to x86recomp below; the other components are fetched or installed when you build
it. A release will carry these notices, the licence texts and each bundled library's licence files.

## In this repository

| Project | What it does here | Licence | Text |
|---|---|---|---|
| **x86recomp**: Copyright (c) 2026 JT | The static recompiler (lifter) and the Win32 runtime that reFrozen builds on. `scripts/setup_tools.sh` checks out a pinned commit and applies reFrozen's modifications, `patches/x86recomp/*.patch`. | MIT | [`LICENSES/x86recomp-MIT.txt`](LICENSES/x86recomp-MIT.txt) |

## Used when you build reFrozen

These are not part of this repository; their licences apply to the copies you install or fetch.

| Project | What it does here | Licence |
|---|---|---|
| **SDL3** | Windows, input, graphics and audio under the runtime | zlib |
| **Berkeley SoftFloat 3** | x87 floating point in the runtime (fetched by x86recomp's build) | BSD-3-Clause |
| **FFmpeg** | Audio decoding in the runtime | LGPL-2.1-or-later (GPL-2.0-or-later, depending on how it was built) |
| **glslang**, **SPIRV-Cross** | Shader translation in the graphics device | glslang: several licences, listed in its `LICENSE.txt`; SPIRV-Cross: Apache-2.0 |
| **LLVM** (demangler; `llvm-mc` in tests) | Symbol demangling in the runtime's DbgHelp, and assembling test programs | Apache-2.0 WITH LLVM-exception |
| **StormLib** | MPQ archive extraction in `scripts/mpq_extract.c` | MIT |
| **Ghidra** | Function analysis during development only; players don't need it | Apache-2.0 |
| **Wine** | A development reference only (`tools/wine/`, git-ignored); never part of reFrozen or its install path | LGPL-2.1-or-later |

## The website (`.website/`)

| Project | Licence |
|---|---|
| **Vue**, **Vue Router**, **Vite**, **Tailwind CSS**, **markdown-it** | MIT |
| Typefaces **Cinzel**, **Cormorant Garamond**, **Inter** (served as latin subsets, licence texts in `.website/public/fonts/`) | SIL Open Font License 1.1 |
