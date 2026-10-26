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

## In reFrozen.app

The app (`scripts/release/make_release_app.sh`) carries these, built from checksum-pinned sources
(`scripts/release/build_deps.sh`). Each one's licence text is in the app, under
`Contents/Resources/licenses/third-party/`.

| Project | In the app | Licence |
|---|---|---|
| **x86recomp** (with reFrozen's patches) | the runtime libraries and the lifter | MIT |
| **SDL3** 3.4.18 | a shared library (windows, input, graphics, audio) | zlib |
| **StormLib** 9.40 | a shared library, used by the installer step | MIT |
| **glslang** 16.6.0 | linked into the runtime (shader compilation) | BSD-3-Clause and others, listed in its `LICENSE.txt` |
| **SPIRV-Tools**, **SPIRV-Headers** 1.4.363.0 | linked into the runtime | Apache-2.0; SPIRV-Headers: MIT-style (Khronos) |
| **SPIRV-Cross** 1.4.363.0 | linked into the runtime (shaders for Metal) | Apache-2.0 |
| **Berkeley SoftFloat 3** | linked into the runtime (x87 floating point) | BSD-3-Clause |
| **Zydis** 4.1.1 and **Zycore** | linked into the lifter | MIT |
| **LLVM** 23.1.4, `llvm/lib/Demangle` only | linked into the runtime (symbol demangling) | Apache-2.0 WITH LLVM-exception |
| Typefaces **Cinzel**, **Cormorant Garamond**, **Inter** | the setup window | SIL Open Font License 1.1 |

The app links no FFmpeg. The installer and builder steps run on Apple's own Python and Command Line
Tools, which are on the player's Mac and not part of the app.

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
