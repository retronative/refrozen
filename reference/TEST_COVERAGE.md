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
| `tests/test_win32.py` | patches 0009, 0012, 0013: REG_DWORD seeding, GetProfileStringA, system language, named events/mutexes and type mismatch, I/O completion ports incl. a woken worker thread, TryEnterCriticalSection across threads, waveOutOpen without a device, EnumDisplayDevicesA, ChangeDisplaySettingsExA, window size-message sequences, glTexGeni, wglSwapLayerBuffers; painting (update regions, WM_PAINT synthesis order and validation, UpdateWindow, BeginPaint's PAINTSTRUCT and WM_ERASEBKGND, show/resize invalidation, DefWindowProc); minimize/restore by ShowWindow and system commands; M5: wsock32's Winsock 1.1 functions by ordinal, wave output (caps, format queries, CALLBACK_FUNCTION device, WOM_* order and thread, header flags, reset, close), overlapped file I/O through a completion port, fullscreen and pointer mapping (mode F: a maximized popup on a simulated 1000x500-point screen, Ctrl+Cmd+F twice, four clicks mapped to the client); nine stops for unimplemented forms (incl. GDI drawing) | 219 | MSDN; Wine's `user32/tests/msg.c` sequences (verified there on Windows); Wine's winmm/display tests; the GL 1.1 specification |
| `tests/test_gl_context.py` | patches 0012, 0013 via x86recomp's `gl_fog_test`, `gl_texture_test` and `fit_map_test`: the fog factor the device gets from glFog (linear/exp/exp2, translated and rotated eye space, off axis, colour, disabled); texel precision of RGBA4/RGB5_A1/RGB4/RGB5 and TexSubImage2D; presentation geometry (FitRect: pillar/letterbox, never stretched, rounding) and pointer mapping into the frame (FramePoint, clamped over the bars) | 54 (29 + 8 + 17) | GL 1.5 §3.10 (fog coordinate = eye distance, \|z_e\| allowed) and D3D9's vertex-fog rules for the device; GL's float-to-fixed conversion, worked by hand; the fit geometry worked by hand in the test's comments |
| `tests/test_font_keydata.py` | the installed key files' cipher, the installer's key step | 23 | MSVC `rand()` and IDEA published vectors, IDEA multiplication by definition, SDM shift semantics; the official installer's output (Wine oracle, test keys of the player's readme): decodes with valid checksums, holds exactly those keys, re-encodes byte for byte (key material compared, never printed) |
| `tests/test_jumptable_corrections.py` | lift-input correction of over-read jump tables | 5 | the script's documented contract |
| `tests/test_bnupdate_patch.py` | the 1.26a patcher (M0) | – | M0 |
| `ctest` (x86recomp) | upstream's tests (x87, SSE, atomics, Miles DSP, GL draw path, pacing, …) M4's `gl_fog`, `gl_texture` and M5's `fit_map` | 19 | upstream (`pacing` is a known timing flake on this Mac, FEASIBILITY §7) |

M1's 15 lifter mutations (patches 0001–0005) were run by hand before the gate existed and only
their counts were recorded (FEASIBILITY §7); they are not in the registry.

## Mutants (last full run: all milestones)

120 mutants: 1 EQUIVALENT, 119 KILLED.

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
| M3-C5 | error handling | associating a file with a port silently returns a new port | `x86recomp/src/runtime/hle/kernel32_sync.cpp` | test_win32.py | stop 3 | KILLED |
| M3-W1 | Win32 API | waveOutOpen reports success with no device (a fake handle) | `x86recomp/src/runtime/hle/winmm_wave.cpp` | test_win32.py | wave: mapper finds no driver | KILLED |
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

## Survivors, equivalents and fixes found by the gate

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
