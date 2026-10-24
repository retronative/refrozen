# reFrozen — Feasibility

Status: **M0 in progress (2026-10-24).** Labels: VERIFIED (observed locally, reproducible),
OBSERVED (stated by a cited external source, not reproduced here), HYPOTHESIS, FALSIFIED,
UNRESOLVED. The full research report with sources is
[research/reports/WC3 native macOS port methods.md](research/reports/WC3%20native%20macOS%20port%20methods.md).

## TL;DR

| Question | Answer |
|---|---|
| Is the input the right release? | **Yes.** WC3 RoC + TFT 1.21b (enGB), patched with the official 1.26a English patch to build 1.26.0.6401. All binaries are x86 Win32 PE, MSVC 2005 (linker 8.0), unpacked (§2). |
| Recompile toolchain | **None ready-made.** The only maintained Win32 x86 → portable C++ recompiler is x86recomp (MIT, ~1 week old, no playable title). Recommended: fork it, as ReCarbon forked SpeedBreaker (report §"Recommended approach"). |
| Reimplementation instead? | **No** for this goal. No open-source engine plays DotA 6.83 or keeps lockstep with real 1.26a clients. |
| Native install path | **Partial.** Tome extraction is native and byte-identical to the official installer. The 1.26a deltas still need a native patcher (§1). |

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
- **1.26a patch:** `War3TFT_126a_English.exe` embeds an MPQ containing `Patch_War3x.mpq`. In it,
  each file is a BNUpdate record with a 0x18-byte header: type 1 = whole file (e.g. `msvcr80.dll`,
  PE at +0x18), type 4 = compressed BSDIFF40 delta (`game.dll`, `war3.exe`, `Storm.dll`). The
  header CRC/size fields don't match the 1.21b files directly; the format is UNRESOLVED.
- **Oracle:** the official installers + patch under Wine 11.18 (development only) give the 1.26a
  binaries, sizes matching the delta headers exactly. Copied to `game/oracle-1.26a/`:

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

## 3. Differences from ReCarbon
- **No reference port** with a working toolchain (VERIFIED by the research: none exists).
- **x86-32 recompilation:** no `.pdata`; discovery uses `.reloc`, call targets, vtables and a
  Ghidra export (HYPOTHESIS, following x86recomp's design).
- **Bit-exact lockstep** with Windows 1.26a peers requires exact x87/SSE semantics (OBSERVED).
- **Legal:** the WC3 EULA bans reverse engineering (OBSERVED). Like ReCarbon, only tooling is
  published; the recompile is generated locally from the player's own copy.

## Open questions (UNRESOLVED)
- The BNUpdate record format and a native 1.26a patcher that reproduces the oracle hashes.
- x86recomp fit: lift `Storm.dll` first as a falsification test.
- Self-modifying code or lock-free code relying on x86 memory ordering in `game.dll`.
- Whether `DotA v6.83se.w3x` loads on 1.26a and its MPQ protection quirks.
- Whether the 1.21b Mac builds in the tomes (`MAC*/`) carry useful symbols.
