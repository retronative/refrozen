# reFrozen — Feasibility

Status: **M0 complete (2026-10-24), awaiting the user's sign-off.** Labels: VERIFIED (observed locally, reproducible),
OBSERVED (stated by a cited external source, not reproduced here), HYPOTHESIS, FALSIFIED,
UNRESOLVED. The full research report with sources is
[research/reports/WC3 native macOS port methods.md](research/reports/WC3%20native%20macOS%20port%20methods.md).

## TL;DR

| Question | Answer |
|---|---|
| Is the input the right release? | **Yes.** WC3 RoC + TFT 1.21b (enGB), patched with the official 1.26a English patch to build 1.26.0.6401. All binaries are x86 Win32 PE, MSVC 2005 (linker 8.0), unpacked (§2). |
| Recompile toolchain | **None ready-made.** The only maintained Win32 x86 → portable C++ recompiler is x86recomp (MIT, ~1 week old, no playable title). Recommended: fork it, as ReCarbon forked SpeedBreaker (report §"Recommended approach"). |
| Reimplementation instead? | **No** for this goal. No open-source engine plays DotA 6.83 or keeps lockstep with real 1.26a clients. |
| Native install path | **Done.** `scripts/native_install.py` installs RoC + TFT and applies the 1.26a patch with no Wine; it reproduces the official result (all loose files byte-identical, all MPQ contents identical except the CD-key files), deterministically (§1). |
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

## 6. Compatibility issues carried forward
- **CD-key step (UNRESOLVED, M3):** the native installer leaves the 5 `font\font.*` files as
  shipped. The installer encodes the key (`cdkey26`, `cdkey1encode`) into them; per the project
  rule the port follows that practice, so the encoding must be reproduced from the installer and
  checked against the oracle made with the test key. Whether 1.26a needs these files for offline
  play is not yet tested.
- **Intro movies (VERIFIED, M3):** on a fresh profile the client plays its intro through
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
