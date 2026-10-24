# x86-32 (Win32 PE) -> arm64 Static Recompilation and Binary Lifting Toolchains (for WC3 TFT 1.26a)

Research date: 2026-10-24. Repo activity data comes from the GitHub REST API, queried this session (`pushed_at` = last push to any branch, which can overstate activity). "Verified" means it was read from the primary source this session. "Unverified" or "from prior knowledge" is marked as such.

## Q1: Is there an x86 analogue of XenonRecomp / N64Recomp / rexglue (per-function C/C++ emission plus a runtime)?

### Takeaway
Yes. As of October 2026 there are three, and all are very recent. **JTM-rootstorm/x86recomp** is the closest fit: an MIT-licensed lifter from 32-bit Win32 PE to portable C++20, with a Win32/DirectX HLE runtime, built for macOS Apple Silicon as a hard requirement. It is new, tiny (2 stars) and unproven on a game as large as WC3. **sp00nznet/xboxrecomp** applies the same approach to original-Xbox x86 binaries. It is more mature (937 commits, 287 stars) and also targets macOS arm64. **M-HT/SR (SRW)** is a long-running static recompiler for DOS/Win32 games that has shipped real ports to arm64 and macOS, but through a different design (an assembly/LLVM IR route, with hand-annotated per-game info).

### Cited Findings
**JTM-rootstorm/x86recomp** (verified from the README and ARCHITECTURE.md)
- Self-description: "Static recompilation of 32-bit x86 Windows games into native 64-bit programs ... A game's machine code is translated ahead of time into C++ and linked against a runtime that reimplements the parts of Windows and its middleware the game uses. There is no emulator, interpreter or Wine in the result." — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp)
- Lifter (`recomp_lift`) "decodes a PE with Zydis and emits C++ for every function, one basic block at a time, with exact x86 integer and flag semantics." DLLs the game loads are lifted in the same run (`--module game.dll`). That matters for a war3.exe + Game.dll + Storm.dll layout. — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp)
- The runtime provides a 4 GiB guest address space, PE loading, threads and SEH. HLE covers kernel32/user32/gdi32/advapi32 on POSIX+SDL3, Miles Sound System, Bink, DirectDraw7/D3D7, OpenGL 1.x, D3D9/D3DX9 (in progress), DirectSound 8, DirectInput 8 and dbghelp. Graphics use SDL_GPU, which is "native Metal on macOS". HLSL/D3D9 SM1-3 shaders are translated to GLSL. — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp)
- Stated requirements: "Linux x86-64, or macOS on Apple Silicon". The macOS build uses Homebrew llvm@22. — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp)
- Design constraint: "macOS on Apple Silicon with a native Metal renderer is a requirement, not an afterthought. Nothing in the lifter output or the runtime may assume an x86 host, 4 KiB pages". Also: "No emulation in the shipping binary ... An indirect branch to an address that was not lifted is a fatal error (reported with its VA so it can be added to the manifest)". — [x86recomp ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- The author's rationale: "No maintained tool lifts Win32 x86 PE to portable C. Early-2000s MSVC code is integer + x87, ~190 mnemonics, few SEH frames, so a purpose-built lifter is tractable (rexglue-style: one C++ function per guest function)." — [x86recomp ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- Function list sources: a Ghidra `functions.tsv` export, PE exports, and a per-game `lifter.manifest` (extra entries, resume sites for SEH/longjmp, setjmp functions). Jump tables also come from Ghidra. — [x86recomp ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- Projects using it: DS1-Rebuilt (Dungeon Siege, 2002), "where it was developed"; CoD1-Reissued (Call of Duty, 2003), "in progress"; LSWTCS_Rebricked (2009), "started". — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp); DS1-Rebuilt is described as "Making Dungeon Siege Work on Linux and MacOS natively" — [DS1-Rebuilt](https://github.com/JTM-rootstorm/DS1-Rebuilt)
- License: MIT. Dependencies: SoftFloat 3e (BSD-3), Zydis (MIT), SDL3 (zlib), ffmpeg (LGPL, linked dynamically). — [x86recomp README](https://github.com/JTM-rootstorm/x86recomp)
- Activity (GitHub API): 80 commits, the first visible on 2026-10-12 and the latest on 2026-10-19. Last push 2026-10-19. 2 stars. The public history is only about one week old, which suggests a recent publication or a squashed history. — [GitHub API repos/JTM-rootstorm/x86recomp](https://api.github.com/repos/JTM-rootstorm/x86recomp)

**sp00nznet/xboxrecomp** (verified from the README and changelog)
- "Turn any Xbox game binary into a native executable for Windows, Linux or macOS". It claims to be "the first public static recompilation toolkit for the original Xbox." It is MIT licensed, with LGPL-2.1+ parts from xemu (the APU sources and NV2A register definitions). — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp)
- Every function is emitted as `void f(void)` with guest registers as globals. Output is split into many `.c` files plus a dispatch file. Indirect calls are called "the hardest 10%" and go through `RECOMP_ICALL` dispatch, with guarded direct calls based on runtime-recorded targets. A conformance suite compares lifted C with the real CPU (5,261 vectors, zero mismatches). — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp)
- Game status is mixed. Burnout 3 (22,097 functions): "an earlier 'playable' claim is retired", and it currently reaches RenderWare init. Wreckless boots to game main and then crashes. Half-Life 2 (Xbox) loads a level and draws its loading screen. — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp)
- Host targets include Linux and macOS on x86-64 and arm64 (SDL2/OpenGL). Releases v0.1 (March 2026) through v0.16.0 (October 2026). 937 commits, 287 stars, last push 2026-10-21. — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp); [GitHub API](https://api.github.com/repos/sp00nznet/xboxrecomp)
- A downstream project, BLiNX 2, lifts game x86 to C with xboxrecomp and links a replacement Xbox kernel plus NV2A/APU runtime. — [blinx2-recomp README](https://raw.githubusercontent.com/apexJCL/blinx2-recomp/HEAD/README.md)

**M-HT/SR** (verified from the README)
- "A project to statically recompile DOS and Windows game executables to create Windows (x86/x64) or Linux (x86/x64/arm/arm64/riscv64) or MacOS (x64/arm64) versions of the games." The supported Win32 games are Septerra Core and Battle Isle 3. The DOS games include Warcraft: Orcs & Humans. — [M-HT/SR](https://github.com/M-HT/SR)
- SRW, the Windows recompiler, "takes the original executable as an input together with information about the original executable and produces x86 / llasm / x64 assembler version". `llasm` converts that output to LLVM IR "which can be compiled to native code". The per-game executable info lives in `SRW-games`. — [M-HT/SR](https://github.com/M-HT/SR)
- License: MIT, also offered as GPLv2+ and LGPLv2.1+. 426 stars. Last commit 2026-08-27. — [M-HT/SR](https://github.com/M-HT/SR); [GitHub API](https://api.github.com/repos/M-HT/SR)

**Lineage context**
- XenonRecomp (Xbox 360 PPC, MIT, 6.6k stars) last pushed 2025-08-04. rexglue-sdk (Xbox 360 recomp runtime, 1.2k stars, no SPDX license detected) last pushed 2026-10-02. Both are PowerPC only. — [GitHub API XenonRecomp](https://api.github.com/repos/hedge-dev/XenonRecomp); [GitHub API rexglue-sdk](https://api.github.com/repos/rexglue/rexglue-sdk)
- The 2026 recomp wave is mostly Xbox 360 (Simpsons Game, GoldenEye XBLA, Castlevania SotN XBLA). — [generationamiga](https://www.generationamiga.com/2026/07/20/the-simpsons-game-returns-with-a-new-windows-and-linux-recompilation-release/); [tbreak](https://tbreak.com/goldeneye-007-xbox-360-pc-recompilation/)

### Inferences
- x86recomp's design matches WC3 1.26a closely: an MSVC Win32 PE, multiple DLLs lifted in one run, an exact x87 model, SEH, a macOS Metal backend, and a fixed 32-bit data layout. The gaps for WC3: its HLE covers D3D7/D3D9 in progress and Miles/Bink, but WC3 1.26a uses Direct3D 8 (or OpenGL with `-opengl`). WC3's network stack (Winsock/Battle.net) and Storm.dll's surface would also need HLE or lifting. The Direct3D 8 claim comes from prior knowledge and was not verified this session.
- Using `-opengl` and targeting x86recomp's existing OpenGL 1.x HLE could be the shortest graphics path. This is speculative and depends on WC3's GL feature use.
- Treat x86recomp as a reference design or fork base, not a turnkey tool. Its maturity rests on one author and about one week of public history. No game is stated to be fully playable in its README.
- xboxrecomp shows that lifting tens of thousands of functions (22k for Burnout 3) is feasible. It also shows the long tail: indirect calls, x87 edge cases and threading still block playability after more than 900 commits.

### Gaps
- Could not verify any game fully playable with x86recomp (DS1-Rebuilt status not read in depth).
- WC3 1.26a function count and indirect-call density are unknown. Game.dll's size suggests well over 22k functions (an inference).
- SRW internals (x87, indirect-jump handling) were not read in this session.

## Q2: Binary lifters — status, x86-32/Win32 PE support, license, fit

### Takeaway
None of the general-purpose lifters is a drop-in for Win32 x86-32 game recompilation. McSema (the only one that explicitly lifted 32-bit Windows PE) is archived. mctoll is archived and x86-64 ELF only. Rellume has no x86-32. RetDec is in limited maintenance and is a decompiler, not a recompiler. remill (Apache-2.0, active) can lift x86-32 instruction semantics but needs a CFG and recovery front end that you would have to supply, for example from Ghidra. That is the gap x86recomp and xboxrecomp fill with purpose-built lifters.

### Cited Findings
| Tool | x86-32 | Win32 PE | Status (API) | License | Source |
|---|---|---|---|---|---|
| **McSema** | yes | yes (32/64-bit PE lifting; Windows build "Experimental") | **Archived 2022-08-23**, last push 2022-04-26 | AGPL-3.0 | [mcsema](https://github.com/lifting-bits/mcsema) |
| **remill** | yes (x86, amd64 incl. AVX/AVX-512; AArch64, SPARC) | n/a (instruction semantics library only) | Active, last push 2026-08-27, 1.9k stars | Apache-2.0 | [ToB remill](https://trailofbits.com/tools/remill/); [API](https://api.github.com/repos/lifting-bits/remill) |
| **anvill** (McSema successor front end) | not verified | not verified | Last push 2024-09-03 (stale) | AGPL-3.0 | [API](https://api.github.com/repos/lifting-bits/anvill) |
| **rellic** (LLVM IR -> goto-free C) | n/a | n/a | Last push 2026-02-12 | Apache-2.0 | [API](https://api.github.com/repos/trailofbits/rellic) |
| **Rellume** | **no**: "lifter for x86-64/AArch64/RISC-V64" | n/a | Active, last push 2026-09-10 | LGPL-2.1 | [rellume](https://github.com/aengelke/rellume) |
| **Instrew** (dynamic, on Rellume) | inherits Rellume | Linux DBI | Last push 2026-09-10 | LGPL-2.1 | [API](https://api.github.com/repos/aengelke/instrew) |
| **llvm-mctoll** | **no**: "X86-64 and Arm32 Linux/ELF ... Raising Windows, OS X and C++ binaries needs to be added"; no SSE/AVX | no | **Archived**, last push 2024-06-22 | NOASSERTION (LLVM-style) | [mctoll](https://github.com/microsoft/llvm-mctoll) |
| **RetDec** | yes (32-bit x86, ARM, MIPS, PIC32, PPC) | yes (ELF, PE, Mach-O, COFF) | "limited maintenance mode due to a lack of resources"; last push 2026-05-26 | MIT | [retdec](https://github.com/avast/retdec) |
| **rev.ng** | not verified this session | not verified | Active, last push 2026-10-22; built on LLVM + QEMU | GPL-2.0 | [revng](https://github.com/revng/revng) |
| **BinRec** (EuroSys 2020) | paper-era x86 | Linux | Research; lifts *dynamic traces* to IR and recompiles; recovered all SPEC INT 2006 incl. C++. No repo found this session | ? | [BinRec paper](https://download.vusec.net/papers/binrec_eurosys20.pdf) |
| **Polynima** (EuroSys 2024) | not verified | not verified | "Practical Hybrid Recompilation for Multithreaded Binaries" (Deshpande, Parzefall, Hetzelt, Franz) | ? | [DOI 10.1145/3627703.3650065](https://api.openalex.org/works/doi:10.1145%2F3627703.3650065) |
| **Lasagne** (PLDI 2022) | x86-64 -> Arm (not verified for 32-bit) | Linux | Static BT with formally proved x86 to Arm concurrency mappings. Fences cut by up to ~65%, average 45.5%. Artifact on Zenodo | ? | [PLDI'22](https://pldi22.sigplan.org/details/pldi-2022-pldi/52/Lasagne-A-Static-Binary-Translator-for-Weak-Memory-Model-Architectures); [Zenodo](https://zenodo.org/records/6408463) |
| **"No Bit Left Behind"** (arXiv, Sept 2026) | x86-64 input only | not stated | Brute-force superset CFG (every byte offset a candidate target). Unresolved computed branches become dispatch-table lookups. Validated by fully static cross-compilation to AArch64. Code release not stated | ? | [arXiv 2609.16423](https://arxiv.org/abs/2609.16423) |

- The McSema README itself says the repo "was archived by the owner on Aug 23, 2022. It is now read-only." — [mcsema](https://github.com/lifting-bits/mcsema)
- x86recomp's author concluded that "No maintained tool lifts Win32 x86 PE to portable C." — [x86recomp ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)

### Inferences
- remill semantics with a Ghidra-derived CFG, then LLVM to arm64, is a viable but heavyweight alternative. You would rebuild x86recomp's runtime pieces (HLE, SEH, x87) anyway. The remill state-struct model also tends to produce slower code than a purpose-built C++ emitter unless heavily optimized (an inference, not measured).
- Ghidra p-code based lifting: no maintained, game-oriented p-code to C/LLVM recompiler was found this session. x86recomp uses Ghidra only for function and jump-table discovery.
- The research systems (BinRec, Polynima, Lasagne, No Bit Left Behind) target Linux ELF and benchmarks, mostly x86-64. They are useful for ideas (trace-guided CFG completion, fence minimization, superset CFG) but not as tools.

### Gaps
- rev.ng's current x86-32 and PE support, and Ghidra-based lifters (e.g. ghidra-to-LLVM projects), were not verified.
- No repo was located for BinRec or Polynima.

## Q3: Technical hard parts for x86-32 static recomp on macOS arm64

### Takeaway
The practical answers from the 2026 projects: take function and jump-table discovery from Ghidra plus a manual manifest, and make unlifted indirect targets a fatal, logged error. Model x87 in software (SoftFloat, 80-bit, with precision/rounding control). Keep flags eager, letting the compiler drop dead flag computations. Map a 4 GiB arena at `base + guest_va`, with the PE mapped at its real VAs. Handle stdcall/thiscall through guest-stack thunks, with host objects exposed only as 32-bit handles. TSO versus ARM weak memory is largely unaddressed in these public projects.

### Cited Findings
- **Function discovery and indirect branches:** x86recomp uses "Indirect calls/jumps: dense table indexed by (va - .text start); addresses in the thunk region go to HLE handlers; anything else is fatal". — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md). xboxrecomp uses closed-CFG proofs, callback recovery from immediates, a vtable classifier (`func_id`), plus an ICALL trace ring buffer. — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp). The academic alternative is a superset CFG over all byte offsets plus a dispatch table. — [arXiv 2609.16423](https://arxiv.org/abs/2609.16423)
- **x87:** x86recomp uses "exact 80-bit x87 (precision and rounding control, status-word flags) on Berkeley SoftFloat with integer fast paths, tested bit for bit against a real x87". Straight-line x87 code becomes "runs" keeping the FPU stack in locals, and a symbolic stack (X87Sim) resolves st(i). The rationale: MSVC CRT helpers and D3D change the control word, so precision must be modelled. — [x86recomp](https://github.com/JTM-rootstorm/x86recomp); [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md). xboxrecomp's x87 bug history shows the risk: FIST ignored the rounding mode, fxch was a no-op, and 904 instructions across 28 mnemonics initially lifted to comments. — [xboxrecomp changelog](https://github.com/sp00nznet/xboxrecomp)
- **SSE:** x86recomp models XMM/MXCSR "with SoftFloat lanes and x86 NaN rules, tested bit for bit". — [x86recomp](https://github.com/JTM-rootstorm/x86recomp)
- **Flags cost:** "Registers are cached in locals per function and flags computed eagerly into locals (clang drops dead ones)". Flags are packed into one EFLAGS word on calls, using a single 32-bit store and load "which every x86 and arm64 core forwards". — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- **Calling conventions and host boundary:** direct `call` becomes a C++ call and the real return address is pushed to the guest stack. `ret N` pops, and a tail jmp becomes a tail call. Guest to host: a pointer becomes `base + addr`. Host to guest: kernel objects become 32-bit handles, and COM objects are guest-memory objects whose vtables point at thunk addresses (0x7F000000+). — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- **SEH:** the fs:[0] chain lives in guest memory, and RaiseException walks it calling lifted handlers. Resuming at a catch or except target throws a host exception (GuestResume) so that the host stack mirrors the guest. — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- **Memory model on macOS arm64:** "One 4 GiB reservation; guest VA A lives at host base + A. The image is mapped at its real VAs (0x400000..)". The preferred base is 0x10_0000_0000, "outside macOS's 4 GiB __PAGEZERO ... macOS may place it elsewhere, the hint being advisory". Host page granularity is 16 KiB on Apple Silicon versus Win32's 4 KiB commit and 64 KiB allocation granularity, so protections are tracked in a per-guest-page table. A guest load costs "one add of a base register plus the load itself, on both x86-64 and ARM64". — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- **Low-4GB pitfalls:** xboxrecomp found that on arm64 macOS "every fixed base sits inside `__PAGEZERO`". macOS has no `MAP_FIXED_NOREPLACE`, and bare `MAP_FIXED` silently replaced live mappings. — [xboxrecomp changelog](https://github.com/sp00nznet/xboxrecomp)
- **Address-space headroom:** x86recomp's allocator currently hands out only addresses below 0x80000000. Allowing up to 0xFFFE0000 is "planned, opt-in". — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)
- **Threads and atomics:** xboxrecomp added `lock`-prefixed atomics in v0.8.0 ("Guest critical sections had been no-ops until then") and serializes SRWLOCK. Neither project's docs (as read) discuss TSO versus the ARM memory model. — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp)
- **TSO in research:** Lasagne inserts fences derived from proven x86 to Arm mappings and minimizes them (average 45.5% fewer). — [PLDI'22](https://pldi22.sigplan.org/details/pldi-2022-pldi/52/Lasagne-A-Static-Binary-Translator-for-Weak-Memory-Model-Architectures)
- **Rosetta:** "Rosetta cannot run 32-bit x86", per xboxrecomp's conformance notes. Testing on Apple Silicon therefore used i386 Docker execution. — [xboxrecomp changelog](https://github.com/sp00nznet/xboxrecomp)
- **Self-modifying code:** x86recomp forbids runtime x86 decoding entirely (constraint 2). — [ARCHITECTURE.md](https://github.com/JTM-rootstorm/x86recomp/blob/main/ARCHITECTURE.md)

### Inferences
- WC3 is mostly single-threaded game logic with worker threads (audio, loading, networking). Plain loads and stores on ARM without fences risk subtle races only where the game relies on x86 ordering for lock-free code. Lifting `lock`-prefixed ops to seq_cst atomics and Interlocked* to host atomics likely covers most cases. This is an inference: WC3's lock-free patterns were not verified.
- Apple's hardware TSO mode (used by Rosetta) is not available to normal third-party processes. This comes from prior knowledge and was not verified this session.
- Self-modifying code, anti-tamper, and Storm.dll/Game.dll runtime patching (common in WC3 mod loaders) would need to be removed or reimplemented as native hooks.
- Game.dll's JASS VM, which interprets bytecode, is ordinary C++ and liftable. It is not self-modifying code.

### Gaps
- No public measurement of WC3-sized lifted code performance on Apple Silicon.
- Whether WC3 1.26a uses any SMC, packed or encrypted code sections, or relies on TSO in lock-free code is unknown.

## Q4: Documented successes statically recompiling a large 32-bit x86 Windows game to another architecture

### Takeaway
There are documented successes, but on smaller or older titles. M-HT/SR ships Septerra Core and Battle Isle 3 (Win32) and Warcraft: Orcs & Humans (DOS) to arm64 and macOS. notaz's 2014 StarCraft and Diablo ARM ports (x86 disassembly to C, linked with ARM Wine) are a historical precedent. In 2026, x86recomp (Dungeon Siege on macOS/Linux) and xboxrecomp (Burnout 3, Xbox HL2) are in progress, and none clearly claims full playability of a large title. No WC3 recompilation was found.

### Cited Findings
- M-HT/SR supports building Septerra Core and Battle Isle 3 (Win32) and Warcraft: Orcs & Humans (DOS) for "MacOS (x64/arm64)" and Linux arm/arm64/riscv64. — [M-HT/SR](https://github.com/M-HT/SR)
- notaz's StarCraft port for OpenPandora (ARM): the game was disassembled, converted from x86 assembly to C with custom tools, and linked against an ARM Wine build for Win32. The same approach reportedly made Diablo 1 and 2 playable on ARM. This was reported via forum/aggregator results; the primary source was not fetched. — [search result: OSNews on Wine on ARM](https://www.osnews.com/story/30880/running-windows-software-on-arm-with-wine/); [linux.org.ru thread](https://www.linux.org.ru/forum/general/14993590/14997693/history)
- x86recomp's DS1-Rebuilt is "Making Dungeon Siege Work on Linux and MacOS natively". The README only says the tool was developed there, and makes no playability claim. — [DS1-Rebuilt](https://github.com/JTM-rootstorm/DS1-Rebuilt); [x86recomp](https://github.com/JTM-rootstorm/x86recomp)
- xboxrecomp: Burnout 3's "playable" claim was retired, Xbox Half-Life 2 reaches level load and loading screen, and Wreckless reaches game main. — [xboxrecomp](https://github.com/sp00nznet/xboxrecomp)
- The Recompendium index lists Takedawn (Burnout 3) as an Xbox x86 to C port compiled for x86-64 and arm64. — [Recompendium](https://nio03.github.io/unricopie/en/)
- Academic recompilers report SPEC-scale successes (BinRec: all SPEC INT 2006, including C++), not games. — [BinRec paper](https://download.vusec.net/papers/binrec_eurosys20.pdf)

### Inferences
- The closest precedent to WC3 (a 2002 Blizzard MSVC C++ title with a Storm.dll dependency) is notaz's StarCraft/Diablo work, but that relied on Wine. The modern no-Wine route is x86recomp's.
- A realistic WC3 plan: fork or vendor x86recomp; feed it Ghidra function and jump-table exports for war3.exe, Game.dll and Storm.dll (or reimplement Storm natively, since StormLib-compatible MPQ code exists); add D3D8 or use the OpenGL path; add Winsock HLE. Expect a long tail on indirect calls (vtables, JASS native tables) and x87. This is speculative planning, not verified.

### Gaps
- No primary source fetched for notaz's StarCraft port details.
- No WC3-specific recompilation or lifting project found in this session's searches.
- Playability status of DS1-Rebuilt and CoD1-Reissued not checked.
