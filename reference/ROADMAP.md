# reFrozen — Roadmap (x86 Win32 → Apple Silicon)

Every milestone is gated, as in ReCarbon. Starting each milestone needs the user's **explicit
approval**, even when the previous one passed. A milestone passes only when its acceptance
criteria are met **and observed**. Each milestone records **Evidence** (what was observed) and
**Verify** (how to reproduce it from a clean checkout plus your own game copy).

States: **Passed**, **Partial** (lists the unmet criteria), **Blocked** (root cause or the
unknown documented). Diagnosing a failure is progress; it does not pass a criterion.

## M0 — Correct input and feasibility *(Partial, 2026-10-24)*
- **Evidence** (FEASIBILITY §1–2): inputs hashed; tomes extracted natively and byte-identical to
  the official installer for 1.21b; 1.26a oracle binaries hashed; `game.dll` headers, sections and
  imports recorded; research report written.
- **Open:** native 1.26a patcher; the approach decision (proposed: fork x86recomp) awaits the
  user's approval; DotA 6.83se map check.
- **Do:**
  - Install WC3 RoC + TFT 1.21b and patch to 1.26a, under `game/` (git-ignored):
    - natively: extract the installer tomes with StormLib (`scripts/mpq_extract.c`) and apply the
      1.26a BNUpdate deltas (BSDIFF40 records in `Patch_War3x.mpq`) with a native patcher;
    - as a development oracle only: the official installers and patch under Wine. The native
      result must match the oracle's hashes byte for byte. Players never need Wine.
  - Inspect `war3.exe`, `Game.dll`, `Storm.dll` and the other shipped DLLs: PE headers,
    sections, entry points, relocations, imports by DLL, compiler/runtime versions, packers.
  - Survey candidate x86 → arm64 static recompilers and Win32 runtimes, and the alternative of
    an engine reimplementation. Record the trade-offs and pick one with the user.
  - Confirm DotA v6.83 loads with 1.26a (map header, required patch version).
- **Accept:**
  - SHA-256/MD5 and header facts for every input binary recorded in `FEASIBILITY.md`.
  - The native install/patch path produces 1.26a `war3.exe`, `Game.dll` and `Storm.dll`
    byte-identical to the Wine oracle.
  - Import list by DLL, with a first classification (Win32 core, D3D, audio, network, Storm).
  - A written approach decision, approved by the user.
- **Verify:** `shasum -a 256` on the inputs; the inspection script's output matches
  FEASIBILITY.

## Later milestones (to be detailed after M0)
Following `../game-port-knowledge/general/bring-up-checklist.md`:
- **M1** Toolchain + recompile-only PoC (0 unrecognized instructions, structural validation,
  byte-identical reruns).
- **M2** Native compile and link (strict import stubs, 0 unresolved symbols).
- **M3** Runtime initialization (CRT, threads, file I/O, MPQ access).
- **M4** First frame (D3D → Metal) and the main menu.
- **M5** Audio, input, a local game on a DotA map.
- **M6** LAN / online play.
