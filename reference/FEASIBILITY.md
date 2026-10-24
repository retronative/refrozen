# reFrozen — Feasibility

Status: **M0, M1 and M2 passed (signed off 2026-10-24); M3 passed (2026-10-24), awaiting the user's sign-off.** Labels: VERIFIED (observed locally, reproducible),
OBSERVED (stated by a cited external source, not reproduced here), HYPOTHESIS, FALSIFIED,
UNRESOLVED. The full research report with sources is
[research/reports/WC3 native macOS port methods.md](research/reports/WC3%20native%20macOS%20port%20methods.md).

## TL;DR

| Question | Answer |
|---|---|
| Is the input the right release? | **Yes.** WC3 RoC + TFT 1.21b (enGB), patched with the official 1.26a English patch to build 1.26.0.6401. All binaries are x86 Win32 PE, MSVC 2005 (linker 8.0), unpacked (§2). |
| Recompile toolchain | **x86recomp + 13 reFrozen patches.** All eleven modules (war3.exe, game.dll, Storm.dll, Mss32.dll, msvcr80.dll, ijl15.dll, 5 Miles providers) lift with 0 reachable unimplemented sites, pass the structural audit, are byte-identical across runs and compile for arm64 (§7, §9, §10). |
| Native process (M2) | **Reaches `GameMain`.** One arm64 executable (`build/main/refrozen`) maps all ten modules at their preferred bases, binds all 675 cross-module imports (Storm by ordinal, Miles by name) to the lifted exports, runs the DllMains dependencies-first and calls `game.dll!GameMain`; every Win32 import without a handler is a strict stub (§9). |
| Runtime initialization (M3) | **Reaches the main menu loop** on the player's native install (CD keys stored as the official installer stores them), with the game's own OpenGL renderer on x86recomp's GL HLE; 3 consecutive launches, no fatal stop; sound is off (no wave device until M5) (§10). |
| Interactive menus (M4) | **Fully interactive and checked against the official client:** mouse/keyboard navigation through profiles, Single Player, Custom Game (DotA 6.85oz LoD selected), Options, focus, minimize/restore and Quit, 3 consecutive launches; fixed on the way: GL fog, the lifter's PUSH/POP slot size (the Quit crash), 16-bit texel precision; real Win32 painting, GDI drawing a strict stop (§11). |
| Playable local match (M5) | **A DotA 6.85oz LoD match plays to the score screen** from Start Game, 3 consecutive runs, replay saved, Miles audio through a real waveOut device; on the way: wsock32's local-game functions, overlapped replay file I/O, Miles' mixer table in the lift input; native fullscreen and Retina/HiDPI with mapped pointer input (§12). |
| DotA target | **DotA 6.85oz LoD** (pure JASS) for the offline milestones; iCCup native-plugin builds (6.83se/6.83s/6.85.308) deferred to M8, iCCup online compatibility, which needs M7 and iCCup's official cooperation (§5). |
| Miles | **Recompile Mss32.dll 6.1d and its providers** rather than extend x86recomp's Miles HLE (§8). |
| Reimplementation instead? | **No** for this goal. No open-source engine plays DotA 6.83 or keeps lockstep with real 1.26a clients. |
| Native install path | **Done.** `scripts/native_install.py` installs RoC + TFT, stores the CD keys as the installer does, and applies the 1.26a patch with no Wine; it reproduces the official result (all loose files and MPQ contents identical except the two `font.ccd` files), deterministically (§1, §10). |
| DotA on 1.26a | **Pure-JASS DotA maps work** (6.85oz LoD plays, IMBA loads, in the official client). **`DotA v6.83se` does not**: it is an iCCup build whose logic is a native plugin DLL, and stock 1.26a crashes loading it (§5). |

## 1. Inputs and install (VERIFIED 2026-10-24)

Player-supplied files in `../DOTA/` (read-only):

| File | SHA-256 |
|---|---|
| `Game cllient pack.zip` (since unpacked by the player) | `d447397a669af727ba49460172b0b8313bf525afb9e8e9d6b6ae70e8989db8a2` |
| `DotA v6.83se.w3x` | `10307817daf372ce57289acebdefe32284574b678e0762cb01cb7b157ca399c5` |

- **Native extraction:** `scripts/mpq_extract.c` (StormLib 9.40) extracts both installer tomes
  with the listfile from the Mac `Installer.app`: RoC 343 files, TFT 513, 0 failures. The tomes
  hold `PC/`, `MAC/`, `MAC-100*/` (1.21b classic Mac OS builds), `Common/` (MPQs, maps, movies).
- **Native = official for 1.21b:** `war3.exe`, `game.dll`, `Storm.dll` from the tomes are
  byte-identical to the official installers' output under Wine (`game/oracle-roc-1.21b.sha256`).
- **Installer (VERIFIED):** each tome carries its manifest,
  `InstallCD/InstallerFileList/InstallerFileList.xml`. Win32 branch: `<repack_into type="file">`
  copies (RoC 77, TFT 194 files) and `<repack_into type="mpq">` adds files into `war3.mpq` (150,
  from `PC-100/`, the original 1.00 files) and `War3x.mpq` (252, mostly `PC-100x/`, the original
  1.0x TFT files). CD-key steps: `<encrypt object="cdkey26">` into `font\font.gid` (RoC) /
  `font\font.exp` (TFT), `<encrypt object="user">` into `font\font.clh`, and `type="cdkey1encode"`
  of `Files\font\font.ccd`: the installed MPQs carry key-derived data (never printed or committed).
- **1.26a patch (VERIFIED):** `War3TFT_126a_English.exe` embeds an MPQ holding `Patch_War3x.mpq`
  (BNUpdate v2.133 input) with `patch.cmd`, `patch.lst`, `revert.lst`, `delete.lst`, `hdfiles.lst`
  (CRLF lines, `*`-terminated) and 723 records. Record = 0x18-byte header (`u16 0x18, u8 4, u8
  type, u32 ?, u32 base size, u32 new size, FILETIME`) + payload. Type 1 (422): whole file. Type 4
  (301): `u32 unpacked size` + RLE (bit 7 set: copy `(b&0x7F)+1` literals; else `b+1` zeros) of a
  BSDIFF40 blob with uncompressed blocks and 12-byte control entries (`u32 add, u32 extra, u32 seek`
  sign-magnitude) — StormLib's "BSD0" scheme. The u32 at +4 is unidentified (not CRC32 of base or
  result).
  - **Base rule:** a delta's base is NOT the installed 1.21b file but the original kept inside the
    installed MPQs: the `revert.lst` name of the target, read from `War3xLocal.mpq`/`War3x.mpq`/
    `war3.mpq`, whose size equals the header's base-size field (e.g. `War3x.mpq:Game.dll`, 8,671,295
    B, PE timestamp 2003). The installed 1.21b binaries are never read.
  - **Targets:** 2-field `patch.lst` lines (145) are loose files; 3-field lines (578) go into a new
    `War3Patch.mpq` (`delete.lst` removes the TFT installer's one) except plain names that exist as
    loose files (`replays.ico`, `CustomKeyInfo.txt`).
  - Tool: `scripts/bnupdate_patch.c` (C, no dependencies). Test: `tests/test_bnupdate_patch.py`,
    hand-computed (add with byte wrap, negative seek, both RLE token kinds, whole-file record, 4
    malformed inputs rejected). Mutations (seek read as unsigned; zero runs one byte short) both
    fail it.
- **Native install (VERIFIED):** `scripts/native_install.py` (StormLib via ctypes + the patcher)
  from the player's two installer folders and the patch EXE to a full 1.26a install in ~19 s.
  `--verify` against the Wine oracle: **PASS** — 204 loose files byte-identical, 0 differ/missing/
  extra; `war3.mpq` 10,676, `War3x.mpq` 5,863, `War3Patch.mpq` 576, `War3xLocal.mpq` 1,135 files
  identical (`War3xLocal.mpq` byte-identical as a whole); only the 5 CD-key files differ (3 in
  `war3.mpq`, 2 in `War3x.mpq`). MPQ (attributes) times are stamped, so two runs are
  byte-identical (tree hash `10f38579…4d83`). Log: `game/native-install-verify.log`.
- **Oracle:** the official installers + patch under Wine 11.18 (development only) give the 1.26a
  binaries. Copied to `game/oracle-1.26a/`:

| File | Size | SHA-256 | MD5 |
|---|---|---|---|
| `war3.exe` | 471,040 | `28173101fcbeb4cdcac0f83e0e724aa444209b479a2ac1c1784e0d4310889909` | `d0fcfe5155e2c8ab858c128147f916fb` |
| `game.dll` | 12,042,240 | `6d21bd9a0f9fbc8446f455c9e89ac994fed68174426fe608fcb9baefd4dec53c` | `ba5a2fe39f08a8272ddb1a45dfb62569` |
| `Storm.dll` | 339,968 | `eecc42b05a91413dee10588a654c6cca05836e7513af6c7c568a56124bf97d0a` | `9a2b885cabcadf8c9bdba934f88a818f` |
| `Mss32.dll` | — | `1f9a83f42de0e7899a7f6772e5cbad6ed10c16cc5f15246c8d80b9f4fe25fc4a` | `bb1defb5c29144511d344bcb88349269` |

  `Storm.dll` is identical (SHA-1 `5144e6bb…`) to the copy in the iCCup launcher.

## 2. Executables (VERIFIED, `llvm-objdump -p/-h`)

`game.dll`: image base 0x6F000000, size 0xBB5000, entry RVA 0x7E15B8, linker 8.0, no ASLR flag.

| Section | Raw size | Entropy |
|---|---|---|
| `.text` | 8,830,976 | 6.37 |
| `.rdata` | 1,974,272 | 5.47 |
| `.data` | 393,216 | 5.14 |
| `.rsrc` | 4,096 | 4.09 |
| `.reloc` | 835,584 | 6.39 |

Normal x86 code entropy and standard MSVC sections: no packer. A full `.reloc` table is available
for function and pointer discovery.

Static imports (named / ordinal-only):

| DLL | `war3.exe` | `game.dll` | `Storm.dll` | `Mss32.dll` |
|---|---|---|---|---|
| KERNEL32 | 112 | 111 | 84 | 86 |
| USER32 | 96 | 104 | 74 | 11 |
| GDI32 | 16 | 25 | 29 | — |
| MSVCR80 | 52 | 85 | 57 | — |
| mss32 (Miles) | 110 | 110 | — | — |
| Storm | 0 / 51 | 0 / 112 | — | — |
| WSOCK32 | 0 / 25 | 0 / 25 | — | — |
| OPENGL32 | — | 50 | — | — |
| ijl15 (JPEG) | — | 0 / 3 | — | — |
| COMCTL32, comdlg32, ADVAPI32, WININET, IMM32, SHELL32, WINMM, ole32, VERSION | small | small | small | WINMM 35 |

- Direct3D 8 is loaded at runtime: `game.dll` contains `d3d8.dll` and `Direct3DCreate8`
  strings (also `ws2_32.dll`). OpenGL is linked statically (the `-opengl` renderer).
- Storm is imported by ordinal only, so it should be recompiled with the game, not reimplemented.

## 3. x86recomp trial on `Storm.dll` (VERIFIED 2026-10-24)

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001` (built by `scripts/setup_tools.sh`,
LLVM 23.1.4, 16/16 library tests pass), Ghidra 12.2 headless (JDK 25).

- **Ghidra export:** 1,085 functions (92 multi-chunk, 19 thunks), 37 resolved jump tables (37
  unresolved: IAT thunks/tail jumps). Two runs give identical TSVs.
- **Lift:** 1,256 functions (1,089 from Ghidra/exports, 167 discovered via code/data pointers),
  82,199 instructions, 8 files. Output hash (sorted files) `ba8ebb1f…db6e4`, byte-identical
  across runs.
- **Gap found and fixed:** the first lift had 5 unimplemented sites, all in Storm's exported
  `SInterlocked*` helpers (`0x15021950`–`0x150219B8`): `lock xchg`, `lock cmpxchg`, and three
  `lock cmpxchg8b`. Cause: every `lock`-prefixed instruction went to `EmitLocked()`, which had no
  case for `xchg`/`cmpxchg`, and `cmpxchg8b` was not implemented. Patch 0001 routes them to
  seq_cst compare-and-swap helpers (`CasSeen`, `Cmpxchg8b` in `lifted.h`). Test:
  `tests/lift_atomic_test.cpp`, hand-computed from the Intel manual plus a two-thread 64-bit
  counter. Mutations (32-bit compare; non-atomic CAS) both fail it. Re-lift: 0 unimplemented, and
  the diff touches only those 5 sites.
- **arm64 compile:** all 8 generated files plus the function table compile with
  `recomp_add_lifted` (-O2, no errors or warnings, 3.9 s, 249 MB peak). The atomics become LSE
  instructions (`casal`/`swpal`).
- **Not yet run:** linking into a process and calling the lifted code needs a game project
  (`GameConfig`, `RunProcess`): M1/M2.

## 4. Differences from ReCarbon
- **No reference port** with a working toolchain (VERIFIED by the research: none exists).
- **x86-32 recompilation:** no `.pdata`; discovery uses `.reloc`, call targets, vtables and a
  Ghidra export (HYPOTHESIS, following x86recomp's design).
- **Bit-exact lockstep** with Windows 1.26a peers requires exact x87/SSE semantics (OBSERVED).
- **Legal:** the WC3 EULA bans reverse engineering (OBSERVED). Like ReCarbon, only tooling is
  published; the recompile is generated locally from the player's own copy.

## 5. DotA maps on 1.26a (VERIFIED 2026-10-24)

Static: `scripts/map_check.py <map> game/native-install` (MPQ/HM3W/w3i headers; pjass from
`tools/pjass` @ `654c3cf` against 1.26a's `Scripts\common.j` + `Scripts\Blizzard.j` from
`War3Patch.mpq`). Live: `scripts/wine_loadtest.sh` in the official 1.26a client (Wine oracle,
`-opengl -window -loadfile`), window captures in `game/loadtest/`.

| Map (SHA-256 prefix) | Script | pjass vs 1.26a | Official 1.26a client |
|---|---|---|---|
| `DotA v6.85oz LoD` (`b4577517…`, in-map name 6.85i) | JASS, 2,689,645 B, 6,108 functions | **0 errors** | **Loads, 3/3 launches**, no crash at 60 s: run 1 captured in a running match (DotA minimap, Sentinel UI, 4,375 gold, units), runs 2–3 at "Press any key to continue" (loading done) |
| `DotA imba v3.86b` (`7d5eb38f…`) | JASS, 3,958,252 B | 10 errors (6 int→real returns, 4 shadowed names) | **Loads** to "Press any key to continue": the game accepts what pjass rejects |
| `DotA v6.83se` (`10307817…`) | 365-B stub + iCCup native plugin | n/a (stub is not the game logic) | **Crash** at map load, 4 s: `EIP=0` (vtable call, return `0x6F45862F` in `game.dll`) |
| `DotA v6.83s` (`f3f1bd65…`) | 365-B stub + iCCup native plugin | n/a | **Crash**, identical registers and return address |
| `DotA v6.85.308` (`edfcc89b…`) | 365-B stub + native plugin (16.9 MB) | n/a | not run (same scheme) |

- **`DotA v6.83se` is an iCCup native-plugin build, not a JASS map.** Its MPQ (16 MiB sectors,
  1,378 entries, no listfile) has a root `war3map.j` of 365 bytes: an `ICCUP_MAP_SIGNATURE_V1:`
  line plus a stub `main` (`SetPlayers(10)`, `SetTeams(10)`); there is no `Scripts\war3map.j`.
  The game logic is an unnamed 13,211,136-byte entry: a 32-bit x86 DLL (`dota.dll`, PDB
  `…\Release\dota.pdb`, built 2025-08-13, imports only 87 KERNEL32 functions, exports
  `Initialize`), with hero tips and spell code. It must be loaded by iCCup's client, which
  presumably calls `Initialize` and lets it hook `game.dll`. Inspected statically only (copy in
  `game/mapcheck/quarantine/`, mode 0400); never executed.
- **Consequence:** stock 1.26a — and therefore a faithful recompile of it — cannot play 6.83se /
  6.83s / 6.85.308. Playing them would need iCCup's loader contract and recompiling each map's
  DLL too (a new native module per map version, outside the original game). Pure-JASS DotA builds
  need nothing beyond the game.
- **Crash detail (OBSERVED):** both plugin maps fault identically during map load: a virtual call
  through an object whose vtable entry is 0. Root cause UNRESOLVED (HYPOTHESIS: an object the
  iCCup loader normally registers or patches); not pursued, since it is outside stock behaviour.
- **Roadmap (decision 2026-10-24):** iCCup maps and online play are M8 (ROADMAP), after LAN and
  private multiplayer (M7) and only with iCCup's official cooperation and anti-cheat approval;
  nothing iCCup-specific is implemented or tested on the network before then.

## 6. Compatibility issues carried forward
- **CD-key step (RESOLVED in M3, §10, except `font.ccd`):** the native installer left the 5
  `font\font.*` files as shipped. The installer encodes the key (`cdkey26`, `cdkey1encode`) into them; per the project
  rule the port follows that practice, so the encoding must be reproduced from the installer and
  checked against the oracle made with the test key. Whether 1.26a needs these files for offline
  play is not yet tested.
- **Intro movies (VERIFIED; M3 seeds `seenintromovie`, §10):** on a fresh profile the client plays its intro through
  DirectShow (`blizzard.ax`) and does not check for failure: with no splitter filters it calls
  through a null graph (`game.dll` `0x6F52C3F8`, `QueryInterface(IID_IMediaPosition)`). Under Wine
  (no GStreamer) that crashes every launch; `HKCU\…\Warcraft III\Misc\seenintromovie=1` avoids it.
  The port's runtime must either provide a DirectShow graph that plays Blizzard's movies or seed
  `seenintromovie`.
- **Rendering under Wine (OBSERVED):** with `-opengl`, most terrain renders black while models
  and UI render: a Wine/macOS OpenGL issue, not a game or map one. The default D3D8 renderer was
  not tried after the movie fix.
- **pjass is stricter than the game (VERIFIED):** IMBA's 10 pjass errors don't stop 1.26a from
  loading it. pjass is a useful static screen, not a verdict.
- **Self-modifying or lock-free code in `game.dll`** relying on x86 ordering: UNRESOLVED (M1+).
- **1.21b Mac builds in the tomes (`MAC*/`)**: symbols not checked; low priority now that the
  Windows path is fully native.

## 7. M1: recompiling all modules (VERIFIED 2026-10-24)

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001`–`0005` (`scripts/setup_tools.sh`; the
series re-applies from a clean checkout to a tree identical to the one tested), LLVM 23.1.4,
Ghidra 12.2 (JDK 25). Inputs are the native install's binaries (identical to the oracle, §1).

**Modules** (one `recomp_lift` run, `scripts/lift.sh`, at their preferred bases, no overlaps):

| Module | Base | Ghidra functions / jump tables (resolved, unresolved) | Lifted functions | Lifted instructions |
|---|---|---|---|---|
| war3.exe | 00400000 | 2,706 / 39, 107 | 3,081 | 86,067 |
| game.dll | 6F000000 | 71,158 / 641, 2,709 | 84,321 | 2,283,363 |
| Storm.dll | 15000000 | 1,085 / 37, 37 | 1,256 | 82,200 |
| Mss32.dll | 21100000 | 1,070 / 55, 4 | 1,100 | 71,735 |
| Mp3dec.asi | 26F00000 | 170 / 35, 9 | 196 | 19,275 |
| Mssfast.m3d | 22600000 | 221 / 35, 36 | 276 | 11,917 |
| Msseax2.m3d | 22C00000 | 233 / 37, 22 | 286 | 13,085 |
| Mssdolby.m3d | 22700000 | 221 / 36, 36 | 276 | 12,350 |
| Reverb3.flt | 24600000 | 153 / 35, 10 | 182 | 10,592 |

Total: 90,974 functions (77,022 from Ghidra/exports/manifests, 13,952 discovered from pointers),
2,590,584 instructions, 220 files (318 MB). Jump tables: 950 from Ghidra, 8 recovered, 8 completed.

**Lifter defects found and fixed** (each with end-to-end, hand-computed tests in
`tests/test_lifter_patches.py` on synthetic PE images, no game data; every listed mutation of
the fix fails them):

| Patch | Defect (evidence) | Fix | Mutations caught |
|---|---|---|---|
| 0001 | `lock xchg/cmpxchg/cmpxchg8b` unimplemented (Storm `SInterlocked*`, §3) | seq_cst CAS helpers | 2 (`lift_atomic_test`) |
| 0002 | Pointer scans took ASCII and constants as code addresses: `game.dll` sits at 0x6F000000 ("o"), giving bogus weak entries and 382 unimplemented sites from text decoded as code | In images with base relocations only relocated dwords/immediates are candidates (exact); `data <va>` manifest directive for images without (fails if it names a real entry) | 1 |
| 0003 | MMX not implemented (119 sites in game.dll blitters, 8 in Miles' MMX mixer), nor `movhps`/`movntps`/`sfence`; x87 runs could span MMX instructions | `recomp::mmx` on the x87 physical registers (SDM vol. 1 §9.5: TOP=0, tags valid, sign/exp FFFF, EMMS empty); the forms seen only; runs end at MMX | 6 |
| 0004 | Only the section named `.text` was code: Miles' `MSSMIXER` (0x21139000, its mixer and CPU check) was never lifted; `pe_symbols.py` called exports outside `.text` data | `PeImage::CodeSpan` (all executable sections, contiguous) for lifter and runtime dispatch; `pe_symbols.py` by section flags | 2 |
| 0005 | Switch tables Ghidra exported with cases missing were used as-is (game.dll 6F30B3B5: `cmp edi,4` but 3 targets; Storm 1500BD83; 8 tables); tables with no bound check were not recovered (game.dll 6F68E6A0, entered by `jmp [6F68E6C8+ecx*4]`) | Recovery also runs on Ghidra's tables and adds missing cases; unbounded tables in relocatable images = the run of relocated slots pointing back into [entry, table) | 2 |

**Configuration** (committed, addresses only): `config/war3.manifest` (8 `data` entries: RTTI
names and string lists that look like pointers in war3.exe, which has no relocations; each with
where it occurs), `config/mss32.manifest` (1 `entry`: the MSSMIXER routine reached through a
pointer table inside that executable section), `config/unreachable.tsv` (below).

**Structural audit** (`scripts/validate_lift.py`, **HARD: PASS**, `game/generated/validate-summary.txt`):
- **Unimplemented sites: 0 reachable.** The 738 left (3DNow!: `pfmul` 283, `pfadd` 274, `pfsub`
  144, `pfsubr` 24, `femms` 8, `pf2id` 5) are in 4 Mp3dec.asi functions chosen only when
  `_AIL_MMX_available() & 2`; Mss32.dll 6.1d's `_AIL_MMX_available` returns only 0 or 1
  (CPUID.1:EDX bit 23), so they cannot run on any CPU (`config/unreachable.tsv`). They stay fatal.
- **Every Ghidra function and every exported function is lifted** in all nine modules.
- **Every relocated pointer into code is explained:** function entry, label inside a function,
  non-code data, the operand of an inline `jmp [table+reg*4]` (CRT memcpy in Mss32 and the
  providers), or a case target of a switch whose code nothing refers to (267 in game.dll).
- **Every Ghidra instruction not lifted is explained:** game.dll 1,564 (1,301 table data Ghidra
  decoded as code, 252 unreferenced code, 11 Ghidra decodes overlapping lifted instructions),
  war3.exe 110 (unreferenced). "Unreferenced" means: no lifted instruction branches into it, and
  no pointer to it exists outside code that is itself unreferenced (relocations, exact, in the
  DLLs; any 4-byte value in the image for war3.exe, which has none). Coverage of Ghidra's code
  bytes: 100% in seven modules, 99.927% game.dll, 99.877% war3.exe.

**Determinism:**
- **Lifter (VERIFIED):** two lifts from the same symbols are byte-identical; tree hash (sorted
  `*.cpp`) `8a2a898dd1219c9bb4d66028d61698be1123336d0441a43af4eaaf1424dde288`.
- **Ghidra (VERIFIED: not deterministic on game.dll):** a second analysis of game.dll defined 2
  more functions (6F4B4110, 6F4B4130: small float-compare tail-jump functions, decoded in both
  runs but unreferenced) and labelled 4 `jmp`s as call terminators; jump tables, instruction
  addresses/lengths and non-code ranges were identical. With those symbols 6 generated files
  differ (tree hash `e90c0681…56ef8`). Two single-threaded runs (`-max-cpu 1`, 410 s each) differ
  the same way (71,161 vs 71,159 functions). Storm.dll's two runs were identical (§3).
- **Fix (VERIFIED, decided by the user):** each module's `functions.tsv` and `jumptables.tsv` are
  pinned in `config/symbols/<module>/` (4.2 MB: addresses, flags and Ghidra's auto names such as
  `FUN_`, `Unwind@`, `thunk_FUN_`, runtime-library matches; no game bytes), as ReCarbon commits its
  function and jump-table addresses. `scripts/lift.sh` builds its input from them plus
  `pe_symbols.py` output from the player's binaries; Ghidra is development-only (the audit's
  instruction listing, and deliberate refreshes of the pinned lists). Two lifts from the pinned
  lists, and one with no Ghidra output on disk at all, give tree hash `8a2a898d…de288`; the audit
  passes on them.

**arm64 compile:** all 220 files with x86recomp's `recomp_add_lifted` flags (-O2, -fnon-call-exceptions,
strict x87 FP), Homebrew LLVM 23.1.4, Ninja: 0 errors, 0 warnings; 238 s wall, 1,569 s CPU, peak
RSS 845 MB; 128 MB of arm64 Mach-O objects defining exactly the 90,974 lifted functions. Not linked
(no game project yet: M2).

**Verify:**
```sh
scripts/setup_tools.sh
ctest --test-dir tools/x86recomp/out/build/debug
/opt/homebrew/bin/python3 -I tests/test_lifter_patches.py
scripts/lift.sh                      # game/generated/war3 from game/native-install
/opt/homebrew/bin/python3 -I scripts/validate_lift.py --generated game/generated/war3 \
  --unreachable config/unreachable.tsv --module game/native-install/war3.exe game/symbols-lift/war3 ...
```
(`lift.sh` builds `game/symbols-lift/` from `config/symbols/`; the development-only Ghidra commands are in AGENTS.md).

**Remaining risks (as of M1; M2 status in §9):**
- **Static imports between lifted modules:** x86recomp binds every static import to an HLE
  thunk. war3.exe/game.dll import Storm (by ordinal) and Mss32 statically; the runtime must bind
  them to the lifted DLLs' exports and run their DllMains in load order. **Resolved in M2 (§9).**
- **Indirect jumps:** game.dll has 2,535 `jmp reg` sites (and calls through pointers) dispatched
  at run time; their targets are not checked statically. A target that is not a lifted entry is
  a fatal stop naming the address (fix: manifest entries, as for MSSMIXER).
- **Non-code bytes:** 730 KB of game.dll's `.text` is neither code nor relocated data nor
  padding (mostly constants and strings Ghidra left undefined). Not reached by any lifted branch
  or relocation; reaching one at run time would be the fatal stop above.
- **Memory ordering:** lock-free hand-offs without locked instructions in game.dll's threads are
  not audited (x86recomp's open item).
- **x86recomp `pacing` test** fails intermittently on this Mac (pristine `ad1b16b` 2/20, patched
  4/20 runs; the test is built from `pacing.cpp` and `platform.cpp`, which no patch touches).

## 8. Miles: recompile Mss32.dll 6.1d rather than extend the HLE (decision 2026-10-24)

| | Recompile Mss32.dll + providers | Extend x86recomp's Miles HLE |
|---|---|---|
| Coverage of WC3's 110 Miles imports | All (the real code) | 62 implemented; 48 missing: XMIDI/sequence and DLS (13+), `AIL_decompress_ASI` (MP3 music via Mp3dec.asi), ADPCM, 3D cone/occlusion/obstruction/velocity/speaker type, stream/sample pan and user data |
| Fidelity | Exact 6.1d behaviour | HLE models Miles 6.5e/6.1c; 6.1d differences would need study |
| Lift state | 0 reachable unimplemented, audit PASS (§7); integer/x87/MMX only | n/a |
| New HLE needed | `dsound.dll!DirectSoundCreate` (Miles asks by name; only `DirectSoundCreate8` exists); IDirectSound v1 compatibility of the existing DirectSound 8 HLE | 48 functions |
| Runtime work | Static-import binding to lifted DLLs (needed for Storm anyway) | none beyond the functions |

**Decision:** recompile. Audio is outside the lockstep simulation, so exactness is not a sync
requirement, but recompiling covers every call the game makes with the original behaviour, for
the price of one HLE entry and the import binding Storm already needs. Revisit if the DirectSound
HLE's gaps (no notifications) block Miles at M3/M5. x86recomp's `recomp_mss32` is not linked.

## 9. M2: native link and process start (VERIFIED 2026-10-24)

**Corrections found in M3 (§10):** (1) "DllMains run … as on Windows" missed one part of the
contract: Windows passes DllMain a non-NULL `lpReserved` for the EXE's static imports and NULL for
LoadLibrary; the M2 loader passed NULL always, and Storm.dll, attached with NULL, seeds its MPQ
crypt table so that no file opens. Fixed in patch 0009. (2) `import_coverage.py` counted handlers
of HLE modules `refrozen` does not link: game.dll's 48 opengl32 imports were reported as handled
but were strict stubs; at the M2 tree the true totals were 922 handled, 412 stubs. (3)
`TryEnterCriticalSection` was among the "accepted" GetProcAddress NULLs, but game.dll calls the
pointer without checking it (6F6EB550); it exists on every NT system and is now implemented.

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001`–`0008` (a fresh clone at `ad1b16b` with
the series applied by `git apply` is identical to the tree tested), LLVM 23.1.4, CMake + Ninja.

**The game project** (`CMakeLists.txt`, `src/main.cpp`): one executable, `refrozen`, made of the
lifted code (`recomp_add_lifted`) and x86recomp's runtime. `GameConfig`: guest install
`C:\Program Files\Warcraft III`, `war3.exe` as the process image, the installers' registry values
(InstallPath, GamePath, Program; FEASIBILITY §1), and the lifted DLLs in dependency order:
msvcr80.dll, Storm.dll, Mss32.dll, game.dll, the five Miles providers. The install directory is
`--game <dir>`, else `REFROZEN_GAME_DIR`, else `game/native-install`. Debug build: 4 min 40 s from
clean (3 min 45 s after a re-lift), 109 MB executable, **0 undefined symbols**.

**msvcr80.dll is lifted** (the 10th module, 2,397 functions, 138,949 instructions; SHA-1
`9fd3a7f0…b564`, shipped in the 1.26a install). war3.exe, game.dll and Storm.dll import 189 CRT
functions and data from it; recompiling it gives the original CRT (heap, stdio, locale, startup)
instead of HLE for each. Its 6 port-I/O exports (`_inp`…`_outpd`, `in`/`out`) are in
`config/unreachable.tsv`: imported by no module, called from nowhere, privileged on NT.

**Loader (patch 0007).** x86recomp bound every static import to an HLE thunk and ran no DllMain
for static imports. Now, as on Windows:
- **Binding:** imports from a lifted module bind to its export by name or `#ordinal` (ordinal
  base applied); a missing export, or an import of a lifted module listed after its importer in
  `lifted_dlls`, is a fatal error at load, never an HLE thunk. All modules are registered before
  any is mapped, so that check sees every lifted module (the first version did not: an importer
  listed early silently got HLE stubs; found by the loader test).
- **Initialization order:** before the EXE entry, the EXE's static imports are loaded
  dependencies-first (`LoadLifted`: imports, then DllMain(PROCESS_ATTACH)); a failing DllMain is
  fatal. LoadLibrary uses the same path; FreeLibrary releases dependencies after DllMain(DETACH).
  Static loads are pinned (never unloaded), as Windows does for load-time imports.
- **Addresses:** every module at the base it was lifted at (its preferred base, §7 table + msvcr80
  at 78130000); the lifter's dispatch tables and the generated code assume exactly these.
- **Indirect branch validation:** every indirect `call`/`jmp` goes through `Dispatch`, which
  checks the target against the lifted entries of the module it is in. A target outside all
  lifted code, or inside code but not a function entry, stops the process naming both addresses
  as `module+offset`, the lifted function the target lies in, and the manifest line that would
  add it (`entry <va>`), with the guest registers and stack.
- `<ID>_TRACE=1` (documented upstream but never wired) now enables the HLE call trace.

**Strict imports.** A Win32 import with no HLE handler is bound to a thunk that stops the process
with `unimplemented import <dll>!<name> called (return address …)`; it never returns a value.
`GetProcAddress` of an unimplemented function returns NULL with ERROR_PROC_NOT_FOUND and a
warning (what Windows does for a missing export; the CRT and Miles check for it).
`scripts/import_coverage.py` classifies every import of the ten modules from their PE import
tables (VERIFIED, exit 0):

| Importer | lifted | HLE | strict stub |
|---|---|---|---|
| war3.exe | 213 | 179 | 102 |
| msvcr80.dll | 0 | 113 | 48 |
| Storm.dll | 57 | 150 | 52 |
| Mss32.dll | 0 | 90 | 42 |
| game.dll | 307 | 246 | 115 |
| 5 Miles providers | 98 | 197 | 0 |
| **total** | **675** | **975** | **359** |

All 675 cross-module imports resolve to a lifted function entry (670) or a data export (5:
`_adjust_fdiv`, `_acmdln`, `_HUGE`); 163 are Storm ordinals (game.dll, war3.exe), 318 are
Mss32/Miles functions (war3.exe, game.dll, the providers).

**HLE functions added (patch 0008)**, each the first fatal stop of a launch, each implemented to
its documented Win32 behaviour and tested (`tests/test_loader.py`, mode H):

| Launch | Stop | Caller | Implementation |
|---|---|---|---|
| a01 | `GetCommandLineW` | msvcr80 startup (7813AC0A) | the process's wide command line |
| a02 | `InterlockedCompareExchange` | Storm DllMain (150388C0) | seq_cst CAS, returns the initial value |
| a03 | `GetWindowsDirectoryA` | Mss32 DllMain (21101DCA) | `C:\WINDOWS`; the size it needs if the buffer is short |
| a04 | `SetCurrentDirectoryA` | war3.exe 00401101 | guest path checked on the host; ERROR_DIRECTORY for a file, errno-mapped errors |
| a05 | `DisableThreadLibraryCalls` | game.dll CRT DllMain (6F7E1F6E) | TRUE for a loaded lifted DLL (thread notifications are never sent); ERROR_MOD_NOT_FOUND otherwise |

One SSE2 gap (patch 0006: `cvtss2sd`/`cvtsd2ss`/`cvtps2pd`/`cvtpd2ps`, `sqrtss`, `minsd`, `rcpss`,
`movmskpd`, `psrad xmm,imm`, `paddd`/`paddw`) came with msvcr80's and game.dll's code; 16
hand-computed checks in `tests/test_lifter_patches.py` (SDM values; 4 mutations caught).

**Runtime evidence** (`scripts/run_attempt.sh`, logs in `game/attempts/`, user paths removed):
- `m2-final-1`, `m2-final-2` (final tree, two launches): both log
  `probe: GameMain (6F009850) ecx 6F000000 args 6F000000 …` and then stop at the next missing
  import (below). Their output is identical up to the host backtrace (ASLR addresses, crash-report
  timestamp); so were a06/a07.
- Traced launch (`REFROZEN_TRACE=1`, a08): `msvcr80.dll: DllMain(1)`, `storm.dll: DllMain(1)`,
  `mss32.dll: DllMain(1)` (static imports, dependencies first), then war3.exe's code:
  `LoadLibraryA("blizzard.ax")` → NULL (not provided: the DirectShow intro-movie filter, §6),
  `LoadLibraryA("game.dll")` → `game.dll: DllMain(1)` (inside it,
  `DisableThreadLibraryCalls(6F000000)` → 1) → 6F000000, `GetProcAddress(6F000000, "GameMain")`
  → 6F009850, and the call with game.dll's HMODULE as its argument (`probe` line). The Miles
  providers are mapped but not loaded before GameMain (Mss32 loads them in `AIL_startup`).
- First stop after GameMain: `unimplemented import kernel32.dll!GetDiskFreeSpaceA called (return
  address 15017A35)`, in Storm (15017990, called from 1501D3B0) under GameMain → 6F009720 →
  6F0010E0. This is M3 work and is left as a strict stub.

**DirectSoundCreate (not reached in M2).** Mss32 asks for it at run time:
`LoadLibraryA("DSOUND.DLL")` + `GetProcAddress(…, "DirectSoundCreate")` (no static import). The
DirectSound HLE module exists (`DirectSoundCreate8`, ordinal 11), so LoadLibrary succeeds, and
`GetProcAddress` for `DirectSoundCreate` returns NULL with ERROR_PROC_NOT_FOUND (by inspection of
`hle.cpp` `ProcAddress`): an explicit failure that Mss32 reports as "DirectSoundCreate() …
failed", never a fake device. Implementing it (IDirectSound v1 on the DirectSound 8 HLE, §8) is
needed when Miles opens its digital driver (M3/M5).

**Tests** (no game data):
- `tests/test_loader.py`: a synthetic t.exe + a.dll + b.dll + c.dll (llvm-mc), lifted together,
  linked with the runtime and run: ordinal and name binding, DllMain order dependencies-first
  (the EXE lists b.dll before a.dll), LoadLibrary/FreeLibrary of a dynamic DLL, pinned static
  loads, the strict-stub stop, both indirect-branch diagnostics, importer-before-import refused,
  and the five 0008 functions (14 results, incl. last-error values): 13 checks, all pass. Each of
  10 mutations fails it: ordinal binding by name, DllMain before dependencies, static loads not
  pinned, a missing handler returning 0, no static-import initialization, modules mapped while
  registered, the old dispatch message, and for 0008 the CAS return value, the directory check
  and the handle check.
- Unchanged and passing: `ctest` 16/16 (the `pacing` flake passed this run),
  `tests/test_lifter_patches.py`, `tests/test_bnupdate_patch.py`.

**Lift:** 93,371 functions, 2,729,533 instructions, 232 files; two lifts byte-identical, tree
hash `5da168f875554a767a91fc081943d29b7fbf45bfff3de85090e1642c36779f85` (changed from M1's
`8a2a898d…` by msvcr80, the GameMain probe and the SSE2 forms). `validate_lift.py` HARD PASS on
all ten modules; 744 unimplemented sites, all in the 10 functions of `config/unreachable.tsv`.

**Verify:**
```sh
scripts/setup_tools.sh
/opt/homebrew/bin/python3 -I tests/test_loader.py
scripts/lift.sh
cmake -S . -B build/main -G Ninja -DCMAKE_BUILD_TYPE=Debug -DRECOMP_LLVM_ROOT=/opt/homebrew/opt/llvm
ninja -C build/main refrozen
/opt/homebrew/bin/python3 -I scripts/import_coverage.py --tsv game/reports/import_coverage.tsv
scripts/run_attempt.sh m2 60          # exit 0 iff "probe: GameMain" was logged
REFROZEN_TRACE=1 scripts/run_attempt.sh m2-trace 120
```

**Remaining risks (for M3+):**
- **Strict stubs:** 359 imports have no handler (102 in war3.exe, 115 in game.dll, 52 in Storm,
  48 in msvcr80, 42 in Mss32); M3 will meet some of them, starting with `GetDiskFreeSpaceA`.
  Many are unreachable for this game (console, `*W` file APIs used only by the CRT's wide paths).
- **GetProcAddress NULLs** accepted for now: `FlsAlloc`/`FlsGetValue`/`FlsSetValue`/`FlsFree`,
  `EncodePointer`/`DecodePointer`, `FindActCtxSectionStringW`, `TryEnterCriticalSection`,
  `advapi32!AllocateAndInitializeSid`. These are the XP RTM answers; the MSVC 8 CRT falls back.
  Their callers' fallbacks are exercised, not audited.
- **Thread notifications:** DLL_THREAD_ATTACH/DETACH are never sent (x86recomp design). Fine for
  the CRT DllMains seen (game.dll disables them); a DLL relying on them would misbehave quietly.
- **Indirect jumps** are validated only when taken; unseen targets are found at run time (with
  the diagnostic above).
- `DirectSoundCreate`, CD-key data, DirectShow movies (§6, §8) and memory ordering (§7) are open.

## 10. M3: runtime initialization to the main menu loop (VERIFIED 2026-10-24)

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001`–`0010` (a fresh clone with the series
applied is identical to the tree tested). Install: `scripts/native_install.py` with the test keys
of the player's readme (development only; nothing key-derived is stored in the repository).

**Acceptance (`scripts/m3_accept.sh 3 60`, final tree):** 3 consecutive launches, each 60 s:
no FATAL, no watchdog report (the runtime reports any 5 s without a presented frame), still
running at the deadline, frames saved from each. The saved frames show the Frozen Throne main
menu (3D background animated, all buttons, version 1.26.0.6401) with the game's own dialog
"Unable to initialize base sound services, sound is disabled" (no wave device, below). A
foreground launch without the focus hook (the player's path) presented frames for 60 s, no
fatal. Earlier full runs (before the last fixes) presented 4,200–5,400 frames per minute; the
final runs 1,200–3,000 on a host at load average 13–24; frame rate is not an M3 criterion.

**Root causes on the way (each from a stop or a hang, each fixed and tested):**

| Stop / symptom | Cause | Fix |
|---|---|---|
| `GetDiskFreeSpaceA` (Storm) | not implemented | NT semantics, statvfs of the per-user volume (Wine's tests for the root forms) |
| `ImmAssociateContextEx` | imm32 not implemented | the IMM-disabled system (en-US XP), ReactOS's results for all 9 imported functions |
| "Warcraft III was unable to initialize" | game.dll's product check (6F009950) decodes the installed CD-key files `font\font.gid`/`.exp`; the native install left the shipped placeholders | the installer's key step reproduced (below) |
| …still: no MPQ file opens | Storm's crypt table seeded with 0x10000100 by its DllMain when `lpReserved` is NULL (a dynamic load); the loader passed NULL for static imports | static imports get a zeroed CONTEXT on the initial thread's stack as `lpReserved` (MSDN contract) |
| "unable to initialize DirectX" | no `d3d8.dll` (Direct3D 8 is M4) | the game's own `Gfx OpenGL` setting (REG_DWORD 1) and x86recomp's existing `recomp_opengl`, linked |
| `EnumDisplayDevicesA`, `ChangeDisplaySettingsExA`, `glTexGeni`, `wglSwapLayerBuffers`, `GetSystemDefaultLangID`, `OpenEventA`, `GetProfileStringA`, `waveOutOpen`, `CreateIoCompletionPort` | not implemented | each to its documented behaviour (patch 0009); forms not needed stop explicitly |
| `ijl15.dll!#2` | the Intel JPEG Library (JPEG BLP textures) is a shipped x86 DLL | lifted as the 11th module; ~40 MMX/SSE2 forms and the `movhps` store (patch 0010) |
| indirect branch 6002E0B2 → 6002E1F4 | `mov eax,[t+4*i]; jmp eax` with the table in `.data` (Intel's compiler), not recovered | recovery of the load-then-jump form; tables outside `.text` need every slot relocated |
| undecodable 6002D1C1 | Ghidra listed index −1 of a computed jump (an impossible case inside a `lea`) | `config/jumptable_corrections.tsv` with the derivation |
| 2 code pointers unexplained (validator) | relocated slots in `.data1` and unaligned ones were never scanned | every relocated slot outside executable sections is scanned (images with relocations) |
| running, but no frame ever | Windows sends `WM_SIZE`/`WM_MOVE` after `WM_CREATE` (popups) and on maximize; the runtime never did, so the GL device never learnt its size | the creation/maximize/first-show sequences of Wine's message tests |

**CD keys, as the installer stores them.** The cipher of the `font\font.*` files was recovered
from game.dll's reader (6F553AA0 → 6F555630, `scripts/font_keydata.py`): a SHA-1 compression with
SHA-0's message schedule, rotations built from arithmetic shifts and little-endian words
(Battle.net's "broken SHA-1"), IDEA (PGP's reference implementation on little-endian words: it
passes IDEA's published test vector), and keys from the CRT's `rand()` after fixed seeds. The
installer's `<encrypt object="cdkey26">` writes the key (26 characters, upper case, no dashes, NUL)
into `font.gid` (war3.mpq) / `font.exp` (War3x.mpq), `<encrypt object="user">` the owner's name
(NUL) into `font.clh`, zero-padded to one 64-byte block. The encoder reproduces the official
installer's three files byte for byte from the same keys and name. `native_install.py` asks for the
keys like the installer (stdin when not a terminal) and stores them nowhere else; `--verify`
against the Wine oracle: **PASS**, every loose file and MPQ entry identical except the two
`font.ccd` files (`cdkey1encode`, not reproduced: game.dll's decoder rejects both the shipped and
the official one, so the game behaves the same). The installer's own key checksum is not
reproduced; the game validates the keys when it starts (the check above), unchanged. While testing
the decoder, the strings in the *shipped placeholder* files (Blizzard's, from the install media)
were printed once into the development session; no key of the player's was ever printed or
written outside the MPQs.

**Settings seeded** (first run only: the registry file does not exist yet; a profile from M2
lacks them): `HKCU\…\Warcraft III\Gfx OpenGL` = 1 and `…\Misc\seenintromovie` = 1, both REG_DWORD
as game.dll's settings table declares them (type 4); `GameConfig::registry_dwords` is new in 0009.

**Decisions:**
- **Renderer:** the game's OpenGL path on x86recomp's existing GL HLE; Direct3D 8 stays M4. The GL
  context does not model texture-coordinate generation: `glTexGeni` now keeps its state with
  GL 1.1's errors, but enabling `TEXTURE_GEN_S/T` is still reported as unsupported (INVALID_ENUM
  and a warning, upstream's model for GL gaps), an M4 risk.
- **Sound:** a system without a wave output device (`waveOutOpen`: MMSYSERR_NODRIVER for the
  mapper, BADDEVICEID otherwise), the codes Windows gives such a machine; Miles runs silent and the
  game shows its dialog. Audio output is M5.
- **Background runs** never get host focus: `REFROZEN_TEST_FOCUS=follow` activates the game's window
  guest-side (test hook; players get real focus events).

**CRT and game fallback paths (investigated statically):** msvcr80's `_encode_pointer` /
`_decode_pointer` return the pointer unchanged when `EncodePointer` is missing (the XP-before-SP2
path, consistent both ways); with any `Fls*` function missing it switches to TLS (`TlsGetValue`,
`TlsSetValue`, `TlsFree`, and a `TlsAlloc` wrapper that ignores the FLS callback), so per-thread CRT
data is freed only on DLL_THREAD_DETACH, which the runtime never sends (a small leak per exiting
CRT thread). game.dll falls back from `GetSystemDefaultUILanguage` to `GetSystemDefaultLangID`
(observed) and skips its privilege check when `AllocateAndInitializeSid` is missing (6F00BB00).

**Thread synchronization:** named events/mutexes now fail on another type's name as Windows does
(ERROR_INVALID_HANDLE); I/O completion ports queue posted packets FIFO and wake blocked
`GetQueuedCompletionStatus` threads (the game creates a port and 16 workers for networking; no
packet is posted before the menu); `TryEnterCriticalSection` uses XP's algorithm on the guest
`CRITICAL_SECTION`. The completion port's concurrency limit (a scheduling hint) is not modelled.

**Lift:** 11 modules, 94,489 functions, 2,823,428 instructions, 241 files; two lifts byte-identical,
tree hash `e9333df8d9039d68b91c720b7275b66f3a8d1a073a10ea38aa05cdc52795b7e7`; `validate_lift.py`
HARD PASS on all eleven; 744 unimplemented sites, all in the documented-unreachable functions.
Imports (`import_coverage.py`, linked HLE modules only): 678 cross-module (all resolve), 1,063
handled, 327 strict stubs.

**Tests and mutation gate** (`reference/TEST_COVERAGE.md`): 249 checks in the project's tests
(lifter 108, loader 18, Win32 95, key files 23, jump-table corrections 5), all passing; ctest 16/16;
87 mutants over M2 and M3, 86 KILLED, 1 documented EQUIVALENT, 0 survivors; the 53 packed-integer
expectations agree 53/53 with x86-64 under Rosetta 2.

**Verify:**
```sh
scripts/setup_tools.sh
/opt/homebrew/bin/python3 -I scripts/native_install.py ... --owner "<name>" --verify game/wine-oracle
scripts/lift.sh && cmake -S . -B build/main && ninja -C build/main refrozen
for t in test_lifter_patches test_loader test_win32 test_font_keydata test_jumptable_corrections; do
  /opt/homebrew/bin/python3 -I tests/$t.py; done
/opt/homebrew/bin/python3 -I tests/mutate.py
scripts/m3_accept.sh 3 60
```

**Remaining risks (for M4+):**
- 327 strict stubs remain; upstream fake-success no-ops met on the way and not changed:
  `InvalidateRect`, `UpdateWindow`, `FillRect`, `DrawTextA` (return success, do nothing).
- Rendering correctness is not checked (M4): texture-coordinate generation, the GL HLE's gaps,
  Direct3D 8; input (mouse/keyboard into the menu) not exercised; the sound dialog must be
  dismissed by the player.
- Accepted GetProcAddress NULLs left: `Fls*`, `Encode/DecodePointer`, `FindActCtxSectionStringW`,
  `GetSystemDefaultUILanguage`, `AllocateAndInitializeSid` (fallbacks above); no
  DLL_THREAD_ATTACH/DETACH.
- `font.ccd` not reproduced; the installer's key checksum not reproduced (the game checks keys).
- Memory ordering in game.dll's threads (16 network workers now exist) is not audited.

## 11. M4: interactive menus and rendering correctness (VERIFIED 2026-10-25)

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001`–`0012` (0011: the lifter's PUSH/POP
slot size; 0012: the M4 runtime). Renderer: the game's OpenGL path on x86recomp's GL HLE
(Direct3D 8 not needed: the OpenGL path renders every menu screen; deferred).

**Acceptance (`scripts/m4_accept.sh 3 110`, `tests/m4/native_path.txt`):** 3 consecutive
launches, each from a fresh per-user tree (new profile) on an APFS clone of the native install
with the DotA map added. Each walks, with scripted mouse and keyboard: dismiss the sound dialog
(Return), Single Player (S), type a profile name and create it (Return), Custom Game (G), the
next map (Down), the Download folder (mouse double-click), DotA v6.85oz LoD (click; preview,
10 players, Sentinel/Scourge slots), Cancel twice (A), Options (O), Video (V), Cancel; then the
window loses and regains focus, is minimized and restored; then Quit (Q). Pass = all 14 named
shots saved, no FATAL, no watchdog report, and the process ends by itself from the Quit button
with status 0. **Result: 3/3 PASS.** Battle.net and Local Area Network are never opened
(network-facing, M7); Start Game is never pressed (loading a map is gameplay, M5).

**Oracle comparison (`scripts/oracle_menus.sh`, `scripts/oracle_keys.c`, `scripts/m4_compare.sh`):**
the official 1.26a client under Wine (development only), on fresh APFS clones of the oracle
install and prefix, walks the same path by keys at the same times (`tests/m4/oracle_path.txt`)
on both of its renderers: its default Direct3D 8 (wined3d) and `-opengl`. The window is resized
to an 800x600 client first: a `-window` window is `CW_USEDEFAULT`-sized (3/4 of the host screen),
whose aspect changes the 3D projection, and Wine's Mac driver has no virtual desktop. Keys are
posted to the game window by a freestanding i686 helper (clang + llvm-dlltool + lld-link), so the
host pointer is never moved. A difference counts as a port defect only where the two oracle
renderers agree with each other and native does not. SSIM of native against the D3D8 oracle on
the static screens is 0.75–0.83 (the 3D background animates); the two oracles agree less with each
other (0.48–0.72: Wine's GL path draws no text and garbles chains). UI chrome, text, layout,
minimap previews and map details match the D3D8 oracle on every screen.

**Defects found and fixed (each with a deterministic test and mutants):**

| Symptom | Root cause | Fix |
|---|---|---|
| No fog over the menu's 3D scene (both oracles show a lavender haze) | the device's vertex fog uses view-space z (D3D: positive forward); the GL context passes GL eye space (forward is −z), so the distance was negative and the linear factor clamped to 1 | range fog: the eye distance, GL 1.5 §3.10's fog coordinate (`gl_fog_test`) |
| Fault at Quit in Miles (`RIB_unregister_interface` called with 0x78 for three arguments) | **lifter**: `push ds/es` (32-bit operand size) lifted as a 2-byte push while `pop` takes 4, so ESP drifted 2 bytes per segment push; Miles' `MIXER_shutdown` (`push ebx/esi/edi/ds/es … pop`) returned with EBX = its return address and EDI = 0x78. Also `push imm16` and `pop r16` (66h) took 4 bytes. Sites: game.dll 1,233 segment pushes, Mss32 334, war3.exe 147, Storm 87, Mp3dec 99, msvcr80 24 | the slot is the instruction's operand size; a segment push writes its 16-bit selector into a 4-byte slot (SDM vol. 2, PUSH) — patch 0011, `test_stack_forms` (12 SDM cases; the old lifter fails 9) |
| …then an indirect branch to 35800000 at exit | game.dll's own exit-time destructors (registered in its CRT order) call through a base-class vtable's float constant; under Wine (and Windows) that access violation happens too, but the loader catches exceptions escaping a DLL entry point (Wine's `MODULE_InitDLL`: `__TRY … __EXCEPT_ALL`), so FreeLibrary returns and the process exits; the runtime stopped on the branch instead | a call to unmapped memory raises EXCEPTION_ACCESS_VIOLATION (execute) through the guest SEH chain; DLL entry points run inside a loader frame that unwinds the inner frames and catches (detach: FreeLibrary still succeeds; attach: a strict stop, the failed-load status is not modelled) |
| Thin alpha-keyed geometry (the throne's long chains) missing | not a port defect: macOS's GL driver, under both oracle renderers, filters anisotropically by default; forcing 16x anisotropy natively reproduces the oracle exactly; the game requests none, so GL semantics (and a Windows driver without forced anisotropy) give native's result | none (documented oracle artifact) |
| 16-bit textures stored at 8 bits per channel | the game asks for `GL_RGBA4` / `GL_RGB5_A1` (Texture Quality Medium); the context kept full precision | texels kept at the requested precision (GL's fixed-point conversion), as period drivers and both oracles store them (`gl_texture_test`) |

**Win32 behaviour made real (no fake successes):**
- Painting: per-window update region (bounding box), `InvalidateRect` (bad hwnd: FALSE,
  ERROR_INVALID_WINDOW_HANDLE), WM_PAINT synthesised after posted messages and input, before
  WM_TIMER (Wine's `get_message` order) and kept until validated, `UpdateWindow` (synchronous),
  `BeginPaint` (validates, sends WM_ERASEBKGND when due, `fErase`, `rcPaint`), `DefWindowProc`
  WM_PAINT (validates) and WM_ERASEBKGND (0 without a class brush). Invalidation by creation
  with WS_VISIBLE, show, restore and resize (CS_HREDRAW/CS_VREDRAW: whole; else the exposed
  strips). The game's main window procedure answers WM_PAINT with BeginPaint/EndPaint only.
- GDI drawing (`FillRect`, `DrawTextA`, `DefWindowProc` erasing with a class brush) and
  `InvalidateRect(NULL)` are strict stops (DrawTextA's diagnostic prints the text). Static
  audit of their callers: game.dll's movie backdrop ("BlockingWindow", black fill behind
  DirectShow cinematics such as TutorialIn) and movie window, Storm's dialogs and war3.exe's
  launcher window; none is reached on the menu paths (user32/gdi32 traces, default and `-window`).
- Minimize/restore: `ShowWindow(SW_MINIMIZE)` sends WM_SIZE(SIZE_MINIMIZED, 0×0) and loses the
  activation (WM_ACTIVATE(WA_INACTIVE, minimized), WM_ACTIVATEAPP(FALSE), WM_KILLFOCUS);
  `SW_RESTORE` reactivates and sends WM_SIZE with the client size; `DefWindowProc` carries out
  SC_MINIMIZE/SC_MAXIMIZE/SC_RESTORE; the host minimizing/restoring the window posts those system
  commands (the game may handle them itself, as on Windows); a resizable (WS_THICKFRAME) window
  resized by the host gets its new client size and WM_SIZE. The game's default window is a
  maximized popup at the display mode's size: resolution changes go through Options/Video.
- Test hooks (`<ID>_TEST_INPUT`): `shot <name>` (time-scripted named frames, independent of host
  load), `dblclick`, `minimize`, `restore`, `resize w h`, `focus out|in`.

**Findings for later milestones:**
- **Start Game initialises networking** even for a local custom game: the first stop is
  `wsock32.dll!#9` (htons). M5 must implement the winsock calls a local game makes.
- The client under Wine with no audio driver faults at startup (an undispatchable exception), so
  the "no sound device" model cannot be checked against that oracle; native shows the game's own
  dialog and continues.
- `import_coverage.py` counted wsock32's ordinal handlers ("#N") as stubs; corrected counts
  (unchanged code, M3 and M4): 678 cross-module, 1,075 handled, 315 strict stubs (M3 stated
  1,063 / 327).

**Tests and mutation gate** (`reference/TEST_COVERAGE.md`): 361 checks (lifter 122, loader 23,
Win32 151, GL context 37, key files 23, jump-table corrections 5), all passing; ctest 18/18 (`pacing`
passes 3/3 on a quiet host and failed once under load, a frame 98 ms late; timing only); 120 mutants over M2–M4:
119 KILLED, 1 documented EQUIVALENT (M3-F9), 0 survivors (M4-D7 survived its first run and led to a
stronger check; M4-L4 was first killed by the wrong check).

**Lift:** 11 modules, 94,489 functions, 2,823,428 instructions, 241 files; two lifts byte-identical,
tree hash `416c05148900f50b4a3d2eb79f62bd2908ba3cd0181ad2e644d0347525d7688d` (changed from M3's by
the PUSH/POP fix); `validate_lift.py` HARD PASS on all eleven; 744 unimplemented sites, all in the
documented-unreachable functions.

**Verify:**
```sh
scripts/setup_tools.sh && scripts/lift.sh && ninja -C build/main refrozen
for t in test_lifter_patches test_loader test_win32 test_gl_context test_font_keydata \
         test_jumptable_corrections; do /opt/homebrew/bin/python3 -I tests/$t.py; done
/opt/homebrew/bin/python3 -I tests/mutate.py
scripts/m4_accept.sh 3 110
scripts/oracle_menus.sh d3d-1 d3d tests/m4/oracle_path.txt 100     # development oracle
scripts/oracle_menus.sh gl-1 opengl tests/m4/oracle_path.txt 100
scripts/m4_compare.sh game/attempts/m4-accept-1-*/shots game/attempts/oracle-d3d-1 \
    game/attempts/oracle-gl-1 game/attempts/m4-compare
```

**Remaining risks (for M5+):**
- A foreground ice spike in the menu scene is lit pale natively and dark in both oracles; not
  fog, culling, mip selection or anisotropy (bisected); lighting-related, unexplained. DotA's
  lit models may show the same.
- The native renderer is isotropic where macOS GL is anisotropic: thin alpha-tested geometry
  (chains, foliage) minifies away sooner than in the oracle (faithful to GL; worth a user option
  later, never a silent default).
- Direct3D 8 absent (not needed so far); texture-coordinate generation still unmodelled.
- The minimized window keeps its rect (Windows parks it at −32000,−32000); WM_SIZE from host
  resizing is queued rather than sent from a sizing loop; WM_NCPAINT/WM_QUERYOPEN not sent.
- 315 strict stubs; winsock for local games (above); `pacing` (ctest) fails under host load.

## 12. M5: playable local match, offline (VERIFIED 2026-10-25)

Toolchain: x86recomp `ad1b16b` + `patches/x86recomp/0001`–`0013` (0013: the M5 runtime: wave
output, overlapped file I/O, wsock32's local-game functions, window sizing, fullscreen/HiDPI).
Map: DotA v6.85oz LoD (the offline target), from the install's `Maps\Download`.

**Acceptance (`scripts/m5_accept.sh 3 240`, `tests/m5/match_path.txt`):** 3 consecutive launches,
each from a fresh per-user tree on the APFS install clone of M4. Each walks the M4 menus to the
map, presses Start Game, waits out the loading screen, types `-ar` (All Random: every slot gets a
hero) and `whosyourdaddy` (Warcraft III's single-player cheat, to keep the match short), then
attack-moves its hero on the Scourge base (A + a minimap click). The hero destroys the towers and
the Frozen Throne and DotA announces "The Sentinel has won!" (shot `won`); F10 > End Game > Quit
Mission leads to the score screen (DotA does not end a single-player game itself). Pass = every
shot saved (the last ones are the score screen), no FATAL, no watchdog report,
`Replay\LastReplay.w3g` written by this run with a Warcraft III replay header, and the wave
output (dumped with `REFROZEN_AUDIO_DUMP`; background runs use SDL's dummy driver) holding sound
(16-bit RMS over 100). **Result: 3/3 PASS** (replays 8,620–8,638 bytes, audio RMS 1,473–1,614;
the random heroes differ per run). The user also heard the menu music and the button clicks in a
foreground run. The match is shortened by the cheat; long-session stability (60+ minutes, AI
opponents) is M6's gate.

**Defects found and fixed (each with a deterministic test and mutants):**

| Symptom | Root cause | Fix |
|---|---|---|
| Start Game stops at `wsock32.dll!#9` | a local custom game still initialises winsock; upstream registered wsock32's ordinals wrongly (#10 as `ioctlsocket`) | Winsock 1.1 ordinals as Wine's `wsock32.spec`: #8 htonl, #9 htons, #10 inet_addr, #11 inet_ntoa (per-thread buffer), #14 ntohl, #15 ntohs, #111 WSAGetLastError (TEB+0x34); no socket is opened |
| No sound; the game's "no sound device" dialog | winmm's waveOut was a no-device stub | a real waveOut device on an SDL audio stream (caps, format queries, CALLBACK_FUNCTION/EVENT, prepare/write/reset/close); WOM_OPEN/WOM_CLOSE synchronous, WOM_DONE from a per-device guest thread in queue order, as Wine's winmm |
| The last queued block never reported done (no WOM_DONE) | SDL's resampler holds back a few frames, so the stream never drained to zero | a block is done when no more than 16 frames of it remain queued |
| Once the wave device existed, Miles' mixer dispatched to an unlifted routine (211394A6) | lift input missed routines reached only through the routine table inside Miles' executable MSSMIXER section (128 relocated dwords), which the data scan does not cover | all 72 routines of the table in `config/mss32.manifest` |
| A local game stops on its replay file (`TempReplay.w3g`) | the file is opened with FILE_FLAG_OVERLAPPED and its I/O goes through a completion port, which the runtime did not model | overlapped file I/O: OVERLAPPED offsets (FFFFFFFF:FFFFFFFF appends), ERROR_IO_PENDING plus a packet for associated handles, hEvent's low bit suppresses it, ERROR_HANDLE_EOF, synchronous handles move the file pointer; `CreateIoCompletionPort` associates files |
| The game window tiny on Retina | the window was sized in pixels on a 2x display | one point per game pixel, scaled down to fit the usable screen |

**Fullscreen and Retina/HiDPI (the user's M5 work item, verified separately):** borderless
fullscreen on the current Space (`SDL_HINT_VIDEO_MAC_FULLSCREEN_SPACES=0`), Ctrl+Cmd+F or the
window's control switches to windowed and back (the player's choice overrides the policy); the
frame is fitted with bars (`gfx::FitRect`, never stretched) and pointer positions map back through
the same rectangle (`gfx::FramePoint`, clamped over the bars); the game's clipped virtual cursor
is unchanged; background runs simulate a screen (`REFROZEN_TEST_SCREEN`) and never take over the
display. Evidence: `scripts/m5_display_check.sh` (1512x982 fullscreen with 101-point bars, two
toggles, `-window` scaled onto a 640x400 screen, clicks reaching the same screen as the
reference); `test_win32.py` mode F; `fit_map_test`; mutants M5-F1–F10. The 800x600 test mode is
unchanged and M4's acceptance still passes 3/3 on the M5 build.

**Tests and mutation gate** (`reference/TEST_COVERAGE.md`): 446 checks (lifter 122, loader 23,
Win32 219, GL context and presentation geometry 54, key files 23, jump-table corrections 5), all
passing; ctest 19/19; 150 mutants over M2–M5: 149 KILLED, 1 documented EQUIVALENT (M3-F9), 0
survivors (four M3 mutants re-expressed for the M5 code; M4-D3/D12 first timed out through a mode F
loop, fixed).

**Lift:** 11 modules, 94,560 functions, 2,827,564 instructions, 242 files; two lifts byte-identical,
tree hash (SHA-256 of the generated `*.cpp` concatenated in C-locale name order)
`ae3e0bdc311aa03ca0dbbc1b59b777fadaa7a677becedd012cd6244604ea599d` (the lift changed with the Miles
manifest: +71 functions, +4,136 instructions, +1 file; M4's hash method was not recorded, so the two
values are not compared); `validate_lift.py` HARD PASS on all eleven; 744 unimplemented sites, all in the
documented-unreachable functions. Import coverage: 678 cross-module, 1,090 handled, 300 strict stubs.

**Verify:**
```sh
scripts/setup_tools.sh && scripts/lift.sh && ninja -C build/main refrozen
for t in test_lifter_patches test_loader test_win32 test_gl_context test_font_keydata \
         test_jumptable_corrections; do /opt/homebrew/bin/python3 -I tests/$t.py; done
/opt/homebrew/bin/python3 -I tests/mutate.py
scripts/m5_accept.sh 3 240
scripts/m5_display_check.sh
scripts/m4_accept.sh 3 110          # regression
```

**Remaining risks (for M6+):**
- Not checked against the oracle: playing the native `LastReplay.w3g` in the Wine client (replay
  determinism); the replays only have valid headers and plausible sizes.
- Heroes are assigned by `-ar` (All Random); picking one in a tavern by mouse is unexercised
  (Single Draft's `-random` gave no hero in the first attempts, not investigated).
- The matches are cheat-shortened (invulnerable hero); unit AI over a long game, memory growth and
  frame pacing over 60+ minutes are M6's.
- M4's open rendering items stand (the pale-lit ice spike, isotropic filtering, Direct3D 8 absent).
- 300 strict stubs; macOS's native Spaces fullscreen and exclusive display modes are not exercised
  by the background checks (a simulated screen stands in).
