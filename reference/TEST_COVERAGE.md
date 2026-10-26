# reFrozen — Test coverage and mutation record

Required before any milestone sign-off from M3 on (AGENTS.md, "Mutation gate"). Each test's
expected values are derived independently of our code; each behaviour a milestone adds or
changes has mutants in `tests/mutants.py`, planted by `tests/mutate.py` in a scratch copy of the
sources (`build/mutate/`, never the real tree) after a passing baseline. A mutant counts as caught
only when the test fails on the check named for it; build failures and mutants that do not apply
are INVALID, never kills; a surviving mutant is either fixed by a better test or documented as
equivalent with the reason it cannot change behaviour.

  /opt/homebrew/bin/python3 -I tests/mutate.py [--milestone M3] [--tsv out.tsv]

## Tests and where their expected values come from

| Test | Covers | Checks | Expected values from |
|---|---|---|---|
| `tests/test_lifter_patches.py` | x86recomp lifter patches 0002–0006, 0010, 0011: relocated-pointer discovery, MMX/SSE/SSE2 forms, code sections, jump tables (incl. `mov reg,[t+i*4]; jmp reg` with a `.data` table), stored addresses in every data section, PUSH/POP slot sizes (segment registers, 66h forms) | 122 | Intel SDM lane definitions, worked by hand in the comments; the 53 packed-integer cases of 0010 also agree 53/53 with real x86-64 execution under Rosetta 2 (a one-off development check, not a test dependency) |
| `tests/test_loader.py` | patches 0007–0009, 0012: name/ordinal binding, DllMain order dependencies-first, static loads pinned, DllMain `lpReserved` non-NULL for static and NULL for dynamic loads, strict stubs, indirect-branch diagnostics, kernel32 functions of 0008, GetDiskFreeSpaceA, imm32, stack balance; an execute fault through the guest SEH chain (search pass, then unwind) and the loader's frame around DllMain (detach caught, FreeLibrary TRUE; attach a strict stop) | 23 (one of them 14 results, one 24) | MSDN (DllMain, the functions' documented results, EXCEPTION_ACCESS_VIOLATION's information), Wine's conformance tests (GetDiskFreeSpace), Wine's loader (`MODULE_InitDLL` catches entry-point exceptions), ReactOS imm32 |
| `tests/test_win32.py` | patches 0009, 0012, 0013, 0015 (follow file: appended lines, relative times, partial lines), 0017/0019 (mode X: an unhandled guest fault's report and FATAL_DUMP: plain, dereferenced and unreadable addresses, "-", "*" before "+", sums of expressions, 32-bit wrapping, numbers over 32 bits, signs, products by non-constants, trailing text and unclosed reads refused, 8 nested reads allowed and a 9th refused, reads side by side, the 0x1000-byte bound), 0018 (stall recorder, modes S/T: frames of known make-up — Sleep(160) waits, phases start-up/interactive/loading, file reads and bytes, a texture upload, a guest loop, the sampler's guest function, STALL_MAX, pure getters counted not timed, the recorder's own time never a stall, the first frame timed from start, the cost per import call): REG_DWORD seeding, GetProfileStringA, system language, named events/mutexes and type mismatch, I/O completion ports incl. a woken worker thread, TryEnterCriticalSection across threads, waveOutOpen without a device, EnumDisplayDevicesA, ChangeDisplaySettingsExA, window size-message sequences, glTexGeni, wglSwapLayerBuffers; painting (update regions, WM_PAINT synthesis order and validation, UpdateWindow, BeginPaint's PAINTSTRUCT and WM_ERASEBKGND, show/resize invalidation, DefWindowProc); minimize/restore by ShowWindow and system commands; M5: wsock32's Winsock 1.1 functions by ordinal, wave output (caps, format queries, CALLBACK_FUNCTION device, WOM_* order and thread, header flags, reset, close), overlapped file I/O through a completion port, fullscreen and pointer mapping (mode F: a maximized popup on a simulated 1000x500-point screen, Ctrl+Cmd+F twice, four clicks mapped to the client); nine stops for unimplemented forms (incl. GDI drawing) | 273 | MSDN; for 0018 the program's own make-up (Sleep's documented minimum, a GetTickCount-timed guest loop, its own read sizes); Wine's `user32/tests/msg.c` sequences (verified there on Windows); Wine's winmm/display tests; the GL 1.1 specification |
| `tests/test_gl_context.py` | patches 0012, 0013 via x86recomp's `gl_fog_test`, `gl_texture_test` and `fit_map_test`: the fog factor the device gets from glFog (linear/exp/exp2, translated and rotated eye space, off axis, colour, disabled); texel precision of RGBA4/RGB5_A1/RGB4/RGB5 and TexSubImage2D; presentation geometry (FitRect: pillar/letterbox, never stretched, rounding) and pointer mapping into the frame (FramePoint, clamped over the bars) | 54 (29 + 8 + 17) | GL 1.5 §3.10 (fog coordinate = eye distance, \|z_e\| allowed) and D3D9's vertex-fog rules for the device; GL's float-to-fixed conversion, worked by hand; the fit geometry worked by hand in the test's comments |
| `tests/test_font_keydata.py` | the installed key files' cipher, the installer's key step | 23 | MSVC `rand()` and IDEA published vectors, IDEA multiplication by definition, SDM shift semantics; the official installer's output (Wine oracle, test keys of the player's readme): decodes with valid checksums, holds exactly those keys, re-encodes byte for byte (key material compared, never printed) |
| `tests/test_jumptable_corrections.py` | lift-input correction of over-read jump tables | 5 | the script's documented contract |
| `tests/test_build_flags.py` | patches 0014, 0018: hot host paths (Dispatch, the stall recorder, GPU device, pixel formats, GL context, x87/SSE, mixer) optimised in a Debug configure | 9 | the measured profile of the AI map's load (FEASIBILITY §13) |
| `tests/test_m6_observe.py` | M6 observation tooling: scoreboard detection on OCR text, camera-box detection, the observer's decisions (verify, one retry, never blind, reopen, recentre), relative cursor paths, no hero orders in the match script | 66 | OCR text of real expanded/collapsed boards (run 1 m0125/m0126, probe m0005), positions measured on 800x600 frames, synthetic BMPs with boxes at known places |
| `tests/test_bnupdate_patch.py` | the 1.26a patcher (M0) | – | M0 |
| `ctest` (x86recomp) | upstream's tests (x87, SSE, atomics, Miles DSP, GL draw path, pacing, …) M4's `gl_fog`, `gl_texture` and M5's `fit_map` | 19 | upstream (`pacing` is a known timing flake on this Mac, FEASIBILITY §7) |

M1's 15 lifter mutations (patches 0001–0005) were run by hand before the gate existed and only
their counts were recorded (FEASIBILITY §7); they are not in the registry.

## Mutants (last full run: all milestones)

198 mutants: 1 EQUIVALENT, 197 KILLED. Full gate on m1-air (Apple M1) 2026-10-26: 186 run (all but 0019's), 185 KILLED, 1 EQUIVALENT (M6-B1 first INVALID, see below, then KILLED). FATAL_DUMP arithmetic (patch 0019) mutants M6-D1–M6-D12 run with M6-R1–M6-R4 and M6-S1–M6-S17: 33 KILLED. Stall recorder (patch 0018) mutants M6-S1–M6-S17 run alone 2026-10-26: 17 KILLED. Full gate 2026-10-25 (`build/mutate-m6.tsv`): 163 run, 161 KILLED, 1 EQUIVALENT, 1 INVALID (M6-O1: its anchor changed with the AI-board rule); M6-O1 re-expressed and M6-O9/M6-O10 added, then run alone: KILLED (M6-O10 first SURVIVED: the test's white mark had fewer pixels than the box outline; a heavier, non-box-shaped mark was added).

| Id | Area | Fault planted | File | Test | Expected failure | Result |
|---|---|---|---|---|---|---|
| M2-L1 | module loading | ordinal imports bound by name only | `x86recomp/src/runtime/process.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M2-L2 | module loading | DllMain runs before the DLL's dependencies are loaded | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M2-L3 | module loading | static imports are not pinned (FreeLibrary unloads them) | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M2-L4 | error handling | an import with no handler returns 0 instead of stopping | `x86recomp/src/runtime/hle/hle.cpp` | test_loader.py | no-handler import diagnostic | KILLED |
| M2-L5 | module loading | static imports not initialised before the EXE entry | `x86recomp/src/runtime/process.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M2-L6 | module loading | modules mapped as they are registered (an early importer binds to HLE stubs) | `x86recomp/src/runtime/process.cpp` | test_loader.py | importer mapped before its import is refused | KILLED |
| M2-L7 | error handling | indirect-branch diagnostic loses its wording | `x86recomp/src/runtime/dispatch.cpp` | test_loader.py | branch into a function diagnostic | KILLED |
| M2-K1 | synchronization | InterlockedCompareExchange returns the new value, not the initial one | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | patch 0008 kernel32 results | KILLED |
| M2-K2 | Win32 API | SetCurrentDirectoryA accepts a file | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_loader.py | patch 0008 kernel32 results | KILLED |
| M2-K3 | Win32 API | DisableThreadLibraryCalls accepts any handle | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | patch 0008 kernel32 results | KILLED |
| M3-F1 | game initialization | SHA rotations use a logical shift | `scripts/font_keydata.py` | test_font_keydata.py | rotations use an arithmetic shift | KILLED |
| M3-F2 | game initialization | SHA-1 message schedule (rol 1) instead of SHA-0's | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | KILLED |
| M3-F3 | memory operations | SHA words loaded big-endian | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | KILLED |
| M3-F4 | game initialization | wrong rand() multiplier | `scripts/font_keydata.py` | test_font_keydata.py | MSVC rand after srand(1) | KILLED |
| M3-F5 | game initialization | decoder subtracts the SHA bytes in forward order | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | KILLED |
| M3-F6 | game initialization | encoder adds the SHA bytes in forward order | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file re-encodes byte for byte | KILLED |
| M3-F7 | error handling | decoder skips the trailer checksum | `scripts/font_keydata.py` | test_font_keydata.py | bit flipped is rejected | KILLED |
| M3-F8 | game initialization | IDEA multiplication: 0 not taken as 65536 | `scripts/font_keydata.py` | test_font_keydata.py | IDEA multiplication modulo 65537 | KILLED |
| M3-F9 | game initialization | key string keeps zero rand() bytes | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | EQUIVALENT |
| M3-F10 | game initialization | IDEA key expansion rotates by 8, not 25 | `scripts/font_keydata.py` | test_font_keydata.py | IDEA reference vector | KILLED |
| M3-F11 | game initialization | decoder uses the encryption subkeys | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | KILLED |
| M3-F12 | game initialization | encoder writes the plaintext length off by one | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file re-encodes byte for byte | KILLED |
| M3-F13 | game initialization | setup XORs the rand() bytes with the digest shifted by one | `scripts/font_keydata.py` | test_font_keydata.py | RoC key file decodes | KILLED |
| M3-K1 | Win32 API | GetDiskFreeSpaceA reports 4096-byte sectors | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_loader.py | M3 GetDiskFreeSpaceA results | KILLED |
| M3-K2 | Win32 API | GetDiskFreeSpaceA swaps free and total clusters | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_loader.py | M3 GetDiskFreeSpaceA results | KILLED |
| M3-K3 | error handling | GetDiskFreeSpaceA accepts any drive letter | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_loader.py | M3 GetDiskFreeSpaceA results | KILLED |
| M3-K4 | error handling | GetDiskFreeSpaceA fails without setting the last error | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_loader.py | M3 GetDiskFreeSpaceA results | KILLED |
| M3-K5 | Win32 API | the guest's C: root is not created at startup | `x86recomp/src/runtime/process.cpp` | test_loader.py | M3 GetDiskFreeSpaceA results | KILLED |
| M3-I1 | Win32 API | ImmAssociateContextEx reports success with IMM disabled | `x86recomp/src/runtime/hle/imm32.cpp` | test_loader.py | M3 imm32 results | KILLED |
| M3-I2 | Win32 API | ImmReleaseContext fails | `x86recomp/src/runtime/hle/imm32.cpp` | test_loader.py | M3 imm32 results | KILLED |
| M3-I3 | Win32 API | ImmGetContext returns a context | `x86recomp/src/runtime/hle/imm32.cpp` | test_loader.py | M3 imm32 results | KILLED |
| M3-I4 | memory operations | ImmGetConversionStatus writes its outputs | `x86recomp/src/runtime/hle/imm32.cpp` | test_loader.py | M3 imm32 results | KILLED |
| M3-I5 | Win32 API | ImmGetCompositionStringA pops the wrong argument count (stack imbalance) | `x86recomp/src/runtime/hle/imm32.cpp` | test_loader.py | M3 stack balanced | KILLED |
| M3-L1 | module loading | static imports attached with a NULL lpReserved (Storm then breaks every MPQ) | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M3-L2 | module loading | LoadLibrary treated as a static load (non-NULL lpReserved, pinned) | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | DllMain order, ordinal + name binding | KILLED |
| M3-R1 | Win32 API | seeded DWORDs typed REG_BINARY | `x86recomp/src/runtime/hle/advapi32.cpp` | test_win32.py | reg: type REG_DWORD | KILLED |
| M3-R2 | memory operations | seeded DWORDs stored big-endian | `x86recomp/src/runtime/hle/advapi32.cpp` | test_win32.py | reg: the seeded value | KILLED |
| M3-P1 | Win32 API | GetProfileStringA keeps a value's quotes | `x86recomp/src/runtime/hle/kernel32_misc.cpp` | test_win32.py | profile: value found | KILLED |
| M3-P2 | Win32 API | GetProfileStringA compares key names case-sensitively | `x86recomp/src/runtime/hle/kernel32_misc.cpp` | test_win32.py | profile: value found | KILLED |
| M3-P3 | Win32 API | GetProfileStringA keeps the default's trailing blanks | `x86recomp/src/runtime/hle/kernel32_misc.cpp` | test_win32.py | profile: default, trailing blanks dropped | KILLED |
| M3-P4 | memory operations | GetProfileStringA fills the whole buffer (no room for the NUL) | `x86recomp/src/runtime/hle/kernel32_misc.cpp` | test_win32.py | profile: truncated to size - 1 | KILLED |
| M3-G1 | Win32 API | GetSystemDefaultLangID differs from the user default | `x86recomp/src/runtime/hle/kernel32.cpp` | test_win32.py | lang: GetSystemDefaultLangID is en-US | KILLED |
| M3-N1 | synchronization | OpenEventA looks for a mutex | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | named: OpenEventA finds it | KILLED |
| M3-N2 | error handling | opening another type's name reports ERROR_FILE_NOT_FOUND | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | named: type mismatch on open | KILLED |
| M3-N3 | synchronization | creating on another type's name hands back that object | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | named: CreateMutexA on an event's name | KILLED |
| M3-C1 | synchronization | GetQueuedCompletionStatus leaves *lpOverlapped on timeout | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | iocp: *lpOverlapped NULL on timeout | KILLED |
| M3-C2 | synchronization | completion packets dequeued last in, first out | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | iocp: FIFO bytes | KILLED |
| M3-C3 | threading | a post does not wake waiting threads | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | iocp: a post wakes a thread blocked | KILLED |
| M3-C4 | error handling | CreateIoCompletionPort(INVALID_HANDLE_VALUE, port) makes a new port | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | iocp: INVALID_HANDLE_VALUE with an existing port fails | KILLED |
| M3-C5 | error handling | associating a handle that is not a file silently succeeds | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | stop 3 | KILLED |
| M3-W1 | Win32 API | waveOutOpen accepts a device that does not exist | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | wave: device 1 is out of range | KILLED |
| M3-D1 | Win32 API | EnumDisplayDevicesA lists adapter 1 too | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | display: no adapter 1 | KILLED |
| M3-D2 | Win32 API | the adapter is not flagged primary | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | display: primary device | KILLED |
| M3-D3 | error handling | ChangeDisplaySettingsExA accepts any device name | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | display: unknown device is DISP_CHANGE_BADPARAM | KILLED |
| M3-D4 | error handling | monitor enumeration silently reports no monitor | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | stop 1 | KILLED |
| M3-S1 | Win32 API | popups get no size messages at creation | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | W: popup: NCCREATE, CREATE, SIZE(RESTORED), MOVE | KILLED |
| M3-S2 | Win32 API | a popup's WM_MOVE comes before its WM_SIZE | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | W: popup: NCCREATE, CREATE, SIZE(RESTORED), MOVE | KILLED |
| M3-S3 | Win32 API | maximizing at creation reports SIZE_RESTORED | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | W: maximized popup: ... SIZE(RESTORED), MOVE, then MOVE, SIZE(MAXIMIZED) | KILLED |
| M3-S4 | memory operations | a maximized window one pixel narrower than the work area | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | W: maximized popup: the maximized size | KILLED |
| M3-S5 | Win32 API | overlapped windows never get their deferred size messages | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | W: overlapped: its first ShowWindow | KILLED |
| M3-S6 | error handling | WS_MINIMIZE at creation is ignored | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | stop 5 | KILLED |
| M3-O1 | Win32 API | glTexGeni accepts SPHERE_MAP for R and Q | `x86recomp/src/runtime/gl/context.cpp` | test_win32.py | gl: SPHERE_MAP for R is INVALID_ENUM | KILLED |
| M3-O2 | error handling | glTexGeni allowed between glBegin and glEnd | `x86recomp/src/runtime/gl/context.cpp` | test_win32.py | gl: inside glBegin/glEnd is INVALID_OPERATION | KILLED |
| M3-O3 | error handling | glTexGeni accepts any pname | `x86recomp/src/runtime/gl/context.cpp` | test_win32.py | gl: pname OBJECT_PLANE is INVALID_ENUM | KILLED |
| M3-O4 | error handling | wglSwapLayerBuffers swaps for planes that do not exist | `x86recomp/src/runtime/hle/opengl32.cpp` | test_win32.py | P: a plane that does not exist stops the process | KILLED |
| M3-X1 | memory operations | PMADDWD multiplies unsigned words | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 pmaddwd mm0, mm1 | KILLED |
| M3-X2 | memory operations | PACKUSWB saturates to signed bytes | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 packuswb mm0, mm1 | KILLED |
| M3-X3 | memory operations | logical shifts by exactly the lane width do not clear (words would still clear: the shift is done in int; dwords keep their value) | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 pslld mm0, 32 | KILLED |
| M3-X4 | memory operations | PMULHW takes the high word of an unsigned product | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 pmulhw mm0, mm1 | KILLED |
| M3-X5 | memory operations | PCMPGTW compares unsigned | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 pcmpgtw mm0, mm1 | KILLED |
| M3-X6 | memory operations | PSHUFW reads the order bits from the wrong pair | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 pshufw mm0, mm1, 0x1B | KILLED |
| M3-X7 | memory operations | unpack-high takes the low half | `x86recomp/src/runtime/simd64.h` | test_lifter_patches.py | 0010 punpckhbw mm0, mm1 | KILLED |
| M3-X8 | memory operations | SSE2 packs pack each half separately | `x86recomp/src/runtime/sse.h` | test_lifter_patches.py | 0010 packssdw xmm0, xmm1 | KILLED |
| M3-X9 | memory operations | PSHUFHW shuffles the low half | `x86recomp/src/runtime/sse.h` | test_lifter_patches.py | 0010 pshufhw xmm0, xmm1, 0x1B | KILLED |
| M3-X10 | memory operations | MOVHPS store writes the low quadword | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0010 movhps qword ptr [ebx], xmm1 | KILLED |
| M3-X11 | memory operations | PUNPCKL* with an m32 operand left unimplemented | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0010 no unimplemented sites | KILLED |
| M3-X12 | memory operations | PADDSW lifted as an unsigned saturating add | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0010 paddsw mm0, mm1 | KILLED |
| M3-T1 | module loading | any mov before jmp reg taken as the table load | `x86recomp/tools/lifter/function.cpp` | test_lifter_patches.py | 0010 jmp through another register is not a table jump | KILLED |
| M3-T2 | module loading | tables outside .text accepted without relocated slots | `x86recomp/tools/lifter/function.cpp` | test_lifter_patches.py | 0010 a table outside .text needs relocated slots | KILLED |
| M3-K6 | game initialization | the installer accepts 25-character keys | `scripts/native_install.py` | test_font_keydata.py | key: 25 characters refused | KILLED |
| M3-K7 | game initialization | the installer accepts characters outside the key alphabet | `scripts/native_install.py` | test_font_keydata.py | key: a character outside the alphabet refused | KILLED |
| M3-J1 | module loading | corrections applied to every module | `scripts/jumptable_corrections.py` | test_jumptable_corrections.py | another module's correction is ignored | KILLED |
| M3-J2 | error handling | a correction naming a missing case is ignored | `scripts/jumptable_corrections.py` | test_jumptable_corrections.py | a target the table lacks is an error | KILLED |
| M3-Y1 | synchronization | TryEnterCriticalSection lets a thread in while another owns the section | `x86recomp/src/runtime/hle/kernel32.cpp` | test_win32.py | cs: another thread is refused | KILLED |
| M3-Y2 | synchronization | TryEnterCriticalSection by the owner is not counted | `x86recomp/src/runtime/hle/kernel32.cpp` | test_win32.py | cs: RecursionCount 2 | KILLED |
| M3-T3 | module loading | relocated slots scanned only in sections named .rdata/.data | `x86recomp/tools/lifter/main.cpp` | test_lifter_patches.py | 0010 relocated slot in another data section lifts its target | KILLED |
| M3-T4 | module loading | unaligned relocated slots skipped | `x86recomp/tools/lifter/main.cpp` | test_lifter_patches.py | 0010 unaligned relocated slot lifts its target | KILLED |
| M4-P1 | memory operations | segment register pushed as a zero-extended dword | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0011 push ds | KILLED |
| M4-P2 | memory operations | segment register pushed into a 2-byte slot (the original bug) | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0011 push ds | KILLED |
| M4-P3 | memory operations | pop with a 16-bit operand size takes 4 bytes | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0011 pop ax | KILLED |
| M4-P4 | memory operations | push imm16 (66h) takes 4 bytes | `x86recomp/tools/lifter/emit.cpp` | test_lifter_patches.py | 0011 push word 1234h | KILLED |
| M4-L1 | error handling | the loader's frame does not catch (exception reaches the top) | `x86recomp/src/runtime/hle/kernel32_seh.cpp` | test_loader.py | exception in DllMain(DETACH): handler, unwind, FreeLibrary TRUE | KILLED |
| M4-L2 | error handling | the loader's frame skips the unwind of the frames above it | `x86recomp/src/runtime/hle/kernel32_seh.cpp` | test_loader.py | exception in DllMain(DETACH): handler, unwind, FreeLibrary TRUE | KILLED |
| M4-L3 | error handling | execute access violation reported as a read | `x86recomp/src/runtime/hle/kernel32_seh.cpp` | test_loader.py | exception in DllMain(DETACH): handler, unwind, FreeLibrary TRUE | KILLED |
| M4-L4 | error handling | an exception in DllMain(ATTACH) is swallowed | `x86recomp/src/runtime/hle/kernel32.cpp` | test_loader.py | exception in DllMain(ATTACH) stops the process | KILLED |
| M4-L5 | error handling | a branch to unmapped memory stops without dispatching an exception | `x86recomp/src/runtime/dispatch.cpp` | test_loader.py | exception in DllMain(DETACH): handler, unwind, FreeLibrary TRUE | KILLED |
| M4-D1 | window messages | WM_PAINT never synthesised | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: shown popup: paint count 1 | KILLED |
| M4-D2 | window messages | PM_REMOVE removes WM_PAINT (validates without painting) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: PM_REMOVE leaves WM_PAINT queued | KILLED |
| M4-D3 | window messages | BeginPaint does not validate | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: validated: PeekMessage finds nothing | KILLED |
| M4-D4 | window messages | fErase inverted | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: shown popup: fErase 1 | KILLED |
| M4-D5 | window messages | InvalidateRect ignores its rect (whole client) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: two rects: rcPaint (10,5)-(60,40) | KILLED |
| M4-D6 | window messages | a second rect replaces the update region instead of joining it | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: two rects: rcPaint (10,5)-(60,40) | KILLED |
| M4-D7 | window messages | hidden windows keep an update region | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: hidden: InvalidateRect left no update region | KILLED |
| M4-D8 | window messages | UpdateWindow does not paint | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: two rects: paint count 2 | KILLED |
| M4-D9 | error handling | bad window handle reported with the wrong error | `x86recomp/src/runtime/hle/win32.h` | test_win32.py | D: InvalidateRect(bad hwnd): 1400 | KILLED |
| M4-D10 | window messages | a resize invalidates the whole client whatever the class style | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: grown, class style 0: rcPaint (100,0)-(150,50) | KILLED |
| M4-D11 | window messages | CS_HREDRAW ignored on resize | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: grown, CS_HREDRAW: rcPaint (0,0)-(120,50) | KILLED |
| M4-D12 | window messages | DefWindowProc(WM_PAINT) does not validate | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: DefWindowProc's WM_PAINT validated it | KILLED |
| M4-D13 | window messages | DefWindowProc(WM_ERASEBKGND) claims to erase without a brush | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | D: shown popup: fErase 1 | KILLED |
| M4-D14 | error handling | FillRect succeeds without drawing (fake success) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | stop 6: an unimplemented form stops the process | KILLED |
| M4-D15 | error handling | DrawTextA succeeds without drawing (fake success) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | stop 7: an unimplemented form stops the process | KILLED |
| M4-M1 | window messages | minimizing sends WM_SIZE(SIZE_RESTORED) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | M: ShowWindow(SW_MINIMIZE) | KILLED |
| M4-M2 | window messages | a minimized window keeps the activation | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | M: ShowWindow(SW_MINIMIZE) | KILLED |
| M4-M3 | window messages | restoring sends no WM_SIZE | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | M: ShowWindow(SW_RESTORE) | KILLED |
| M4-M4 | window messages | DefWindowProc ignores SC_MINIMIZE | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | M: DefWindowProc(SC_MINIMIZE) minimizes | KILLED |
| M4-G1 | rendering | GL fog on the device's view-space z (no range fog: the original bug) | `x86recomp/src/runtime/gl/context.cpp` | test_gl_context.py | linear on axis | KILLED |
| M4-G2 | rendering | sized formats stored at 8 bits | `x86recomp/src/runtime/gl/context.cpp` | test_gl_context.py | RGBA4 | KILLED |
| M4-G3 | rendering | RGB5_A1 keeps 8-bit alpha | `x86recomp/src/runtime/gl/context.cpp` | test_gl_context.py | RGB5_A1 alpha 127 | KILLED |
| M4-G4 | rendering | glTexSubImage2D forgets the sized format | `x86recomp/src/runtime/gl/context.cpp` | test_gl_context.py | TexSubImage2D on RGB5_A1 | KILLED |
| M4-G5 | rendering | fixed-point conversion truncates instead of rounding | `x86recomp/src/runtime/gl/context.cpp` | test_gl_context.py | RGBA4 | KILLED |
| M5-O1 | file I/O | overlapped transfers ignore the OVERLAPPED's offset | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: read data: 00 00 00 00 'ABCD' | KILLED |
| M5-O2 | file I/O | an associated handle's I/O completes synchronously without a packet | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: overlapped WriteFile returns FALSE | KILLED |
| M5-O3 | file I/O | the completion packet loses the association's key | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: packet key 55h | KILLED |
| M5-O4 | file I/O | a handle may be associated twice | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: a second association fails | KILLED |
| M5-O5 | file I/O | offset FFFFFFFFh:FFFFFFFFh does not append | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: append wrote at the end | KILLED |
| M5-O6 | file I/O | a read at the end of the file succeeds with 0 bytes | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: ... ERROR_HANDLE_EOF | KILLED |
| M5-O7 | file I/O | hEvent's low bit does not suppress the packet | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: low bit: no packet | KILLED |
| M5-O8 | file I/O | a synchronous handle's file pointer stays put | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | O: ... file pointer at 5 | KILLED |
| M5-W1 | Win32 API | htons swaps 32 bits | `x86recomp/src/runtime/hle/shell_net.cpp` | test_win32.py | wsock: htons(1234h) = 3412h | KILLED |
| M5-W2 | Win32 API | inet_addr fails for every address (the upstream behaviour) | `x86recomp/src/runtime/hle/shell_net.cpp` | test_win32.py | wsock: inet_addr(127.0.0.1) in network order | KILLED |
| M5-W3 | Win32 API | inet_ntoa prints the address in host order | `x86recomp/src/runtime/hle/shell_net.cpp` | test_win32.py | wsock: inet_ntoa(127.0.0.1) | KILLED |
| M5-W4 | Win32 API | WSAGetLastError always 0 | `x86recomp/src/runtime/hle/shell_net.cpp` | test_win32.py | wsock: WSAGetLastError is the last error | KILLED |
| M5-A1 | audio | the resampler's held-back frames keep the last block queued | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: both blocks returned in order | KILLED |
| M5-A2 | audio | no WOM_OPEN | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: WOM_OPEN from waveOutOpen | KILLED |
| M5-A3 | audio | no WOM_CLOSE | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: WOM_CLOSE from waveOutClose | KILLED |
| M5-A4 | audio | an unprepared block is accepted | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: unprepared write: WAVERR_UNPREPARED | KILLED |
| M5-A5 | audio | waveOutReset returns before the blocks are | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: waveOutReset returned the block first | KILLED |
| M5-A6 | audio | non-PCM formats accepted | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: non-PCM query: WAVERR_BADFORMAT | KILLED |
| M5-A7 | audio | a device with queued blocks can be closed | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: close while queued: STILLPLAYING | KILLED |
| M5-A8 | audio | caps report mono | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | V: caps: 2 channels | KILLED |
| M5-F1 | display | the fitted frame is not centred (no left bar) | `x86recomp/src/runtime/gfx/device.cpp` | test_gl_context.py | 800x600 in 1512x982 | KILLED |
| M5-F2 | display | the fitted width truncates instead of rounding | `x86recomp/src/runtime/gfx/device.cpp` | test_gl_context.py | 800x600 in 1000x500 | KILLED |
| M5-F3 | input | pointer x mapped from the frame's top instead of its left | `x86recomp/src/runtime/gfx/device.cpp` | test_gl_context.py | 1512x982: centre | KILLED |
| M5-F4 | input | a pointer over a bar is not clamped to the frame | `x86recomp/src/runtime/gfx/device.cpp` | test_gl_context.py | 1512x982: left bar | KILLED |
| M5-F5 | input | pointer positions in a scaled or fullscreen window are not mapped to the client | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: fullscreen: a click inside the frame | KILLED |
| M5-F6 | display | Ctrl+Cmd+F is swallowed without toggling | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: Ctrl+Cmd+F: windowed, then fullscreen | KILLED |
| M5-F7 | display | the fullscreen policy ignores the player's windowed choice | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: a maximized popup goes fullscreen on the simulated screen, and again after the toggles | KILLED |
| M5-F8 | display | background runs never simulate fullscreen (TEST_SCREEN ignored by the policy) | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: a maximized popup goes fullscreen on the simulated screen, and again after the toggles | KILLED |
| M5-F9 | display | the windowed size is fitted to the real display, not the (simulated) screen | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: windowed (Ctrl+Cmd+F): the scaled window maps to the client | KILLED |
| M5-F10 | display | simulated fullscreen leaves the window at its windowed size | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | F: fullscreen: a click inside the frame | KILLED |
| M6-B1 | performance | Dispatch built at -O0 in a Debug build | `x86recomp/CMakeLists.txt` | test_build_flags.py | optimised in a Debug build: dispatch.cpp | KILLED |
| M6-B2 | performance | the GPU device built at -O0 in a Debug build | `x86recomp/CMakeLists.txt` | test_build_flags.py | optimised in a Debug build: gfx/gpu_device.cpp | KILLED |
| M6-B3 | performance | the GL context built at -O0 in a Debug build | `x86recomp/CMakeLists.txt` | test_build_flags.py | optimised in a Debug build: gl/context.cpp | KILLED |
| M6-O1 | observation | one row label taken as an expanded scoreboard | `scripts/m6_observe.py` | test_m6_observe.py | board: one stray label is not a board | KILLED |
| M6-O2 | observation | a failed collapse does not stop the clicks (blind toggling) | `scripts/m6_observe.py` | test_m6_observe.py | fail: expanded periodic frames: still no clicks (never blind) | KILLED |
| M6-O3 | observation | more than one retry after a failed collapse | `scripts/m6_observe.py` | test_m6_observe.py | fail: still expanded after the retry: no more clicks | KILLED |
| M6-O4 | observation | a periodic shot taken as the pending verification | `scripts/m6_observe.py` | test_m6_observe.py | seq: a periodic shot before the verification: no input | KILLED |
| M6-O5 | observation | a collapse counted when the board is still expanded | `scripts/m6_observe.py` | test_m6_observe.py | seq: ... counted | KILLED |
| M6-O6 | observation | the camera recentred at exactly the tolerance | `scripts/m6_observe.py` | test_m6_observe.py | seq: camera moved within tolerance: no input | KILLED |
| M6-O7 | observation | the match script selects the hero during the match | `scripts/m6_accept.sh` | test_m6_observe.py | match script: no 'key F1' during the match | KILLED |
| M6-O8 | observation | the cursor moved in one big jump (larger than the game takes per frame) | `scripts/m6_observe.py` | test_m6_observe.py | seq: expanded: toggle: steps of at most 200 points | KILLED |
| M6-O9 | observation | the AI board taken as expanded from one team line | `scripts/m6_observe.py` | test_m6_observe.py | board: one team line is not the AI board | KILLED |
| M6-O10 | observation | any white component taken as the camera box (no size check) | `scripts/m6_observe.py` | test_m6_observe.py | camera: a mark with more white pixels than the box, but not box-shaped, is not the box | KILLED |
| M6-S1 | stall recorder | every frame is reported, not only those over the threshold | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: a short frame is not reported | KILLED |
| M6-S2 | stall recorder | the recorder's own report time counts towards a stall | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: and never makes a stall | KILLED |
| M6-S3 | stall recorder | leaving a scope does not restore the category it interrupted | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the guest loop is charged to guest code | KILLED |
| M6-S4 | stall recorder | import calls are not timed | `x86recomp/src/runtime/hle/hle.cpp` | test_win32.py | S: the sleep is charged to waits | KILLED |
| M6-S5 | stall recorder | Sleep is not a wait | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the sleep is charged to waits | KILLED |
| M6-S6 | stall recorder | PeekMessage does not mark the frame as pumping messages | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | S: phase of a frame that pumped messages: interactive | KILLED |
| M6-S7 | stall recorder | frames after the first pumping one are still called start-up | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: phase of a frame without pumping, after pumping: loading | KILLED |
| M6-S8 | stall recorder | ReadFile's bytes are not counted | `x86recomp/src/runtime/hle/kernel32_file.cpp` | test_win32.py | S: file reads counted (3 ops, 3 KB) | KILLED |
| M6-S9 | stall recorder | the graphics device's texture work is charged as plain graphics | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the texture upload is texture work | KILLED |
| M6-S10 | stall recorder | lifted function names are not recognised (the mangled suffix read as hex) | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the sampler names the guest function waiting in Sleep | KILLED |
| M6-S11 | stall recorder | the executable's code range is skipped instead of searched | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the sampler names the guest function looping | KILLED |
| M6-S12 | stall recorder | STALL_MAX is ignored | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: STALL_MAX=1: one report | KILLED |
| M6-S13 | stall recorder | the categories are not reset per frame | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the categories partition the frame | KILLED |
| M6-S14 | stall recorder | guest code called from the host is not charged to guest code | `x86recomp/src/runtime/process.cpp` | test_win32.py | S: the guest loop is charged to guest code | KILLED |
| M6-S15 | stall recorder | the first frame is not timed from the start | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: the first frame is timed from the start | KILLED |
| M6-S16 | stall recorder | untimed imports are not counted | `x86recomp/src/runtime/stall.h` | test_win32.py | S: pure getters are counted, not timed | KILLED |
| M6-S17 | stall recorder | GetTickCount is timed like other imports | `x86recomp/src/runtime/stall.cpp` | test_win32.py | S: pure getters are counted, not timed | KILLED |
| M6-R1 | fault report | an unhandled guest fault reported without its reason | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: the fault address and the reason | KILLED |
| M6-R2 | fault report | an unhandled guest fault reported without the guest's state (host-only report) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: the guest registers (as of the call) | KILLED |
| M6-R3 | fault report | FATAL_DUMP's [expr] uses the address instead of the value read there | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a dereferenced address (base + e_lfanew) reaches the PE signature | KILLED |
| M6-R4 | fault report | the requested guest memory is not dumped in a fatal report | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a plain address is dumped | KILLED |
| M6-D1 | fault report | FATAL_DUMP's "-" adds | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: subtraction | KILLED |
| M6-D2 | fault report | FATAL_DUMP's "*" evaluated left to right with "+" and "-" (no precedence) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: "*" binds tighter than "+" | KILLED |
| M6-D3 | fault report | FATAL_DUMP's sum takes only a number after "+" (the old grammar) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: the sum of two expressions | KILLED |
| M6-D4 | fault report | FATAL_DUMP accepts numbers over 32 bits (truncated) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a number over 32 bits is malformed | KILLED |
| M6-D5 | fault report | FATAL_DUMP accepts a signed number (strtoul's sign) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a signed number is malformed | KILLED |
| M6-D6 | fault report | FATAL_DUMP multiplies by any expression | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a product by a non-constant is malformed | KILLED |
| M6-D7 | fault report | FATAL_DUMP's nesting limit is off by one (9 reads allowed) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a 9th nested read is refused | KILLED |
| M6-D8 | fault report | FATAL_DUMP's nesting limit is off by one (only 7 reads allowed) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: reads nest 8 deep | KILLED |
| M6-D9 | fault report | FATAL_DUMP's nesting depth is not restored after a read (reads in sequence count as nested) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: reads side by side do not count as nested | KILLED |
| M6-D10 | fault report | FATAL_DUMP dumps are not bounded | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: a dump is at most 0x1000 bytes | KILLED |
| M6-D11 | fault report | FATAL_DUMP's arithmetic refuses to wrap (an overflowing sum is malformed) | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: addition wraps at 32 bits | KILLED |
| M6-D12 | fault report | FATAL_DUMP accepts an unclosed read | `x86recomp/src/runtime/dispatch.cpp` | test_win32.py | X: FATAL_DUMP: an unclosed read is malformed | KILLED |
| M6-T1 | observation | a partly written follow line is queued before it is complete | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | FF: each complete appended line read once | KILLED |
| M6-T2 | observation | follow lines are read again at every poll | `x86recomp/src/runtime/hle/user32_window.cpp` | test_win32.py | FF: each complete appended line read once | KILLED |

## Survivors, equivalents and fixes found by the gate

- **M6-B1 became INVALID after patch 0018:** 0018 added `stall.cpp` to the `-O2` line its anchor
  named, and the mutant was not updated then. Re-expressed (drop `dispatch.cpp` from the line): KILLED.
- **0019's tests were shaped by two mutants before the first run:** a signed operand (M6-D5) is
  tested as `++4`, because `strtoull("-4")` already exceeds 32 bits and the range check would hide
  the missing digit check; a depth counter that is never restored (M6-D9) only shows with reads side
  by side, so nine summed reads are tested next to the eight nested ones.
- **M6-S2 needed a test aid:** whether the recorder's own report time can make a stall depends on how
  slow a report is. `<ID>_TEST_STALL_REPORT_MS` makes each report 150 ms slower, and the check requires
  every reported frame to be over the threshold without its recorder time.

- **M3-F9 (equivalent):** the key string's zero-byte filter never drops a byte for seed 0x150B
  (the first 19 `rand()` low bytes are non-zero), so removing it cannot change the output.
- **M3-X3 survived its first run:** shifting by exactly a lane's width is computed in `int` for
  words (still 0), but is undefined for dwords and kept the value on arm64. The tests had no
  dword shift by 32; `pslld/psrld mm0, 32` were added (SDM: counts above 31 clear the lane) and
  kill it.
- **M3-I5 survived its first run:** a handler popping the wrong number of stdcall arguments was
  invisible. Every guest mode now checks that `esp` is the same after its calls ("stack
  balanced").
- **M3-F6 was "killed" by the wrong check:** two mutants of equal size written within one second
  shared stale bytecode. The runner now purges `__pycache__` and runs Python tests with `-B`.
- **M2-L2 became INVALID in M3** (its text no longer matched after `LoadLifted` took the static
  CONTEXT) and was re-expressed for the same fault; it is killed.
- The first loader mutation run (M2) missed "DllMain before dependencies" because the test EXE
  imported the dependency first; the EXE now imports the dependent DLL first.
- Not observable, not mutated: `PUNPCKL*` reading 64 instead of 32 bits from memory gives the same
  result except at the end of mapped memory (the mutant that removes the m32 form, M3-X11, is
  killed by the unimplemented-site check instead).
- **M4-D7 survived its first run:** a hidden window keeping an update region was invisible to the
  checks (painting needs a visible window, and showing one invalidates it whole). It is observable
  on Windows through BeginPaint on the hidden window; mode D now checks that its rcPaint is empty.
- **M4-L4 was killed by the wrong check:** with the attach-time exception swallowed, the test EXE
  ended itself with code 4, which "stops the process" accepted. The check now excludes the EXE's
  own exit code, as the stop modes already do.
- **M3-C3, M3-C4, M3-C5, M3-W1 became INVALID in M5** (completion ports learned file association
  and posts went through `PostCompletion`; waveOut gained a real device) and were re-expressed for
  the same faults against the new code; all are killed.
- **M4-D3 and M4-D12 were killed by the wrong check in M5's first full run:** a runtime that never
  validates floods the queue with WM_PAINT, and mode F's pump loop (counting only empty-queue
  rounds) never ended, so the whole test timed out. Mode F now counts every round; both are killed
  by their own checks.
