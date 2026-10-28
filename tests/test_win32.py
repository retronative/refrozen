#!/usr/bin/env python3
"""End-to-end tests for reFrozen's x86recomp runtime patch 0009 (M3), no game
data: a guest EXE (assembled with llvm-mc) is lifted, linked with the runtime
and recomp_opengl, and run once per mode.

  /opt/homebrew/bin/python3 -I tests/test_win32.py [--modes A,N,...] [--cache DIR]

--modes runs only the named groups' checks (the mutation gate's focused
runs): A W V O N Q B (with R) F (with FF) X S T M D L P, and stops (the numbered modes). Without
it every mode runs; a subset run says so in its last line. --cache DIR reuses
the linked test program from DIR when every input of its compile is unchanged
(the mutation gate's runs; see link_key).

Modes (the command line's last character):
  A  Win32 functions: REG_DWORD seeding, GetProfileStringA, the system
     language, named events/mutexes, I/O completion ports (with a worker
     thread woken by a post), waveOutOpen, EnumDisplayDevicesA,
     ChangeDisplaySettingsExA. One 1/0 flag per check.
  W  window messages: the WM_NCCREATE/WM_CREATE/WM_SIZE/WM_MOVE a wndproc
     sees for a popup, a WS_MAXIMIZE popup, an overlapped window and its
     first ShowWindow.
  L  OpenGL: glTexGeni's state and errors, wglSwapLayerBuffers.
  P  wglSwapLayerBuffers of a plane that does not exist (a stop).
  F  fullscreen and pointer mapping (M5): a maximized popup (the whole
     screen) on a simulated 1000x500-point screen (<ID>_TEST_SCREEN), clicked
     by test pointers in fullscreen, after Ctrl+Cmd+F (windowed) and after it
     again (fullscreen); the clicks' client positions and the runtime's log.
  M  minimize/restore (M4): the messages ShowWindow(SW_MINIMIZE /
     SW_RESTORE) and DefWindowProc(WM_SYSCOMMAND, SC_MINIMIZE / SC_RESTORE)
     send to an active window.
  V  wave output (M5): device caps, format queries, a CALLBACK_FUNCTION
     device (WOM_OPEN, WOM_DONE in order from another thread, WOM_CLOSE),
     header flags and errors, waveOutReset. One 1/0 flag per check.
  O  overlapped file I/O through a completion port (M5): association,
     pending writes and reads at the OVERLAPPED's offset with their packets,
     append, end of file, hEvent's no-packet bit, a synchronous handle given
     an OVERLAPPED. One 1/0 flag per check.
  B  LAN discovery broadcasts (patch 0025): a datagram to
     255.255.255.255:6112 arrives at 0.0.0.0:6112 on this host; R: the same
     with 255.255.255.255 refused (<ID>_TEST_NO_LIMITED_BROADCAST, a VPN as
     the primary service): it still arrives, and a broadcast to another port
     is refused. One 1/0 flag per check.
  D  painting (M4): update regions, WM_PAINT synthesis and order,
     UpdateWindow, BeginPaint's PAINTSTRUCT and WM_ERASEBKGND, invalidation
     by show and resize, DefWindowProc's WM_PAINT. One 1/0 flag per check.
  1-5  the other forms M3 does not implement, each a stop with its diagnostic:
     monitor enumeration (EnumDisplayDevicesA), ChangeDisplaySettingsExA with
     an hwnd, CreateIoCompletionPort on a file handle, GetProfileStringA
     enumeration, CreateWindowExA(WS_MINIMIZE).
  6-9  GDI drawing M4 does not implement, each a stop: FillRect, DrawTextA,
     InvalidateRect(NULL), DefWindowProc erasing with a class brush.

Expected values come from Windows' documented behaviour and Wine's
conformance tests (which pass on Windows), ReactOS where named, and the
GL 1.1 specification; each check says which.

Needs scripts/setup_tools.sh (tools/x86recomp built) and Homebrew LLVM.
"""
import hashlib
import os
import shutil
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_loader as tl  # noqa: E402  (PE writer, assembler, paths)

EXE = 0x00400000
TEXT = EXE + 0x1000
DATA_RVA, DATA_SIZE = 0x8000, 0x4000  # .text may use 0x1000-0x7FFF
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


def image(text, data, import_dir):
    """PE32 EXE: .text at RVA 0x1000, .data (DATA_SIZE) at DATA_RVA."""
    pad = lambda blob, n=0x200: blob + b"\0" * (-len(blob) % n)
    body_data = bytes(data.b).ljust(DATA_SIZE, b"\0")
    assert len(text) <= DATA_RVA - 0x1000, "text overlaps .data"
    secs = [(b".text", 0x1000, pad(text), DATA_RVA - 0x1000, tl.EXEC),
            (b".data", DATA_RVA, pad(body_data), DATA_SIZE, tl.RW)]
    hdr = bytearray(0x200)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, 0x40)
    hdr[0x40:0x44] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", hdr, 0x44, 0x14C, 2, 0, 0, 0, 0xE0, 0x0102)
    opt = 0x58
    struct.pack_into("<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII", hdr, opt,
                     0x10B, 8, 0, len(secs[0][2]), len(secs[1][2]), 0, 0x1000, 0x1000, DATA_RVA,
                     EXE, 0x1000, 0x200, 4, 0, 0, 0, 4, 0, 0, DATA_RVA + DATA_SIZE, 0x200, 0, 2, 0,
                     0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    struct.pack_into("<II", hdr, opt + 96 + 8, *import_dir)
    raw, body = 0x200, b""
    for i, (name, rva, blob, vsize, ch) in enumerate(secs):
        o = opt + 0xE0 + 40 * i
        hdr[o:o + 8] = name.ljust(8, b"\0")
        struct.pack_into("<IIIIIIHHI", hdr, o + 8, vsize, rva, len(blob), raw + len(body), 0, 0, 0, 0, ch)
        body += blob
    return bytes(hdr) + body


IMPORTS = [
    ("kernel32.dll", ["ExitProcess", "OutputDebugStringA", "GetLastError", "GetCommandLineA",
                      "GetProfileStringA", "GetSystemDefaultLangID", "GetUserDefaultLangID",
                      "CreateEventA", "OpenEventA", "CreateMutexA", "OpenMutexA",
                      "CreateIoCompletionPort", "PostQueuedCompletionStatus",
                      "GetQueuedCompletionStatus", "CreateThread", "Sleep", "WaitForSingleObject",
                      "InitializeCriticalSection", "TryEnterCriticalSection", "LeaveCriticalSection",
                      "CreateFileA", "ReadFile", "WriteFile", "CloseHandle", "SetFilePointer",
                      "SetLastError", "GetCurrentThreadId", "GetTickCount", "LoadLibraryA",
                      "GetProcAddress"]),
    # Winsock 1.1 by ordinal (Wine's wsock32.spec): htonl, htons, inet_addr,
    # inet_ntoa, ntohl, ntohs, WSAGetLastError; mode N's sockets: accept, bind,
    # closesocket, connect, getpeername, getsockname, ioctlsocket, listen,
    # recv, recvfrom, select, send, sendto, setsockopt, socket.
    ("wsock32.dll", [8, 9, 10, 11, 14, 15, 111, 1, 2, 3, 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 23]),
    ("mswsock.dll", ["AcceptEx", "GetAcceptExSockaddrs"]),
    ("user32.dll", ["EnumDisplayDevicesA", "EnumDisplaySettingsA", "ChangeDisplaySettingsExA",
                    "RegisterClassA", "CreateWindowExA", "DefWindowProcA", "ShowWindow", "GetDC",
                    "wsprintfA", "SystemParametersInfoA", "InvalidateRect", "UpdateWindow", "BeginPaint",
                    "EndPaint", "FillRect", "DrawTextA", "PeekMessageA", "DispatchMessageA",
                    "PostMessageA", "SetTimer", "SetWindowPos"]),
    ("advapi32.dll", ["RegOpenKeyExA", "RegQueryValueExA"]),
    ("winmm.dll", ["waveOutOpen", "waveOutGetDevCapsA", "waveOutPrepareHeader", "waveOutUnprepareHeader",
                   "waveOutWrite", "waveOutReset", "waveOutClose", "waveOutGetID"]),
    ("gdi32.dll", ["ChoosePixelFormat", "SetPixelFormat"]),
    ("opengl32.dll", ["wglCreateContext", "wglMakeCurrent", "wglSwapLayerBuffers", "glGetError",
                      "glTexGeni", "glBegin", "glEnd", "glBindTexture", "glTexImage2D"]),
]
# fixed text offsets (function entries)
WORKER, WNDPROC, TRYCS, PAINTPROC, WAVEPROC, MAIN = 0x10, 0x40, 0xC0, 0x100, 0x1C0, 0x240
REG_KEY, REG_VALUE, REG_DWORD = "Software\\reFrozen Test", "Dword", 0x12345678


class Guest:
    """Builds the EXE's asm and the names of mode A's checks, in order."""

    def __init__(self):
        self.d = tl.Data(EXE)
        self.d.va0 = EXE + DATA_RVA
        self.iat, self.imp = self.d.imports(IMPORTS)
        self.dll = {s: dll for dll, syms in IMPORTS for s in syms}
        self.names = []
        self.s = {}
        self.buf, self.n = self.d.put(b"\0" * 256), self.d.put(b"\0" * 4)
        self.tmp = self.d.put(b"\0" * 64)
        self.var = {k: self.d.put(b"\0" * 4) for k in
                    ("hk", "type", "size", "lang", "port", "bytes", "key", "ovl", "wkey", "thread",
                     "hwave", "hwnd", "hdc", "logn", "seg0", "seg1", "seg2", "seg3", "hover", "tryres",
                     "pcount", "perase", "pl", "pt", "pr", "pb", "phdc", "ecount", "hp", "hq", "cn", "xself")}
        self.clicks = self.d.put(b"\0" * 16)  # mode F: WM_LBUTTONDOWN lParams
        self.ps = self.d.put(b"\0" * 64)    # PAINTSTRUCT
        self.msg = self.d.put(b"\0" * 28)   # MSG
        self.r1 = self.d.put(struct.pack("<iiii", 10, 5, 30, 20))
        self.r2 = self.d.put(struct.pack("<iiii", 20, 10, 60, 40))
        self.r3 = self.d.put(struct.pack("<iiii", 200, 200, 300, 300))
        self.r4 = self.d.put(struct.pack("<iiii", 1, 2, 3, 4))
        self.wc2 = self.d.put(b"\0" * 40)
        self.wc3 = self.d.put(b"\0" * 40)
        self.wc4 = self.d.put(b"\0" * 40)
        self.ovl = self.d.put(b"\0" * 20)    # OVERLAPPED
        # wave output: callback log (msg, p1, thread) x 16, two WAVEHDRs of 400
        # bytes of 8-bit silence (50 ms at 8 kHz mono), formats, caps
        self.wlog, self.wn = self.d.put(b"\0" * 12 * 16), self.d.put(b"\0" * 4)
        self.wdata = self.d.put(b"\x80" * 400)
        self.whdr1, self.whdr2 = self.d.put(b"\0" * 32), self.d.put(b"\0" * 32)
        self.wfx8 = self.d.put(struct.pack("<HHIIHHH", 1, 1, 8000, 8000, 1, 8, 0))
        self.wfxbad = self.d.put(struct.pack("<HHIIHHH", 2, 1, 8000, 8000, 1, 8, 0))  # ADPCM
        self.wcaps = self.d.put(b"\0" * 52)
        self.hwo, self.wmain, self.wsnap = self.d.put(b"\0" * 4), self.d.put(b"\0" * 4), self.d.put(b"\0" * 4)
        self.iobuf = self.d.put(b"\0" * 32)
        self.nv = {k: self.d.put(b"\0" * 4) for k in ("u1", "u2", "u3", "u4", "t0", "ls", "cs", "as", "c2", "len", "one", "x", "lin")}
        self.nsa1, self.nsa2, self.nsa3, self.nsa4, self.nsa5, self.nfrom, self.nbc = (self.d.put(b"\0" * 16)
                                                                                     for _ in range(7))
        self.nbuf = self.d.put(b"\0" * 64)
        # mode Q: handles and results, OVERLAPPEDs, AcceptEx's two 32-byte
        # address areas, addresses, and read buffers filled with ABh.
        self.qv = {k: self.d.put(b"\0" * 4) for k in
                   ("mod", "ev", "e2", "S", "port", "L", "L2", "A1", "A2", "A3", "A4", "A5", "C", "C3", "acc",
                    "bytes", "key", "ovl", "ret", "abytes", "pl", "ll", "pr", "rl", "lin", "lg", "i", "good")}
        self.qovl = [self.d.put(b"\0" * 20) for _ in range(13)]
        self.qab = self.d.put(b"\xEE" * 64)
        self.qsaL, self.qsaC, self.qsa2, self.qsaL2 = (self.d.put(b"\0" * 16) for _ in range(4))
        self.qbuf = [self.d.put(b"\xAB" * 64) for _ in range(7)]
        self.nfr, self.nfw, self.nfe = (self.d.put(b"\0" * 20) for _ in range(3))  # fd_set: count + 4 SOCKETs
        self.ntv1, self.ntv0 = self.d.put(struct.pack("<ii", 1, 0)), self.d.put(struct.pack("<ii", 0, 0))
        self.oport, self.ofile, self.obytes, self.okey, self.opovl, self.oev = (self.d.put(b"\0" * 4)
                                                                             for _ in range(6))
        self.label = 0
        self.cs = self.d.put(b"\0" * 24)  # CRITICAL_SECTION
        self.dd = self.d.put(struct.pack("<I", 424) + b"\0" * 420)        # DISPLAY_DEVICEA
        dm = bytearray(156)  # DEVMODEA: dmSize (offset 36) = 156
        struct.pack_into("<H", dm, 36, 156)
        self.dm = self.d.put(bytes(dm))
        self.wfx = self.d.put(struct.pack("<HHIIHHH", 1, 2, 22050, 88200, 4, 16, 0))  # WAVEFORMATEX
        self.logbuf = self.d.put(b"\0" * (64 * 16))
        self.out = self.d.put(b"\0" * 4096)
        # PIXELFORMATDESCRIPTOR: nSize, nVersion, dwFlags (DRAW_TO_WINDOW |
        # SUPPORT_OPENGL | DOUBLEBUFFER), RGBA, 32-bit colour, 24-bit depth,
        # 8-bit stencil.
        pfd = struct.pack("<HHI", 40, 1, 0x25) + bytes([0, 32] + [0] * 13 + [24, 8, 0, 0, 0]) + b"\0" * 12
        assert len(pfd) == 40
        self.pfd = self.d.put(pfd)
        self.rect = self.d.put(b"\0" * 16)
        self.wc = self.d.put(b"\0" * 40)

    def str(self, text):
        if text not in self.s:
            self.s[text] = self.d.put(text.encode() + b"\0", 1)
        return self.s[text]

    def call(self, sym, *args):
        out = "".join(f"  push {a}\n" for a in reversed([hex(x) if isinstance(x, int) else x for x in args]))
        return out + f"  call dword ptr [{self.iat[(self.dll[sym], sym)]:#x}]\n"

    def chk(self, name, cond):
        self.names.append(name)
        return cond + "  call flag\n"

    @staticmethod
    def eq(v):
        return f"  cmp eax, {v:#x}\n" if isinstance(v, int) and v >= 0 else f"  cmp eax, {v}\n"

    @staticmethod
    def nonzero():
        return "  test eax, eax\n  setnz al\n  cmp al, 1\n"

    def mem(self, va, v, size="dword"):
        return f"  cmp {size} ptr [{va:#x}], {v:#x}\n"

    def gle(self, name, code):
        return self.call("GetLastError") + self.chk(name, self.eq(code))


def build_text(g):
    v = g.var
    a = ""  # mode A
    # -- wsock32's pure functions (Winsock 1.1, BSD semantics for inet_addr).
    a += g.call(9, 0x1234) + g.chk("wsock: htons(1234h) = 3412h", g.eq(0x3412))
    a += g.call(15, 0xABCD1234) + g.chk("wsock: ntohs keeps the low word only", g.eq(0x3412))
    a += g.call(8, 0x12345678) + g.chk("wsock: htonl(12345678h) = 78563412h", g.eq(0x78563412))
    a += g.call(14, 0x78563412) + g.chk("wsock: ntohl inverts it", g.eq(0x12345678))
    a += g.call(10, g.str("127.0.0.1")) + g.chk("wsock: inet_addr(127.0.0.1) in network order", g.eq(0x0100007F))
    a += g.call(10, g.str("1.2.3")) + g.chk("wsock: inet_addr(a.b.c): c fills the last 16 bits", g.eq(0x03000201))
    a += g.call(10, g.str("bad")) + g.chk("wsock: inet_addr of a non-address is INADDR_NONE", g.eq(0xFFFFFFFF))
    a += g.call(11, 0x0100007F) + "  mov esi, eax\n"
    a += g.chk("wsock: inet_ntoa(127.0.0.1)", "  cmp dword ptr [esi], 0x2E373231\n  jne 9f\n"
               "  cmp dword ptr [esi+4], 0x2E302E30\n  jne 9f\n  cmp word ptr [esi+8], 0x31\n9:\n")
    a += g.call("SetLastError", 10054) + g.call(111) + g.chk("wsock: WSAGetLastError is the last error", g.eq(10054))
    # -- REG_DWORD seeding (GameConfig::registry_dwords): RegQueryValueExA
    # reports type REG_DWORD (4), 4 bytes, the value (MSDN).
    a += f"  mov dword ptr [{v['size']:#x}], 64\n"
    a += g.call("RegOpenKeyExA", 0x80000001, g.str(REG_KEY), 0, 0x20019, v["hk"])
    a += g.chk("reg: RegOpenKeyExA(HKCU, seeded key) succeeds", g.eq(0))
    a += f"  push {v['size']:#x}\n  push {g.tmp:#x}\n  push {v['type']:#x}\n  push 0\n  push {g.str(REG_VALUE):#x}\n"
    a += f"  push dword ptr [{v['hk']:#x}]\n  call dword ptr [{g.iat[('advapi32.dll', 'RegQueryValueExA')]:#x}]\n"
    a += g.chk("reg: RegQueryValueExA succeeds", g.eq(0))
    a += g.chk("reg: type REG_DWORD", g.mem(v["type"], 4))
    a += g.chk("reg: 4 bytes", g.mem(v["size"], 4))
    a += g.chk("reg: the seeded value", g.mem(g.tmp, REG_DWORD))
    # -- GetProfileStringA (MSDN GetProfileString / GetPrivateProfileString):
    # case-insensitive names, quotes dropped, default without trailing
    # blanks, truncation to size - 1, return = characters copied.
    a += g.call("GetProfileStringA", g.str("MSS"), g.str("msSdebug"), g.str("None"), g.tmp, 64)
    a += g.chk("profile: value found (case-insensitive), 3 characters", g.eq(3))
    a += g.chk("profile: quotes removed", g.mem(g.tmp, 0x00736559))  # "Yes\0"
    a += g.call("GetProfileStringA", g.str("MSS"), g.str("missing"), g.str("Abc  "), g.tmp, 64)
    a += g.chk("profile: default, trailing blanks dropped", g.eq(3))
    a += g.chk("profile: default text", g.mem(g.tmp, 0x00636241))  # "Abc\0"
    a += g.call("GetProfileStringA", g.str("MSS"), g.str("missing"), g.str("None"), g.tmp, 3)
    a += g.chk("profile: truncated to size - 1", g.eq(2))
    a += g.chk("profile: truncated text", g.mem(g.tmp, 0x00006F4E))  # "No\0" (+ old byte 0)
    a += g.call("GetProfileStringA", g.str("Nope"), g.str("MSSDebug"), 0, g.tmp, 64)
    a += g.chk("profile: NULL default is empty", g.eq(0))
    # -- System language: the en-US system the runtime models; the system
    # default equals the user default on a stock install.
    a += g.call("GetSystemDefaultLangID") + f"  mov dword ptr [{v['lang']:#x}], eax\n"
    a += g.chk("lang: GetSystemDefaultLangID is en-US", g.eq(0x409))
    a += g.call("GetUserDefaultLangID")
    a += g.chk("lang: system default = user default", f"  cmp eax, dword ptr [{v['lang']:#x}]\n")
    # -- Named objects (MSDN CreateEvent/CreateMutex/OpenEvent; NT
    # STATUS_OBJECT_TYPE_MISMATCH = ERROR_INVALID_HANDLE).
    a += g.call("CreateEventA", 0, 1, 0, g.str("evt"))
    a += g.chk("named: CreateEventA", g.nonzero()) + g.gle("named: new name, last error 0", 0)
    a += g.call("OpenEventA", 2, 0, g.str("evt")) + g.chk("named: OpenEventA finds it", g.nonzero())
    a += g.call("OpenEventA", 2, 0, g.str("nope")) + g.chk("named: OpenEventA unknown name", g.eq(0))
    a += g.gle("named: unknown name is ERROR_FILE_NOT_FOUND", 2)
    a += g.call("CreateMutexA", 0, 0, g.str("evt")) + g.chk("named: CreateMutexA on an event's name", g.eq(0))
    a += g.gle("named: type mismatch on create is ERROR_INVALID_HANDLE", 6)
    a += g.call("OpenMutexA", 0x1F0001, 0, g.str("evt")) + g.chk("named: OpenMutexA on an event's name", g.eq(0))
    a += g.gle("named: type mismatch on open is ERROR_INVALID_HANDLE", 6)
    a += g.call("CreateEventA", 0, 1, 0, g.str("evt")) + g.chk("named: CreateEventA again", g.nonzero())
    a += g.gle("named: existing name is ERROR_ALREADY_EXISTS", 183)
    # -- I/O completion ports (MSDN CreateIoCompletionPort,
    # PostQueuedCompletionStatus, GetQueuedCompletionStatus).
    a += g.call("CreateIoCompletionPort", 0xFFFFFFFF, 0, 0, 0) + f"  mov dword ptr [{v['port']:#x}], eax\n"
    a += g.chk("iocp: new port", g.nonzero())
    a += f"  push 0\n  push 0\n  push dword ptr [{v['port']:#x}]\n  push 0xFFFFFFFF\n"
    a += f"  call dword ptr [{g.iat[('kernel32.dll', 'CreateIoCompletionPort')]:#x}]\n"
    a += g.chk("iocp: INVALID_HANDLE_VALUE with an existing port fails", g.eq(0))
    a += g.gle("iocp: ERROR_INVALID_PARAMETER", 87)
    gq = lambda timeout: (f"  push {timeout:#x}\n  push {v['ovl']:#x}\n  push {v['key']:#x}\n  push {v['bytes']:#x}\n"
                          f"  push dword ptr [{v['port']:#x}]\n"
                          f"  call dword ptr [{g.iat[('kernel32.dll', 'GetQueuedCompletionStatus')]:#x}]\n")
    post = lambda n, key, ovl, port=None: (f"  push {ovl:#x}\n  push {key:#x}\n  push {n:#x}\n" +
                                           (f"  push {port:#x}\n" if port is not None else
                                            f"  push dword ptr [{v['port']:#x}]\n") +
                                           f"  call dword ptr [{g.iat[('kernel32.dll', 'PostQueuedCompletionStatus')]:#x}]\n")
    a += f"  mov dword ptr [{v['ovl']:#x}], 0x55\n" + gq(0)
    a += g.chk("iocp: empty port, zero timeout: FALSE", g.eq(0)) + g.gle("iocp: WAIT_TIMEOUT", 258)
    a += g.chk("iocp: *lpOverlapped NULL on timeout", g.mem(v["ovl"], 0))
    a += post(5, 0x11, 0x1234) + g.chk("iocp: post", g.eq(1)) + post(6, 0x22, 0x5678)
    a += gq(0) + g.chk("iocp: first packet", g.eq(1))
    a += g.chk("iocp: FIFO bytes", g.mem(v["bytes"], 5)) + g.chk("iocp: FIFO key", g.mem(v["key"], 0x11))
    a += g.chk("iocp: FIFO overlapped", g.mem(v["ovl"], 0x1234))
    a += gq(10) + g.chk("iocp: second packet", g.eq(1)) + g.chk("iocp: second key", g.mem(v["key"], 0x22))
    a += g.call("CreateThread", 0, 0, TEXT + WORKER, f"dword ptr [{v['port']:#x}]", 0, 0)
    a += f"  mov dword ptr [{v['thread']:#x}], eax\n" + g.call("Sleep", 100)
    a += post(7, 0x33, 0) + g.call("WaitForSingleObject", f"dword ptr [{v['thread']:#x}]", 5000)
    a += g.chk("iocp: a post wakes a thread blocked in GetQueuedCompletionStatus", g.eq(0))
    a += g.chk("iocp: the woken thread got the packet", g.mem(v["wkey"], 0x33))
    a += post(1, 0, 0, 0x1234) + g.chk("iocp: post to a bad handle fails", g.eq(0))
    a += g.gle("iocp: ERROR_INVALID_HANDLE", 6)
    # -- TryEnterCriticalSection (MSDN): nonzero if entered or already owned
    # by the caller (RecursionCount counts it), zero if another thread owns
    # the section.
    a += g.call("InitializeCriticalSection", g.cs)
    a += g.call("TryEnterCriticalSection", g.cs) + g.chk("cs: a free section is entered", g.eq(1))
    a += g.call("TryEnterCriticalSection", g.cs) + g.chk("cs: the owner enters again", g.eq(1))
    a += g.chk("cs: RecursionCount 2", g.mem(g.cs + 8, 2))
    trycs = (g.call("CreateThread", 0, 0, TEXT + TRYCS, g.cs, 0, 0) + "  mov esi, eax\n" +
             g.call("WaitForSingleObject", "esi", 5000))
    a += f"  mov dword ptr [{v['tryres']:#x}], 0x55\n" + trycs
    a += g.chk("cs: another thread is refused", g.mem(v["tryres"], 0))
    a += g.call("LeaveCriticalSection", g.cs) + g.call("LeaveCriticalSection", g.cs)
    a += f"  mov dword ptr [{v['tryres']:#x}], 0x55\n" + trycs
    a += g.chk("cs: released, another thread enters", g.mem(v["tryres"], 1))
    # -- waveOutOpen: one wave output device (0); device 1 is out of range
    # (MMSYSERR_BADDEVICEID). The rest of wave output is mode V.
    a += g.call("waveOutOpen", v["hwave"], 1, g.wfx, 0, 0, 0)
    a += g.chk("wave: device 1 is out of range", g.eq(2))
    # -- Display devices (MSDN EnumDisplayDevices/ChangeDisplaySettingsEx;
    # Wine's tests: an unknown device name is DISP_CHANGE_BADPARAM).
    a += g.call("EnumDisplayDevicesA", 0, 0, g.dd, 0) + g.chk("display: adapter 0 exists", g.eq(1))
    a += g.chk("display: named \\\\.\\DISP...", g.mem(g.dd + 4, 0x5C2E5C5C))
    a += g.chk("display: ...DISPLAY", g.mem(g.dd + 8, 0x50534944))
    a += f"  mov eax, dword ptr [{g.dd + 164:#x}]\n  and eax, 4\n"
    a += g.chk("display: primary device", "  cmp eax, 4\n")
    a += g.call("EnumDisplaySettingsA", g.dd + 4, 0xFFFFFFFF, g.dm)
    a += g.chk("display: its name works for EnumDisplaySettingsA", g.eq(1))
    a += g.call("EnumDisplayDevicesA", 0, 1, g.dd, 0) + g.chk("display: no adapter 1", g.eq(0))
    a += g.call("ChangeDisplaySettingsExA", g.str("\\\\.\\DISPLAY1"), 0, 0, 0, 0)
    a += g.chk("display: restore on the adapter succeeds", g.eq(0))
    a += g.call("ChangeDisplaySettingsExA", g.str("\\\\.\\DISPLAY9"), 0, 0, 0, 0)
    a += g.chk("display: unknown device is DISP_CHANGE_BADPARAM", g.eq(0xFFFFFFFB))

    # mode W: wndproc log of four windows (see the test for the sequences)
    wc = struct.pack("<IIIIIIIIII", 0, TEXT + WNDPROC, 0, 0, EXE, 0, 0, 0, 0, g.str("T"))
    g.d.b[g.wc - g.d.va0:g.wc - g.d.va0 + 40] = wc
    mkclass = g.call("RegisterClassA", g.wc)
    win = lambda title, style, x, y, w, h: g.call("CreateWindowExA", 0, g.str("T"), g.str(title), style,
                                                  x, y, w, h, 0, 0, EXE, 0)
    seg = lambda k: f"  mov eax, dword ptr [{v['logn']:#x}]\n  mov dword ptr [{v[k]:#x}], eax\n"
    w = mkclass + win("p", 0x80000000, 10, 20, 100, 50) + seg("seg0")
    w += win("m", 0x81000000, 10, 20, 100, 50) + seg("seg1")
    w += win("o", 0x00CF0000, 10, 20, 200, 150) + f"  mov dword ptr [{v['hover']:#x}], eax\n" + seg("seg2")
    w += g.call("ShowWindow", f"dword ptr [{v['hover']:#x}]", 5) + seg("seg3")
    w += g.call("SystemParametersInfoA", 0x30, 0, g.rect, 0)  # SPI_GETWORKAREA
    w += g.call("wsprintfA", g.out, g.str("R%X,%X S%X,%X,%X,%X:"), f"dword ptr [{g.rect + 8:#x}]",
                f"dword ptr [{g.rect + 12:#x}]", f"dword ptr [{v['seg0']:#x}]",
                f"dword ptr [{v['seg1']:#x}]", f"dword ptr [{v['seg2']:#x}]", f"dword ptr [{v['seg3']:#x}]")
    w += f"""  add esp, 32
  mov edi, {g.out:#x}
  add edi, eax
  xor esi, esi
3:
  cmp esi, dword ptr [{v['logn']:#x}]
  jae 4f
  mov edx, esi
  shl edx, 4
  push dword ptr [{g.logbuf:#x}+edx+8]
  push dword ptr [{g.logbuf:#x}+edx+4]
  push dword ptr [{g.logbuf:#x}+edx]
  push {g.str("%X/%X/%X "):#x}
  push edi
  call dword ptr [{g.iat[('user32.dll', 'wsprintfA')]:#x}]
  add esp, 20
  add edi, eax
  inc esi
  jmp 3b
4:
  mov byte ptr [edi], 0x0A
  mov byte ptr [edi+1], 0
""" + g.call("OutputDebugStringA", g.out) + g.call("ExitProcess", 0)

    # mode D: painting. T2 (CS 0) and T3 (CS_HREDRAW | CS_VREDRAW) use
    # paintproc, which records each BeginPaint's PAINTSTRUCT; T uses the
    # logging wndproc (DefWindowProc paints); T4 has a background brush.
    for va, style, name in ((g.wc2, 0, "T2"), (g.wc3, 3, "T3")):
        g.d.b[va - g.d.va0:va - g.d.va0 + 40] = struct.pack("<IIIIIIIIII", style, TEXT + PAINTPROC, 0, 0, EXE,
                                                            0, 0, 0, 0, g.str(name))
    g.d.b[g.wc4 - g.d.va0:g.wc4 - g.d.va0 + 40] = struct.pack("<IIIIIIIIII", 0, TEXT + WNDPROC, 0, 0, EXE, 0, 0,
                                                              0x00E00004, 0, g.str("T4"))
    P = lambda k: f"dword ptr [{v[k]:#x}]"
    NL = "\n"

    def pump():
        # Retrieves and dispatches until the queue is empty (at most 10).
        g.label += 1
        n = g.label
        return (f"  mov dword ptr [{g.tmp:#x}], 10{NL}lp{n}:{NL}" + g.call("PeekMessageA", g.msg, 0, 0, 0, 1) +
                f"  test eax, eax{NL}  jz ld{n}{NL}" + g.call("DispatchMessageA", g.msg) +
                f"  dec dword ptr [{g.tmp:#x}]{NL}  jnz lp{n}{NL}ld{n}:{NL}")

    def peek(remove):
        return g.call("PeekMessageA", g.msg, 0, 0, 0, remove)

    def paint_is(name, count, erase, l, t, r, b):
        rc = (f"  cmp dword ptr [{v['pl']:#x}], {l}{NL}  jne 9f{NL}  cmp dword ptr [{v['pt']:#x}], {t}{NL}"
              f"  jne 9f{NL}  cmp dword ptr [{v['pr']:#x}], {r}{NL}  jne 9f{NL}"
              f"  cmp dword ptr [{v['pb']:#x}], {b}{NL}9:{NL}")
        return (g.chk(f"{name}: paint count {count}", g.mem(v["pcount"], count)) +
                g.chk(f"{name}: fErase {erase}", g.mem(v["perase"], erase)) +
                g.chk(f"{name}: rcPaint ({l},{t})-({r},{b})", rc))

    first_d = len(g.names)  # mode D's checks are split off g.names below
    d = g.call("RegisterClassA", g.wc2) + g.call("RegisterClassA", g.wc3) + mkclass
    # A visible popup: the whole client area is invalid and to be erased.
    # (MSDN BeginPaint: fErase is TRUE when the background still needs
    # erasing, i.e. WM_ERASEBKGND returned 0, as DefWindowProc does for a
    # class without a background brush.)
    d += g.call("CreateWindowExA", 0, g.str("T2"), g.str("d"), 0x90000000, 0, 0, 100, 50, 0, 0, EXE, 0)
    d += f"  mov dword ptr [{v['hp']:#x}], eax{NL}" + pump()
    d += paint_is("D: shown popup", 1, 1, 0, 0, 100, 50)
    d += g.chk("D: shown popup: WM_ERASEBKGND sent once", g.mem(v["ecount"], 1))
    d += g.chk("D: shown popup: BeginPaint returned a DC",
               f"  cmp dword ptr [{v['phdc']:#x}], 0{NL}  setne al{NL}  cmp al, 1{NL}")
    d += peek(0) + g.chk("D: validated: PeekMessage finds nothing", g.eq(0))
    # Two rects, no erase: one paint of their bounding box, sent by
    # UpdateWindow; a second UpdateWindow has nothing to paint.
    d += g.call("InvalidateRect", P("hp"), g.r1, 0) + g.chk("D: InvalidateRect returns TRUE", g.eq(1))
    d += g.call("InvalidateRect", P("hp"), g.r2, 0)
    d += g.call("UpdateWindow", P("hp")) + g.chk("D: UpdateWindow returns TRUE", g.eq(1))
    d += paint_is("D: two rects", 2, 0, 10, 5, 60, 40)
    d += g.chk("D: two rects: no WM_ERASEBKGND without erase", g.mem(v["ecount"], 1))
    d += g.call("UpdateWindow", P("hp")) + g.chk("D: UpdateWindow when valid: TRUE, no paint",
                                                 g.eq(1) + f"  jne 9f{NL}" + g.mem(v["pcount"], 2) + f"9:{NL}")
    # A bad window handle: FALSE and ERROR_INVALID_WINDOW_HANDLE (1400).
    d += g.call("InvalidateRect", 0x12345, 0, 0) + g.chk("D: InvalidateRect(bad hwnd) fails", g.eq(0))
    d += g.gle("D: InvalidateRect(bad hwnd): 1400", 1400)
    d += g.call("UpdateWindow", 0x12345) + g.chk("D: UpdateWindow(bad hwnd) fails", g.eq(0))
    d += g.gle("D: UpdateWindow(bad hwnd): 1400", 1400)
    d += g.call("BeginPaint", 0x12345, g.ps) + g.chk("D: BeginPaint(bad hwnd) returns NULL", g.eq(0))
    d += g.gle("D: BeginPaint(bad hwnd): 1400", 1400)
    # A rect outside the client area invalidates nothing.
    d += g.call("InvalidateRect", P("hp"), g.r3, 1) + peek(0)
    d += g.chk("D: rect outside the client: nothing to paint", g.eq(0))
    # Hidden windows are not painted; showing one invalidates it whole.
    d += g.call("ShowWindow", P("hp"), 0) + g.call("InvalidateRect", P("hp"), 0, 1) + peek(0)
    d += g.chk("D: hidden: no WM_PAINT", g.eq(0))
    # ...and invalidating it had no effect: BeginPaint called on it directly
    # reports an empty rcPaint (Wine's RedrawWindow does nothing for a window
    # that is not visible).
    d += g.call("InvalidateRect", P("hp"), g.r1, 0) + g.call("BeginPaint", P("hp"), g.ps)
    d += g.chk("D: hidden: InvalidateRect left no update region",
               f"  mov eax, dword ptr [{g.ps + 8:#x}]{NL}  or eax, dword ptr [{g.ps + 12:#x}]{NL}"
               f"  or eax, dword ptr [{g.ps + 16:#x}]{NL}  or eax, dword ptr [{g.ps + 20:#x}]{NL}  cmp eax, 0{NL}")
    d += g.call("EndPaint", P("hp"), g.ps)
    d += g.call("ShowWindow", P("hp"), 5) + pump()
    d += paint_is("D: shown again", 3, 1, 0, 0, 100, 50)
    # Order (Wine's get_message: posted, then paint, then timers); WM_PAINT
    # stays until validated, PM_REMOVE notwithstanding.
    # (A 0 ms timer runs at Windows' minimum interval, USER_TIMER_MINIMUM,
    # 10 ms: it is due after the Sleep.)
    d += g.call("SetTimer", P("hp"), 1, 0, 0) + g.call("Sleep", 50)
    d += g.call("PostMessageA", P("hp"), 0x400, 0, 0) + g.call("InvalidateRect", P("hp"), 0, 0)
    d += peek(0) + g.chk("D: posted message first", g.mem(g.msg + 4, 0x400))
    d += peek(1)
    d += peek(0) + g.chk("D: then WM_PAINT", g.mem(g.msg + 4, 0xF))
    d += peek(1) + peek(0) + g.chk("D: PM_REMOVE leaves WM_PAINT queued", g.mem(g.msg + 4, 0xF))
    d += g.call("DispatchMessageA", g.msg) + peek(0)
    d += g.chk("D: validated: WM_TIMER comes next", g.mem(g.msg + 4, 0x113))
    d += paint_is("D: dispatched WM_PAINT", 4, 0, 0, 0, 100, 50)
    # DefWindowProc(WM_PAINT) validates.
    d += g.call("CreateWindowExA", 0, g.str("T"), g.str("q"), 0x90000000, 0, 0, 40, 40, 0, 0, EXE, 0)
    d += f"  mov dword ptr [{v['hq']:#x}], eax{NL}" + g.call("PeekMessageA", g.msg, P("hq"), 0, 0, 0)
    d += g.chk("D: DefWindowProc window: WM_PAINT due", g.mem(g.msg + 4, 0xF))
    d += g.call("DispatchMessageA", g.msg) + g.call("PeekMessageA", g.msg, P("hq"), 0, 0, 0)
    d += g.chk("D: DefWindowProc's WM_PAINT validated it", g.eq(0))
    # Growing a CS 0 window exposes the new strip; with CS_HREDRAW the
    # whole window is invalid (MSDN, Window Class Styles). The timer of
    # hp (still due) is dispatched by the pumps too.
    d += g.call("SetWindowPos", P("hp"), 0, 0, 0, 150, 50, 0x16) + pump()
    d += paint_is("D: grown, class style 0", 5, 1, 100, 0, 150, 50)
    d += g.call("CreateWindowExA", 0, g.str("T3"), g.str("h"), 0x90000000, 0, 0, 100, 50, 0, 0, EXE, 0)
    d += f"  mov dword ptr [{v['hp']:#x}], eax{NL}" + pump()
    d += g.call("SetWindowPos", P("hp"), 0, 0, 0, 120, 50, 0x16) + pump()
    d += paint_is("D: grown, CS_HREDRAW", 7, 1, 0, 0, 120, 50)
    g.d_code = d
    g.d_names, g.names = g.names[first_d:], g.names[:first_d]

    # mode V: wave output (MSDN waveOut*; Wine's winmm delivers WOM_OPEN and
    # WOM_CLOSE from waveOutOpen / waveOutClose and WOM_DONE from its device
    # thread).
    for h in (g.whdr1, g.whdr2):
        g.d.b[h - g.d.va0:h - g.d.va0 + 8] = struct.pack("<II", g.wdata, 400)
    first_v = len(g.names)
    W = lambda va: f"dword ptr [{va:#x}]"
    LOG = lambda i, k: f"dword ptr [{g.wlog + 12 * i + 4 * k:#x}]"
    w5 = g.call("GetCurrentThreadId") + f"  mov dword ptr [{g.wmain:#x}], eax{NL}"
    w5 += g.call("waveOutGetDevCapsA", 0, g.wcaps, 52) + g.chk("V: caps of device 0", g.eq(0))
    w5 += g.chk("V: caps: 2 channels", g.mem(g.wcaps + 44, 2, "word"))
    w5 += g.call("waveOutGetDevCapsA", 5, g.wcaps, 52) + g.chk("V: caps of device 5: BADDEVICEID", g.eq(2))
    w5 += g.call("waveOutOpen", 0, 0xFFFFFFFF, g.wfxbad, 0, 0, 1) + g.chk("V: non-PCM query: WAVERR_BADFORMAT", g.eq(32))
    w5 += g.call("waveOutOpen", 0, 0xFFFFFFFF, g.wfx8, 0, 0, 1) + g.chk("V: PCM query: supported", g.eq(0))
    w5 += g.call("waveOutOpen", g.hwo, 0xFFFFFFFF, g.wfx8, TEXT + WAVEPROC, 0x77, 0x30000)
    w5 += g.chk("V: open with CALLBACK_FUNCTION", g.eq(0))
    w5 += g.chk("V: WOM_OPEN from waveOutOpen", g.mem(g.wn, 1) + f"  jne 9f{NL}" +
                f"  cmp {LOG(0, 0)}, 0x3BB{NL}9:{NL}")
    w5 += g.chk("V: ... on the calling thread", f"  mov eax, {LOG(0, 2)}{NL}  cmp eax, {W(g.wmain)}{NL}")
    w5 += g.call("waveOutWrite", W(g.hwo), g.whdr1, 32) + g.chk("V: unprepared write: WAVERR_UNPREPARED", g.eq(34))
    w5 += g.call("waveOutPrepareHeader", W(g.hwo), g.whdr1, 32) + g.call("waveOutPrepareHeader", W(g.hwo), g.whdr2, 32)
    w5 += g.chk("V: prepared: WHDR_PREPARED", g.mem(g.whdr1 + 16, 2))
    w5 += g.call("waveOutWrite", W(g.hwo), g.whdr1, 32) + g.call("waveOutWrite", W(g.hwo), g.whdr2, 32)
    w5 += g.chk("V: written: WHDR_INQUEUE", g.mem(g.whdr2 + 16, 0x12))
    w5 += g.call("waveOutUnprepareHeader", W(g.hwo), g.whdr1, 32) + g.chk("V: unprepare while queued: STILLPLAYING", g.eq(33))
    w5 += g.call("waveOutClose", W(g.hwo)) + g.chk("V: close while queued: STILLPLAYING", g.eq(33))
    w5 += g.call("Sleep", 600)
    w5 += g.chk("V: both blocks returned in order", g.mem(g.wn, 3) + f"  jne 9f{NL}" +
                f"  cmp {LOG(1, 0)}, 0x3BD{NL}  jne 9f{NL}  cmp {LOG(1, 1)}, {g.whdr1:#x}{NL}  jne 9f{NL}"
                f"  cmp {LOG(2, 0)}, 0x3BD{NL}  jne 9f{NL}  cmp {LOG(2, 1)}, {g.whdr2:#x}{NL}9:{NL}")
    w5 += g.chk("V: WOM_DONE from another thread", f"  mov eax, {LOG(1, 2)}{NL}  cmp eax, {W(g.wmain)}{NL}  setne al{NL}  cmp al, 1{NL}")
    w5 += g.chk("V: done: WHDR_DONE, not in queue", g.mem(g.whdr1 + 16, 0x3))
    # waveOutReset returns the queued block before it returns.
    w5 += g.call("waveOutWrite", W(g.hwo), g.whdr1, 32) + g.call("waveOutReset", W(g.hwo))
    w5 += f"  mov eax, {W(g.wn)}{NL}  mov dword ptr [{g.wsnap:#x}], eax{NL}"
    w5 += g.chk("V: waveOutReset returned the block first", g.mem(g.wsnap, 4) + f"  jne 9f{NL}" + f"  cmp {LOG(3, 1)}, {g.whdr1:#x}{NL}9:{NL}")
    w5 += g.call("waveOutUnprepareHeader", W(g.hwo), g.whdr1, 32) + g.call("waveOutUnprepareHeader", W(g.hwo), g.whdr2, 32)
    w5 += g.chk("V: unprepared", g.mem(g.whdr1 + 16, 1))
    w5 += g.call("waveOutClose", W(g.hwo)) + g.chk("V: close", g.eq(0))
    w5 += g.chk("V: WOM_CLOSE from waveOutClose", f"  cmp {LOG(4, 0)}, 0x3BC{NL}")
    w5 += g.call("waveOutGetID", W(g.hwo), g.wsnap) + g.chk("V: closed handle: MMSYSERR_INVALHANDLE", g.eq(5))
    g.v_code = w5
    g.v_names, g.names = g.names[first_v:], g.names[:first_v]

    # mode O: overlapped I/O (MSDN ReadFile / WriteFile / CreateIoCompletionPort;
    # "Synchronous and Asynchronous I/O"). File C:\\o.bin in the per-user tree.
    first_o = len(g.names)
    OV = lambda off, hi=0, ev=0: (f"  mov dword ptr [{g.ovl:#x}], 0{NL}  mov dword ptr [{g.ovl + 4:#x}], 0{NL}"
                                  f"  mov dword ptr [{g.ovl + 8:#x}], {off:#x}{NL}"
                                  f"  mov dword ptr [{g.ovl + 12:#x}], {hi:#x}{NL}"
                                  f"  mov dword ptr [{g.ovl + 16:#x}], {ev}{NL}")
    M = lambda va: f"dword ptr [{va:#x}]"
    gq = lambda t: g.call("GetQueuedCompletionStatus", M(g.oport), g.obytes, g.okey, g.opovl, t)
    o = g.call("CreateFileA", g.str("C:\\o.bin"), 0xC0000000, 0, 0, 2, 0x40000000, 0)
    o += f"  mov dword ptr [{g.ofile:#x}], eax{NL}" + g.chk("O: CreateFileA(FILE_FLAG_OVERLAPPED)", "  cmp eax, -1\n  setne al\n  cmp al, 1\n")
    o += g.call("CreateIoCompletionPort", M(g.ofile), 0, 0x55, 0) + f"  mov dword ptr [{g.oport:#x}], eax{NL}"
    o += g.chk("O: file associated with a new port", g.nonzero())
    o += g.call("CreateIoCompletionPort", M(g.ofile), M(g.oport), 0x66, 0)
    o += g.chk("O: a second association fails", g.eq(0)) + g.gle("O: ... with ERROR_INVALID_PARAMETER", 87)
    # Pending write of 8 bytes at offset 4; its packet carries (8, key, &ovl).
    o += OV(4) + g.call("WriteFile", M(g.ofile), g.str("ABCDEFGH"), 8, g.obytes, g.ovl)
    o += g.chk("O: overlapped WriteFile returns FALSE", g.eq(0)) + g.gle("O: ... ERROR_IO_PENDING", 997)
    o += gq(1000) + g.chk("O: GetQueuedCompletionStatus: TRUE", g.eq(1))
    o += g.chk("O: packet bytes 8", g.mem(g.obytes, 8)) + g.chk("O: packet key 55h", g.mem(g.okey, 0x55))
    o += g.chk("O: packet OVERLAPPED", g.mem(g.opovl, g.ovl))
    o += g.chk("O: Internal STATUS_SUCCESS", g.mem(g.ovl, 0)) + g.chk("O: InternalHigh 8", g.mem(g.ovl + 4, 8))
    # Read 12 from offset 0: the 4 bytes never written read as zeros.
    o += OV(0) + g.call("ReadFile", M(g.ofile), g.iobuf, 12, g.obytes, g.ovl)
    o += g.chk("O: overlapped ReadFile pending", g.eq(0)) + gq(1000)
    o += g.chk("O: read packet: 12 bytes", g.mem(g.obytes, 12))
    o += g.chk("O: read data: 00 00 00 00 'ABCD'", g.mem(g.iobuf, 0) + f"  jne 9f{NL}" + g.mem(g.iobuf + 4, 0x44434241) + f"9:{NL}")
    o += g.chk("O: read data: 'EFGH'", g.mem(g.iobuf + 8, 0x48474645))
    # Offset FFFFFFFFh:FFFFFFFFh appends (12 -> 14 bytes).
    o += OV(0xFFFFFFFF, 0xFFFFFFFF) + g.call("WriteFile", M(g.ofile), g.str("XY"), 2, g.obytes, g.ovl) + gq(1000)
    o += OV(12) + g.call("ReadFile", M(g.ofile), g.iobuf, 8, g.obytes, g.ovl) + gq(1000)
    o += g.chk("O: append wrote at the end", g.mem(g.obytes, 2) + f"  jne 9f{NL}" + g.mem(g.iobuf, 0x5958, "word") + f"9:{NL}")
    # A read at the end of the file: FALSE, ERROR_HANDLE_EOF, no packet.
    o += OV(100) + g.call("ReadFile", M(g.ofile), g.iobuf, 4, g.obytes, g.ovl)
    o += g.chk("O: read past the end fails", g.eq(0)) + g.gle("O: ... ERROR_HANDLE_EOF", 38)
    o += gq(0) + g.chk("O: ... and queues no packet", g.eq(0)) + g.gle("O: ... (WAIT_TIMEOUT)", 258)
    # hEvent with its low bit set: the event is set, no packet is queued.
    o += g.call("CreateEventA", 0, 1, 0, 0) + f"  mov dword ptr [{g.oev:#x}], eax{NL}  or eax, 1{NL}"
    o += f"  push eax{NL}  pop esi{NL}" + OV(0).replace(f"[{g.ovl + 16:#x}], 0", f"[{g.ovl + 16:#x}], esi")
    o += g.call("WriteFile", M(g.ofile), g.str("Z"), 1, g.obytes, g.ovl)
    o += g.call("WaitForSingleObject", M(g.oev), 0) + g.chk("O: hEvent set", g.eq(0))
    o += gq(0) + g.chk("O: low bit: no packet", g.eq(0))
    o += g.call("CloseHandle", M(g.ofile))
    # A synchronous handle with an OVERLAPPED: at the offset, TRUE, and its
    # file pointer moves past the transfer.
    o += g.call("CreateFileA", g.str("C:\\s.bin"), 0xC0000000, 0, 0, 2, 0, 0) + f"  mov dword ptr [{g.ofile:#x}], eax{NL}"
    o += OV(2) + g.call("WriteFile", M(g.ofile), g.str("abc"), 3, g.obytes, g.ovl)
    o += g.chk("O: synchronous handle: TRUE", g.eq(1)) + g.chk("O: ... 3 bytes written", g.mem(g.obytes, 3))
    o += g.call("SetFilePointer", M(g.ofile), 0, 0, 1) + g.chk("O: ... file pointer at 5", g.eq(5))
    g.o_code = o

    # mode F: a visible maximized popup (WS_POPUP | WS_VISIBLE | WS_MAXIMIZE)
    # covers the screen; 800 rounds of PeekMessage/DispatchMessage, sleeping
    # 10 ms when the queue is empty (~8 s; TEST_INPUT is injected by the
    # pump), keeping the lParams of the first 4 WM_LBUTTONDOWNs; prints the
    # work area (the client) and them. Every round counts, so a runtime that
    # floods the queue (an unvalidated WM_PAINT) ends the loop, not the test.
    f = mkclass + win("f", 0x91000000, 0, 0, 100, 100) + f"  mov dword ptr [{v['hwnd']:#x}], eax{NL}"
    f += g.call("ShowWindow", P("hwnd"), 5) + "  mov esi, 800\n3:\n"
    f += g.call("PeekMessageA", g.msg, 0, 0, 0, 1) + f"""  test eax, eax
  jz 4f
  cmp dword ptr [{g.msg + 4:#x}], 0x201
  jne 5f
  mov ecx, dword ptr [{v['cn']:#x}]
  cmp ecx, 4
  jae 5f
  mov eax, dword ptr [{g.msg + 12:#x}]
  mov dword ptr [{g.clicks:#x}+ecx*4], eax
  inc dword ptr [{v['cn']:#x}]
5:
""" + g.call("DispatchMessageA", g.msg) + "  jmp 6f\n4:\n" + g.call("Sleep", 10)
    f += "6:\n  dec esi\n  jnz 3b\n"
    f += g.call("SystemParametersInfoA", 0x30, 0, g.rect, 0)  # SPI_GETWORKAREA
    f += g.call("wsprintfA", g.out, g.str("R%X,%X C%X:%X,%X,%X,%X\n"), f"dword ptr [{g.rect + 8:#x}]",
                f"dword ptr [{g.rect + 12:#x}]", P("cn"), *(f"dword ptr [{g.clicks + 4 * i:#x}]" for i in range(4)))
    g.f_code = f + "  add esp, 36\n" + g.call("OutputDebugStringA", g.out) + g.call("ExitProcess", 0)
    g.o_names, g.names = g.names[first_o:], g.names[:first_o]

    # mode N: Winsock 1.1 sockets on loopback (patch 0023). Expected values:
    # MSDN's socket, bind, getsockname, getpeername, setsockopt, ioctlsocket,
    # listen, accept, connect, send, recv, sendto, recvfrom and select pages,
    # and the Winsock 1.1 specification: errors are WSA codes (WSAGetLastError);
    # a non-blocking connect returns WSAEWOULDBLOCK and completes in select's
    # writefds or fails in its exceptfds; an accepted socket has the listening
    # socket's properties; a datagram longer than the buffer fills it and fails
    # with WSAEMSGSIZE; getsockname of an unbound socket and listen on one are
    # WSAEINVAL, as is select with no socket in any set; sendto a broadcast
    # address without SO_BROADCAST is WSAEACCES.
    first_n = len(g.names)
    W = lambda k: f"dword ptr [{g.nv[k]:#x}]"
    SA = lambda va, port_from=None, addr=0x0100007F: (
        f"  mov word ptr [{va:#x}], 2{NL}  mov word ptr [{va + 2:#x}], 0{NL}  mov dword ptr [{va + 4:#x}], {addr:#x}{NL}"
        + (f"  mov ax, word ptr [{port_from + 2:#x}]{NL}  mov word ptr [{va + 2:#x}], ax{NL}" if port_from else ""))
    LEN = lambda: f"  mov dword ptr [{g.nv['len']:#x}], 16{NL}"
    ERR = lambda name, code: g.call(111) + g.chk(name, g.eq(code))
    FD = lambda va, *keys: f"  mov dword ptr [{va:#x}], {len(keys)}{NL}" + "".join(
        f"  mov eax, {W(k)}{NL}  mov dword ptr [{va + 4 + 4 * i:#x}], eax{NL}" for i, k in enumerate(keys))
    SOCK = lambda k, t, p: g.call(23, 2, t, p) + f"  mov {W(k)}, eax{NL}"
    NB = lambda k: f"  mov dword ptr [{g.nv['one']:#x}], 1{NL}" + g.call(12, W(k), 0x8004667E, g.nv["one"])
    n = ""
    # -- socket(): only AF_INET stream and datagram sockets.
    n += SOCK("u1", 2, 0) + g.chk("N: socket(AF_INET, SOCK_DGRAM)", "  cmp eax, -1\n  setne al\n  cmp al, 1\n")
    n += g.call(23, 23, 2, 0) + g.chk("N: socket(AF_INET6) fails", g.eq(-1)) + ERR("N: ... WSAEAFNOSUPPORT", 10047)
    n += g.call(23, 2, 3, 0) + g.chk("N: socket(SOCK_RAW) fails", g.eq(-1)) + ERR("N: ... WSAESOCKTNOSUPPORT", 10044)
    n += g.call(23, 2, 1, 17) + g.chk("N: a stream socket with IPPROTO_UDP fails", g.eq(-1)) + ERR("N: ... WSAEPROTONOSUPPORT", 10043)
    # -- names: unbound, then bound to 127.0.0.1 on a port of the system's choice.
    n += LEN() + g.call(6, W("u1"), g.nsa1, g.nv["len"]) + g.chk("N: getsockname of an unbound socket fails", g.eq(-1))
    n += ERR("N: ... WSAEINVAL", 10022)
    n += SA(g.nsa1) + g.call(2, W("u1"), g.nsa1, 16) + g.chk("N: bind(127.0.0.1:0)", g.eq(0))
    n += LEN() + g.call(6, W("u1"), g.nsa1, g.nv["len"]) + g.chk("N: getsockname", g.eq(0))
    n += g.chk("N: ... family AF_INET (16 bits, no sin_len)", g.mem(g.nsa1, 2, "word"))
    n += g.chk("N: ... address 127.0.0.1", g.mem(g.nsa1 + 4, 0x0100007F)) + g.chk("N: ... length 16", g.mem(g.nv["len"], 16))
    n += g.chk("N: ... a port was chosen", f"  cmp word ptr [{g.nsa1 + 2:#x}], 0{NL}  setne al{NL}  cmp al, 1{NL}")
    n += g.call(2, W("u1"), g.nsa1, 8) + g.chk("N: bind with a short address fails", g.eq(-1)) + ERR("N: ... WSAEFAULT", 10014)
    # -- datagrams between two sockets.
    n += SOCK("u2", 2, 17) + SA(g.nsa2) + g.call(2, W("u2"), g.nsa2, 16)
    # a receive never waits more than 1 s (SO_RCVTIMEO, milliseconds), so a
    # broken socket fails a check instead of hanging the test.
    n += f"  mov dword ptr [{g.nv['x']:#x}], 1000{NL}" + g.call(21, W("u2"), 0xFFFF, 0x1006, g.nv["x"], 4)
    n += g.chk("N: setsockopt(SO_RCVTIMEO, 1000 ms)", g.eq(0))
    n += LEN() + g.call(17, W("u2"), g.nbuf, 64, 0, g.nfrom, g.nv["len"])
    n += g.chk("N: a blocking receive with nothing to read times out", g.eq(-1))
    n += ERR("N: ... with WSAETIMEDOUT", 10060)
    n += LEN() + g.call(6, W("u2"), g.nsa2, g.nv["len"])
    n += g.call(20, W("u1"), g.str("hello"), 5, 0, g.nsa2, 16) + g.chk("N: sendto: 5 bytes", g.eq(5))
    n += LEN() + g.call(17, W("u2"), g.nbuf, 64, 0, g.nfrom, g.nv["len"]) + g.chk("N: recvfrom: 5 bytes", g.eq(5))
    n += g.chk("N: ... the data", g.mem(g.nbuf, 0x6C6C6568))
    n += g.chk("N: ... from AF_INET", g.mem(g.nfrom, 2, "word"))
    n += g.chk("N: ... from the sender's port", f"  mov ax, word ptr [{g.nsa1 + 2:#x}]{NL}  cmp word ptr [{g.nfrom + 2:#x}], ax{NL}")
    n += g.call(20, W("u1"), g.str("ABCDEFGH"), 8, 0, g.nsa2, 16)
    n += LEN() + g.call(17, W("u2"), g.nbuf, 4, 0, g.nfrom, g.nv["len"])
    n += g.chk("N: a datagram longer than the buffer fails", g.eq(-1)) + ERR("N: ... WSAEMSGSIZE", 10040)
    n += g.chk("N: ... and the buffer holds its start", g.mem(g.nbuf, 0x44434241))
    n += NB("u2") + g.chk("N: ioctlsocket(FIONBIO)", g.eq(0))
    n += LEN() + g.call(17, W("u2"), g.nbuf, 64, 0, g.nfrom, g.nv["len"]) + g.chk("N: non-blocking recvfrom with nothing", g.eq(-1))
    n += ERR("N: ... WSAEWOULDBLOCK", 10035)
    n += g.call(12, W("u2"), 0x12345678, g.nv["one"]) + g.chk("N: an unknown ioctlsocket command fails", g.eq(-1))
    n += ERR("N: ... WSAEINVAL", 10022)
    # -- broadcast needs SO_BROADCAST; options.
    n += SA(g.nbc, g.nsa2, 0xFFFFFFFF) + g.call(20, W("u1"), g.str("x"), 1, 0, g.nbc, 16)
    n += g.chk("N: sendto the broadcast address without SO_BROADCAST fails", g.eq(-1)) + ERR("N: ... WSAEACCES", 10013)
    n += f"  mov dword ptr [{g.nv['one']:#x}], 1{NL}" + g.call(21, W("u1"), 0xFFFF, 0x20, g.nv["one"], 4)
    n += g.chk("N: setsockopt(SO_BROADCAST)", g.eq(0))
    n += g.call(21, W("u1"), 0xFFFF, 0x4, g.nv["one"], 4) + g.chk("N: setsockopt(SO_REUSEADDR)", g.eq(0))
    # broadcast from an unbound socket (the system binds it to every address,
    # as the game's are); a socket bound to 127.0.0.1 has no broadcast route.
    n += SOCK("u4", 2, 0) + g.call(21, W("u4"), 0xFFFF, 0x20, g.nv["one"], 4)
    # A broadcast can fail for a moment when the host's network changes (seen
    # rarely on Wi-Fi); up to 3 attempts, 50 ms apart. Without SO_BROADCAST it
    # fails every time (WSAEACCES).
    n += f"  mov dword ptr [{g.nv['x']:#x}], 3{NL}8:{NL}" + g.call(20, W("u4"), g.str("x"), 1, 0, g.nbc, 16)
    n += f"  cmp eax, 1{NL}  je 7f{NL}" + g.call("Sleep", 50) + f"  dec dword ptr [{g.nv['x']:#x}]{NL}  jnz 8b{NL}  xor eax, eax{NL}7:{NL}"
    n += g.chk("N: ... then sendto the broadcast address succeeds", g.eq(1))
    n += g.call(3, W("u4"))
    n += SOCK("u3", 2, 0) + g.call(21, W("u3"), 0xFFFF, 0x4, g.nv["one"], 4) + g.call(2, W("u3"), g.nsa1, 16)
    n += g.chk("N: with SO_REUSEADDR a second socket binds the same port", g.eq(0)) + g.call(3, W("u3"))
    n += g.call(21, W("u1"), 0xFFFF, 0x1234, g.nv["one"], 4) + g.chk("N: an unknown option fails", g.eq(-1))
    n += ERR("N: ... WSAENOPROTOOPT", 10042)
    n += g.call(21, W("u1"), 99, 1, g.nv["one"], 4) + g.chk("N: an unknown level fails", g.eq(-1)) + ERR("N: ... WSAEINVAL", 10022)
    n += g.call(13, W("u1"), 1) + g.chk("N: listen on a datagram socket fails", g.eq(-1)) + ERR("N: ... WSAEOPNOTSUPP", 10045)
    # -- a TCP connection: non-blocking connect, select, accept, data, close.
    n += SOCK("ls", 1, 6) + g.call(13, W("ls"), 5) + g.chk("N: listen on an unbound socket fails", g.eq(-1))
    n += ERR("N: ... WSAEINVAL", 10022)
    n += SA(g.nsa3) + g.call(2, W("ls"), g.nsa3, 16) + g.call(13, W("ls"), 5) + g.chk("N: listen", g.eq(0))
    n += LEN() + g.call(6, W("ls"), g.nsa3, g.nv["len"])
    n += NB("ls") + LEN() + g.call(1, W("ls"), g.nsa4, g.nv["len"])
    n += g.chk("N: accept with no connection pending fails", g.eq(-1)) + ERR("N: ... WSAEWOULDBLOCK", 10035)
    n += SOCK("cs", 1, 0) + NB("cs") + g.call(4, W("cs"), g.nsa3, 16)
    n += g.chk("N: a non-blocking connect returns SOCKET_ERROR", g.eq(-1))
    n += ERR("N: ... WSAEWOULDBLOCK (the connect in progress)", 10035)
    n += FD(g.nfw, "cs") + FD(g.nfe, "cs") + g.call(18, 0, 0, g.nfw, g.nfe, g.ntv1)
    n += g.chk("N: select: the connect completes", g.eq(1))
    n += g.chk("N: ... in writefds", g.mem(g.nfw, 1)) + g.chk("N: ... not in exceptfds", g.mem(g.nfe, 0))
    n += FD(g.nfr, "ls") + g.call(18, 0, g.nfr, 0, 0, g.ntv1)
    n += g.chk("N: select: the listening socket is readable", g.eq(1)) + g.chk("N: ... readfds keeps it", g.mem(g.nfr, 1))
    n += LEN() + g.call(1, W("ls"), g.nsa4, g.nv["len"]) + f"  mov {W('as')}, eax{NL}"
    n += g.chk("N: accept", "  cmp eax, -1\n  setne al\n  cmp al, 1\n") + g.chk("N: ... address length 16", g.mem(g.nv["len"], 16))
    n += f"  mov dword ptr [{g.nv['x']:#x}], 1000{NL}" + g.call(21, W("as"), 0xFFFF, 0x1006, g.nv["x"], 4)
    n += LEN() + g.call(6, W("cs"), g.nsa5, g.nv["len"])
    n += g.chk("N: ... the connecting socket's port", f"  mov ax, word ptr [{g.nsa5 + 2:#x}]{NL}  cmp word ptr [{g.nsa4 + 2:#x}], ax{NL}")
    n += LEN() + g.call(5, W("as"), g.nsa4, g.nv["len"]) + g.chk("N: getpeername", g.eq(0))
    n += g.chk("N: ... the peer's port", f"  mov ax, word ptr [{g.nsa5 + 2:#x}]{NL}  cmp word ptr [{g.nsa4 + 2:#x}], ax{NL}")
    n += g.call(21, W("cs"), 6, 1, g.nv["one"], 4) + g.chk("N: setsockopt(TCP_NODELAY)", g.eq(0))
    n += f"  mov dword ptr [{g.nv['lin']:#x}], 1{NL}" + g.call(21, W("as"), 0xFFFF, 0x80, g.nv["lin"], 4)
    n += g.chk("N: setsockopt(SO_LINGER) with Winsock 1.1's 16-bit linger", g.eq(0))
    n += g.call(19, W("cs"), g.str("ping"), 4, 0) + g.chk("N: send: 4 bytes", g.eq(4))
    n += FD(g.nfr, "as") + g.call(18, 0, g.nfr, 0, 0, g.ntv1) + g.chk("N: select: data to read", g.eq(1))
    n += g.call(12, W("as"), 0x4004667F, g.nv["x"]) + g.chk("N: ioctlsocket(FIONREAD)", g.eq(0)) + g.chk("N: ... 4 bytes", g.mem(g.nv["x"], 4))
    n += g.call(16, W("as"), g.nbuf, 64, 0) + g.chk("N: recv: 4 bytes", g.eq(4)) + g.chk("N: ... the data", g.mem(g.nbuf, 0x676E6970))
    n += g.call("GetTickCount") + f"  mov dword ptr [{g.nv['t0']:#x}], eax{NL}"
    n += g.call(16, W("as"), g.nbuf, 64, 0) + f"  mov dword ptr [{g.nv['lin']:#x}], eax{NL}"
    n += g.call("GetTickCount") + f"  sub eax, dword ptr [{g.nv['t0']:#x}]{NL}"
    n += g.chk("N: the accepted socket is non-blocking like its listener (no wait)", f"  cmp eax, 500{NL}  setb al{NL}  cmp al, 1{NL}")
    n += f"  mov eax, dword ptr [{g.nv['lin']:#x}]{NL}" + g.chk("N: ... SOCKET_ERROR", g.eq(-1))
    n += ERR("N: ... WSAEWOULDBLOCK at once, not a wait", 10035)
    n += g.call(3, W("cs")) + g.chk("N: closesocket", g.eq(0))
    n += FD(g.nfr, "as") + g.call(18, 0, g.nfr, 0, 0, g.ntv1) + g.chk("N: select: the closed connection is readable", g.eq(1))
    n += g.call(16, W("as"), g.nbuf, 64, 0) + g.chk("N: recv after the peer closed: 0", g.eq(0))
    n += g.call(3, W("cs")) + g.chk("N: closesocket twice fails", g.eq(-1)) + ERR("N: ... WSAENOTSOCK", 10038)
    # -- a refused connect: exceptfds, never writefds.
    n += g.call(3, W("ls")) + SOCK("c2", 1, 0) + NB("c2") + g.call(4, W("c2"), g.nsa3, 16)
    n += g.chk("N: a refused non-blocking connect returns SOCKET_ERROR", g.eq(-1)) + ERR("N: ... WSAEWOULDBLOCK", 10035)
    n += FD(g.nfw, "c2") + FD(g.nfe, "c2") + g.call(18, 0, 0, g.nfw, g.nfe, g.ntv1)
    n += g.chk("N: select: the failure is reported", g.eq(1))
    n += g.chk("N: ... in exceptfds", g.mem(g.nfe, 1)) + g.chk("N: ... not in writefds", g.mem(g.nfw, 0))
    # -- select's own rules.
    n += g.call(18, 0, 0, 0, 0, g.ntv1) + g.chk("N: select with no sets fails", g.eq(-1)) + ERR("N: ... WSAEINVAL", 10022)
    n += FD(g.nfr, "u1") + g.call(18, 0, g.nfr, 0, 0, g.ntv0) + g.chk("N: select with nothing ready returns 0", g.eq(0))
    n += g.chk("N: ... and empties the set", g.mem(g.nfr, 0))
    n += f"  mov dword ptr [{g.nfr:#x}], 1{NL}  mov dword ptr [{g.nfr + 4:#x}], 0xDEAD{NL}" + g.call(18, 0, g.nfr, 0, 0, g.ntv0)
    n += g.chk("N: select with an invalid socket fails", g.eq(-1)) + ERR("N: ... WSAENOTSOCK", 10038)
    g.n_code = n
    g.n_names, g.names = g.names[first_n:], g.names[:first_n]

    # modes B and R: Warcraft III's LAN discovery broadcast (patch 0025). A
    # datagram to 255.255.255.255:6112 goes to each local network's broadcast
    # address and arrives at a socket bound to 0.0.0.0:6112 on this host (a
    # broadcast is delivered to the sender's own sockets too: BSD's and
    # Windows' IP). Mode R runs with 255.255.255.255 refused
    # (<ID>_TEST_NO_LIMITED_BROADCAST), as macOS refuses it when a VPN is the
    # primary service (EADDRNOTAVAIL): the 6112 broadcast still arrives, and
    # one to another port, which is not rewritten, fails with
    # WSAEADDRNOTAVAIL (MSDN's sendto). The receiver reads up to 8 datagrams
    # for its own: another host may be announcing a game.
    def lan_mode(prefix, refused):
        bv = {k: g.d.put(b"\0" * 4) for k in ("rb", "s", "len", "one", "x", "n")}
        bsa, bdst, bfrom, bbuf = (g.d.put(b"\0" * 16) for _ in range(4))
        V = lambda k: f"dword ptr [{bv[k]:#x}]"
        SAB = lambda va, port_be, addr: (f"  mov word ptr [{va:#x}], 2{NL}  mov word ptr [{va + 2:#x}], {port_be:#x}{NL}"
                                         f"  mov dword ptr [{va + 4:#x}], {addr:#x}{NL}")
        first = len(g.names)
        b = g.call(23, 2, 2, 0) + f"  mov {V('rb')}, eax{NL}"
        b += f"  mov dword ptr [{bv['one']:#x}], 1{NL}" + g.call(21, V("rb"), 0xFFFF, 0x4, bv["one"], 4)
        b += SAB(bsa, 0xE017, 0) + g.call(2, V("rb"), bsa, 16) + g.chk(f"{prefix}: bind 0.0.0.0:6112", g.eq(0))
        b += f"  mov dword ptr [{bv['x']:#x}], 1000{NL}" + g.call(21, V("rb"), 0xFFFF, 0x1006, bv["x"], 4)
        b += g.call(23, 2, 2, 0) + f"  mov {V('s')}, eax{NL}" + g.call(21, V("s"), 0xFFFF, 0x20, bv["one"], 4)
        b += SAB(bdst, 0xE017, 0xFFFFFFFF) + g.call(20, V("s"), g.str("B25!"), 4, 0, bdst, 16)
        b += g.chk(f"{prefix}: sendto 255.255.255.255:6112 sends the datagram", g.eq(4))
        b += f"  mov dword ptr [{bv['n']:#x}], 8{NL}9:{NL}  mov dword ptr [{bv['len']:#x}], 16{NL}"
        b += g.call(17, V("rb"), bbuf, 64, 0, bfrom, bv["len"])
        b += (f"  cmp eax, 4{NL}  jne 8f{NL}  cmp dword ptr [{bbuf:#x}], 0x21353242{NL}  je 7f{NL}"
              f"8:{NL}  cmp eax, -1{NL}  je 6f{NL}  dec dword ptr [{bv['n']:#x}]{NL}  jnz 9b{NL}"
              f"6:{NL}  xor eax, eax{NL}  jmp 5f{NL}7:{NL}  mov eax, 1{NL}5:{NL}")
        b += g.chk(f"{prefix}: ... and arrives at 0.0.0.0:6112 on this host", g.eq(1))
        b += SAB(bdst, 0xE117, 0xFFFFFFFF) + g.call(20, V("s"), g.str("x"), 1, 0, bdst, 16)
        if refused:
            b += g.chk("R: a broadcast to another port is not rewritten: refused", g.eq(-1))
            b += g.call(111) + g.chk("R: ... with WSAEADDRNOTAVAIL", g.eq(10049))
        else:
            b += g.chk("B: a broadcast to another port is sent as before", g.eq(1))
        b += g.call(3, V("s")) + g.call(3, V("rb"))
        names, g.names = g.names[first:], g.names[:first]
        return b, names

    g.b_code, g.b_names = lan_mode("B", False)
    g.r_code, g.r_names = lan_mode("R", True)

    # mode Q: completion ports on sockets (patch 0024), as the game hosts and
    # joins: mswsock's AcceptEx and GetAcceptExSockaddrs, sockets associated
    # with a port, overlapped ReadFile, and closing with operations pending.
    # Expected values: Wine's conformance tests, which run on Windows
    # (ws2_32/tests/sock.c: test_completion_port, test_AcceptEx), and MSDN:
    # AcceptEx returns FALSE with ERROR_IO_PENDING and OVERLAPPED.Internal
    # STATUS_PENDING; its checks fail with WSA_INVALID_PARAMETER (no
    # OVERLAPPED), WSAEINVAL (the listening socket is not listening),
    # WSAENOTSOCK (no accepting socket); the remote address it reports is the
    # connecting socket's name; a completion carries the association's key,
    # the OVERLAPPED and the byte count, and Internal/InternalHigh the status
    # and count; a graceful close completes a read with 0 bytes and TRUE; a
    # reset one with FALSE, ERROR_NETNAME_DELETED; closing a socket ends its
    # pending operations (and an AcceptEx's on its accepting socket) with
    # FALSE, ERROR_OPERATION_ABORTED, Internal STATUS_CANCELLED, exactly once;
    # a wait that times out is FALSE, WAIT_TIMEOUT, *overlapped NULL, bytes
    # and key untouched; an event with its low bit set gets no packet.
    # GetAcceptExSockaddrs: each area is the address's length (an int) then
    # the address (Wine's layout and pointer calculation).
    first_q = len(g.names)
    QW = lambda k: f"dword ptr [{g.qv[k]:#x}]"
    ST = lambda k: f"  mov {QW(k)}, eax{NL}"
    OV = g.qovl
    NOTERR = "  cmp eax, -1\n  setne al\n  cmp al, 1\n"
    WERR = lambda name, code: g.call(111) + g.chk(name, g.eq(code))
    SOCKQ = lambda k: g.call(23, 2, 1, 0) + ST(k)
    LOOP = lambda va: (f"  mov word ptr [{va:#x}], 2{NL}  mov word ptr [{va + 2:#x}], 0{NL}"
                       f"  mov dword ptr [{va + 4:#x}], 0x0100007F{NL}")
    NAME = lambda k, va: f"  mov {QW('lin')}, 16{NL}" + g.call(6, QW(k), va, g.qv["lin"])
    PORTEQ = lambda a, b: f"  mov ax, word ptr [{a:#x}]{NL}  cmp ax, word ptr [{b:#x}]{NL}"
    ASSOC = lambda k, key: g.call("CreateIoCompletionPort", QW(k), QW("port"), key, 0)
    AE = lambda l, a, ovl: g.call("AcceptEx", l, a, g.qab, 0, 32, 32, g.qv["abytes"], ovl)
    RF = lambda k, buf, n, ovl: g.call("ReadFile", QW(k), buf, n, 0, ovl)

    def GQ(t):
        return (f"  mov {QW('bytes')}, 0xDEADBEEF{NL}  mov {QW('key')}, 0xDEADBEEF{NL}"
                f"  mov {QW('ovl')}, 0xDEADBEEF{NL}"
                + g.call("GetQueuedCompletionStatus", QW("port"), g.qv["bytes"], g.qv["key"], g.qv["ovl"], t))

    def PACKET(name, ok, key, ovl, nbytes, err=None):  # after GQ
        r = g.chk(f"{name}: {'TRUE' if ok else 'FALSE'}", g.eq(1 if ok else 0))
        if err is not None:
            r += g.gle(f"{name}: error {err}", err)
        return (r + g.chk(f"{name}: key {key:X}h", g.mem(g.qv["key"], key))
                + g.chk(f"{name}: its OVERLAPPED", g.mem(g.qv["ovl"], ovl))
                + g.chk(f"{name}: {nbytes} bytes", g.mem(g.qv["bytes"], nbytes)))

    def NONE(name):
        return (GQ(200) + g.chk(f"{name}: no packet", g.eq(0)) + g.gle(f"{name}: ... WAIT_TIMEOUT", 258)
                + g.chk(f"{name}: ... *overlapped NULL", g.mem(g.qv["ovl"], 0))
                + g.chk(f"{name}: ... bytes untouched", g.mem(g.qv["bytes"], 0xDEADBEEF))
                + g.chk(f"{name}: ... key untouched", g.mem(g.qv["key"], 0xDEADBEEF)))

    def STATUS(name, ovl, status, nbytes):
        return (g.chk(f"{name}: Internal {status:08X}h", g.mem(ovl, status))
                + g.chk(f"{name}: InternalHigh {nbytes}", g.mem(ovl + 4, nbytes)))

    q = ""
    # -- mswsock.dll through the loader, as the game finds it.
    q += g.call("LoadLibraryA", g.str("mswsock.dll")) + ST("mod") + g.chk("Q: LoadLibraryA(mswsock.dll)", g.nonzero())
    for fn in ("AcceptEx", "GetAcceptExSockaddrs"):
        q += g.call("GetProcAddress", QW("mod"), g.str(fn))
        q += g.chk(f"Q: GetProcAddress({fn}) is the imported {fn}",
                   f"  cmp eax, dword ptr [{g.iat[('mswsock.dll', fn)]:#x}]{NL}")
    # -- one handle namespace: a socket is a kernel handle.
    q += g.call("CreateEventA", 0, 1, 0, 0) + ST("e2") + g.call(23, 2, 2, 0) + ST("S") + g.chk("Q: socket", NOTERR)
    q += g.chk("Q: a socket's handle is not an event's", f"  mov eax, {QW('S')}{NL}  cmp eax, {QW('e2')}{NL}  setne al{NL}  cmp al, 1{NL}")
    q += LOOP(g.qsa2) + g.call(2, QW("S"), g.qsa2, 16) + NAME("S", g.qsa2)
    q += g.call("CloseHandle", QW("e2")) + NAME("S", g.qsa2) + g.chk("Q: closing the event leaves the socket", g.eq(0))
    q += g.call("CloseHandle", QW("S")) + g.chk("Q: CloseHandle closes a socket", g.eq(1))
    q += g.call(3, QW("S")) + g.chk("Q: ... closesocket then fails", g.eq(-1)) + WERR("Q: ... WSAENOTSOCK", 10038)
    q += g.call(23, 2, 2, 0) + ST("S") + g.call(2, QW("S"), g.qsa2, 16)
    q += g.chk("Q: ... and its UDP port is free again", g.eq(0)) + g.call(3, QW("S"))
    # -- a listening socket on a port.
    q += g.call("CreateIoCompletionPort", 0xFFFFFFFF, 0, 0, 0) + ST("port")
    q += SOCKQ("L") + LOOP(g.qsaL) + g.call(2, QW("L"), g.qsaL, 16) + g.call(13, QW("L"), 5) + NAME("L", g.qsaL)
    q += ASSOC("L", 0x11) + g.chk("Q: CreateIoCompletionPort(listening socket, port, 11h)", f"  cmp eax, {QW('port')}{NL}")
    q += ASSOC("L", 0x12) + g.chk("Q: a second association fails", g.eq(0)) + g.gle("Q: ... ERROR_INVALID_PARAMETER", 87)
    # -- AcceptEx's own checks.
    q += SOCKQ("A1") + SOCKQ("A2")
    q += AE(QW("L"), QW("A1"), 0) + g.chk("Q: AcceptEx without an OVERLAPPED fails", g.eq(0))
    q += WERR("Q: ... WSA_INVALID_PARAMETER", 87)
    q += AE(QW("A2"), QW("A1"), OV[12]) + g.chk("Q: AcceptEx on a socket not listening fails", g.eq(0))
    q += WERR("Q: ... WSAEINVAL", 10022) + STATUS("Q: ... OVERLAPPED", OV[12], 0x103, 0)
    q += AE(QW("L"), 0xDEAD, OV[12]) + g.chk("Q: AcceptEx with no accepting socket fails", g.eq(0))
    q += WERR("Q: ... WSAENOTSOCK", 10038)
    # -- a pending AcceptEx, completed by a connection.
    q += f"  mov {QW('abytes')}, 0xDEADBEEF{NL}" + AE(QW("L"), QW("A1"), OV[0])
    q += g.chk("Q: AcceptEx: FALSE", g.eq(0)) + g.gle("Q: ... ERROR_IO_PENDING", 997)
    q += STATUS("Q: ... pending", OV[0], 0x103, 0) + g.chk("Q: ... bytes received 0", g.mem(g.qv["abytes"], 0))
    q += AE(QW("L"), QW("A1"), OV[1]) + g.chk("Q: the accepting socket of a pending AcceptEx is refused", g.eq(0))
    q += WERR("Q: ... WSAEINVAL, not pending", 10022)
    q += NONE("Q: before a connection")
    q += SOCKQ("C") + g.call(4, QW("C"), g.qsaL, 16) + g.chk("Q: connect", g.eq(0)) + NAME("C", g.qsaC)
    q += GQ(2000) + PACKET("Q: the connection", True, 0x11, OV[0], 0) + STATUS("Q: the connection", OV[0], 0, 0)
    # the next AcceptEx stays pending through the reads below, as the game's do
    q += AE(QW("L"), QW("A2"), OV[8]) + g.gle("Q: AcceptEx again: ERROR_IO_PENDING", 997)
    # -- GetAcceptExSockaddrs.
    q += g.call("GetAcceptExSockaddrs", g.qab, 0, 32, 32, g.qv["pl"], g.qv["ll"], g.qv["pr"], g.qv["rl"])
    q += g.chk("Q: local address at buffer + 4", g.mem(g.qv["pl"], g.qab + 4))
    q += g.chk("Q: ... length 16", g.mem(g.qv["ll"], 16))
    q += g.chk("Q: remote address at buffer + 32 + 4", g.mem(g.qv["pr"], g.qab + 36))
    q += g.chk("Q: ... length 16", g.mem(g.qv["rl"], 16))
    q += g.chk("Q: remote: AF_INET", g.mem(g.qab + 36, 2, "word")) + g.chk("Q: remote: the connecting socket's port", PORTEQ(g.qab + 38, g.qsaC + 2))
    q += g.chk("Q: remote: 127.0.0.1", g.mem(g.qab + 40, 0x0100007F))
    q += g.chk("Q: local: AF_INET", g.mem(g.qab + 4, 2, "word")) + g.chk("Q: local: the listening port", PORTEQ(g.qab + 6, g.qsaL + 2))
    q += g.chk("Q: local: 127.0.0.1", g.mem(g.qab + 8, 0x0100007F))
    q += g.chk("Q: local area zero after the address", g.mem(g.qab + 20, 0)) + g.chk("Q: remote area zero after the address", g.mem(g.qab + 52, 0))
    # -- the accepted socket.
    q += f"  mov {QW('lin')}, 16{NL}" + g.call(5, QW("A1"), g.qsa2, g.qv["lin"]) + g.chk("Q: getpeername(accepted)", g.eq(0))
    q += g.chk("Q: ... the connecting socket", PORTEQ(g.qsa2 + 2, g.qsaC + 2))
    q += g.call(21, QW("A1"), 0xFFFF, 0x700B, g.qv["L"], 4) + g.chk("Q: setsockopt(SO_UPDATE_ACCEPT_CONTEXT)", g.eq(0))
    q += ASSOC("A1", 0x22) + g.chk("Q: associate the accepted socket (22h)", f"  cmp eax, {QW('port')}{NL}")
    # -- overlapped reads.
    q += RF("A1", g.qbuf[0], 64, OV[2]) + g.chk("Q: ReadFile: FALSE", g.eq(0)) + g.gle("Q: ReadFile: ERROR_IO_PENDING", 997)
    q += STATUS("Q: ReadFile pending", OV[2], 0x103, 0) + NONE("Q: nothing sent yet")
    q += g.call(19, QW("C"), g.str("hello"), 5, 0) + g.chk("Q: send 5", g.eq(5))
    q += GQ(2000) + PACKET("Q: the data", True, 0x22, OV[2], 5) + STATUS("Q: the data", OV[2], 0, 5)
    q += g.chk("Q: ... hell", g.mem(g.qbuf[0], 0x6C6C6568)) + g.chk("Q: ... o", g.mem(g.qbuf[0] + 4, 0x6F, "byte"))
    q += g.chk("Q: ... nothing after it written", g.mem(g.qbuf[0] + 5, 0xAB, "byte"))
    # two reads pending complete in order
    q += RF("A1", g.qbuf[1], 3, OV[3]) + RF("A1", g.qbuf[2], 64, OV[4])
    q += g.call(19, QW("C"), g.str("abcdefg"), 7, 0)
    q += GQ(2000) + PACKET("Q: the first of two reads", True, 0x22, OV[3], 3)
    q += GQ(2000) + PACKET("Q: the second", True, 0x22, OV[4], 4)
    q += g.chk("Q: ... abc", g.mem(g.qbuf[1], 0xAB636261)) + g.chk("Q: ... defg", g.mem(g.qbuf[2], 0x67666564))
    # an event with its low bit set: the event, no packet
    q += g.call("CreateEventA", 0, 1, 0, 0) + ST("ev") + f"  or eax, 1{NL}  mov dword ptr [{OV[5] + 16:#x}], eax{NL}"
    q += RF("A1", g.qbuf[3], 64, OV[5]) + g.call(19, QW("C"), g.str("z"), 1, 0)
    q += g.call("WaitForSingleObject", QW("ev"), 2000) + g.chk("Q: an event with its low bit set is set", g.eq(0))
    q += STATUS("Q: ... its OVERLAPPED", OV[5], 0, 1) + NONE("Q: ... and no packet")
    # the peer's close: 0 bytes, TRUE
    q += RF("A1", g.qbuf[3], 64, OV[6]) + g.call(3, QW("C")) + g.chk("Q: closesocket(peer)", g.eq(0))
    q += GQ(2000) + PACKET("Q: the peer's close", True, 0x22, OV[6], 0)
    # closesocket with a read pending: cancelled once, buffer untouched
    q += RF("A1", g.qbuf[4], 64, OV[7]) + g.call(3, QW("A1")) + g.chk("Q: closesocket with a read pending", g.eq(0))
    q += GQ(2000) + PACKET("Q: the cancelled read", False, 0x22, OV[7], 0, 995) + STATUS("Q: the cancelled read", OV[7], 0xC0000120, 0)
    q += NONE("Q: exactly one packet") + g.chk("Q: its buffer untouched", g.mem(g.qbuf[4], 0xABABABAB))
    q += ASSOC("A1", 0x23) + g.chk("Q: associating a closed socket fails", g.eq(0)) + g.gle("Q: ... ERROR_INVALID_HANDLE", 6)
    # a reset connection (SO_LINGER 0), on a second AcceptEx
    q += SOCKQ("C3") + g.call(4, QW("C3"), g.qsaL, 16)
    q += GQ(2000) + PACKET("Q: the second connection", True, 0x11, OV[8], 0)
    q += ASSOC("A2", 0x33) + RF("A2", g.qbuf[5], 64, OV[9])
    q += f"  mov {QW('lg')}, 1{NL}" + g.call(21, QW("C3"), 0xFFFF, 0x80, g.qv["lg"], 4) + g.call(3, QW("C3"))
    q += GQ(2000) + PACKET("Q: the reset connection", False, 0x33, OV[9], 0, 64) + STATUS("Q: the reset connection", OV[9], 0xC000020D, 0)
    q += g.call(3, QW("A2")) + g.chk("Q: closesocket after its read ended", g.eq(0)) + NONE("Q: ... no packet")
    # AcceptEx cancelled by closing its accepting socket
    q += SOCKQ("A3") + AE(QW("L"), QW("A3"), OV[10]) + g.call(3, QW("A3"))
    q += GQ(2000) + PACKET("Q: AcceptEx, its accepting socket closed", False, 0x11, OV[10], 0, 995)
    q += STATUS("Q: ... cancelled", OV[10], 0xC0000120, 0) + NONE("Q: ... once")
    # ... and by closing the listening socket: both, in order, once each
    q += SOCKQ("A4") + SOCKQ("A5") + AE(QW("L"), QW("A4"), OV[10]) + AE(QW("L"), QW("A5"), OV[11])
    q += g.call(3, QW("L")) + g.chk("Q: closesocket(listening) with two AcceptEx pending", g.eq(0))
    q += GQ(2000) + PACKET("Q: the first AcceptEx", False, 0x11, OV[10], 0, 995)
    q += GQ(2000) + PACKET("Q: the second AcceptEx", False, 0x11, OV[11], 0, 995) + NONE("Q: ... once each")
    q += g.call(3, QW("A4")) + g.chk("Q: their accepting sockets still close", g.eq(0)) + g.call(3, QW("A5"))
    q += NONE("Q: ... with no packet")
    # -- closing a socket while its read completes, 50 times: exactly one
    # packet each time, either the data (TRUE, 1 byte, written) or the
    # cancellation (FALSE, ERROR_OPERATION_ABORTED, buffer untouched).
    q += SOCKQ("L2") + LOOP(g.qsaL2) + g.call(2, QW("L2"), g.qsaL2, 16) + g.call(13, QW("L2"), 5) + NAME("L2", g.qsaL2)
    q += f"  mov {QW('i')}, 50{NL}  mov {QW('good')}, 0{NL}q_race:{NL}"
    q += f"  mov byte ptr [{g.qbuf[6]:#x}], 0xAB{NL}  mov dword ptr [{OV[12] + 16:#x}], 0{NL}"
    q += SOCKQ("C") + g.call(4, QW("C"), g.qsaL2, 16) + g.call(1, QW("L2"), 0, 0) + ST("acc")
    q += ASSOC("acc", 0x44) + g.call(19, QW("C"), g.str("x"), 1, 0)
    q += RF("acc", g.qbuf[6], 64, OV[12]) + g.call(3, QW("acc"))
    q += GQ(2000) + ST("ret")
    q += f"  cmp {QW('ovl')}, {OV[12]:#x}{NL}  jne q_bad{NL}  cmp {QW('key')}, 0x44{NL}  jne q_bad{NL}"
    q += f"  cmp {QW('ret')}, 1{NL}  jne q_cancelled{NL}"
    q += f"  cmp {QW('bytes')}, 1{NL}  jne q_bad{NL}  cmp dword ptr [{OV[12]:#x}], 0{NL}  jne q_bad{NL}"
    q += f"  cmp byte ptr [{g.qbuf[6]:#x}], 0x78{NL}  jne q_bad{NL}  jmp q_once{NL}q_cancelled:{NL}"
    q += g.call("GetLastError") + f"  cmp eax, 995{NL}  jne q_bad{NL}  cmp {QW('bytes')}, 0{NL}  jne q_bad{NL}"
    q += f"  cmp dword ptr [{OV[12]:#x}], 0xC0000120{NL}  jne q_bad{NL}  cmp byte ptr [{g.qbuf[6]:#x}], 0xAB{NL}  jne q_bad{NL}"
    q += f"q_once:{NL}" + GQ(0) + f"  test eax, eax{NL}  jnz q_bad{NL}"
    q += g.call("GetLastError") + f"  cmp eax, 258{NL}  jne q_bad{NL}  inc {QW('good')}{NL}q_bad:{NL}"
    q += g.call(3, QW("C")) + f"  dec {QW('i')}{NL}  jnz q_race{NL}"
    q += g.chk("Q: close racing a completion: one consistent packet, 50 of 50", g.mem(g.qv["good"], 50))
    q += g.call(3, QW("L2"))
    g.q_code = q
    g.q_names, g.names = g.names[first_q:], g.names[:first_q]

    # mode M: a shown (active) popup minimized and restored, by ShowWindow
    # and by the system commands; the log is printed as in mode W.
    m = mkclass + win("n", 0x90000000, 10, 20, 100, 50) + f"  mov dword ptr [{v['hover']:#x}], eax{NL}"
    m += g.call("ShowWindow", P("hover"), 1) + seg("seg0")
    m += g.call("ShowWindow", P("hover"), 6) + seg("seg1")
    m += g.call("ShowWindow", P("hover"), 9) + seg("seg2")
    m += g.call("DefWindowProcA", P("hover"), 0x112, 0xF020, 0) + seg("seg3")
    m += g.call("DefWindowProcA", P("hover"), 0x112, 0xF120, 0)
    m += g.call("wsprintfA", g.out, g.str("S%X,%X,%X,%X:"), P("seg0"), P("seg1"), P("seg2"), P("seg3"))
    # (wsprintfA here takes 6 arguments; mode W's printing then follows.)
    g.m_code = m + "  add esp, 24\n" + w[w.index("  add esp, 32") + len("  add esp, 32\n"):]

    # mode L: a GL context on a popup's DC
    gl = mkclass + win("g", 0x80000000, 0, 0, 64, 64) + f"  mov dword ptr [{v['hwnd']:#x}], eax\n"
    gl += g.call("GetDC", f"dword ptr [{v['hwnd']:#x}]") + f"  mov dword ptr [{v['hdc']:#x}], eax\n"
    hdc = f"dword ptr [{v['hdc']:#x}]"
    gl += g.call("ChoosePixelFormat", hdc, g.pfd) + "  push eax\n  pop esi\n"
    gl += g.call("SetPixelFormat", hdc, "esi", g.pfd)
    gl += g.call("wglCreateContext", hdc) + "  mov esi, eax\n" + g.call("wglMakeCurrent", hdc, "esi")
    gl_names = []

    def glchk(name, setup, err):
        gl_names.append(name)
        return setup + g.call("glGetError") + f"  cmp eax, {err:#x}\n  call flag\n"
    # GL 1.1 glTexGen: INVALID_ENUM for a coord other than S/T/R/Q, a pname
    # other than TEXTURE_GEN_MODE, a bad mode, SPHERE_MAP for R or Q;
    # INVALID_OPERATION between glBegin and glEnd.
    gl += glchk("gl: a context, no error", "", 0)
    gl += glchk("gl: glTexGeni(S, MODE, SPHERE_MAP)", g.call("glTexGeni", 0x2000, 0x2500, 0x2402), 0)
    gl += glchk("gl: glTexGeni(T, MODE, OBJECT_LINEAR)", g.call("glTexGeni", 0x2001, 0x2500, 0x2401), 0)
    gl += glchk("gl: glTexGeni(Q, MODE, EYE_LINEAR)", g.call("glTexGeni", 0x2003, 0x2500, 0x2400), 0)
    gl += glchk("gl: SPHERE_MAP for R is INVALID_ENUM", g.call("glTexGeni", 0x2002, 0x2500, 0x2402), 0x500)
    gl += glchk("gl: pname OBJECT_PLANE is INVALID_ENUM", g.call("glTexGeni", 0x2000, 0x2501, 0x2400), 0x500)
    gl += glchk("gl: coord 0x2004 is INVALID_ENUM", g.call("glTexGeni", 0x2004, 0x2500, 0x2400), 0x500)
    gl += glchk("gl: mode 0x2403 is INVALID_ENUM", g.call("glTexGeni", 0x2001, 0x2500, 0x2403), 0x500)
    gl += glchk("gl: inside glBegin/glEnd is INVALID_OPERATION",
                g.call("glBegin", 0) + g.call("glTexGeni", 0x2000, 0x2500, 0x2400) + g.call("glEnd"), 0x502)
    gl_names.append("gl: wglSwapLayerBuffers(main plane) is TRUE")
    gl += g.call("wglSwapLayerBuffers", hdc, 1) + "  cmp eax, 1\n  call flag\n"
    g.gl_names = gl_names

    # mode S: the stall recorder (<ID>_STALL): frames of a known make-up on a
    # GL context, each ended by a swap (a presented frame). The recorder's
    # reports on stderr are checked; the program prints nothing.
    swap = g.call("wglSwapLayerBuffers", hdc, 1)
    sc = mkclass + win("s", 0x80000000, 0, 0, 64, 64) + f"  mov dword ptr [{v['hwnd']:#x}], eax\n"
    sc += g.call("GetDC", f"dword ptr [{v['hwnd']:#x}]") + f"  mov dword ptr [{v['hdc']:#x}], eax\n"
    sc += g.call("ChoosePixelFormat", hdc, g.pfd) + "  push eax\n  pop esi\n"
    sc += g.call("SetPixelFormat", hdc, "esi", g.pfd)
    sc += g.call("wglCreateContext", hdc) + "  mov esi, eax\n" + g.call("wglMakeCurrent", hdc, "esi")
    # frames 1-2: process start to the first frame, the window system's
    # first events (not checked)
    sc += swap + g.call("Sleep", 20) + swap
    sc += g.call("Sleep", 5) + swap               # frame 3: short
    sc += g.call("Sleep", 160) + swap             # frame 4: no message pumped yet
    sc += g.call("PeekMessageA", g.msg, 0, 0, 0, 0) + g.call("Sleep", 160) + swap  # frame 5: pumped
    sc += g.call("Sleep", 160) + swap             # frame 6: not pumped, after pumping
    # frame 7: three 1 KB reads, a 16x16 RGBA texture upload, then a wait
    sc += g.call("CreateFileA", g.str("C:\\T\\data.bin"), 0x80000000, 1, 0, 3, 0x80, 0) + "  mov edi, eax\n"
    for _ in range(3):
        sc += g.call("ReadFile", "edi", g.out, 1024, g.tmp, 0)
    sc += g.call("CloseHandle", "edi") + g.call("glBindTexture", 0x0DE1, 1)
    sc += g.call("glTexImage2D", 0x0DE1, 0, 0x1908, 16, 16, 0, 0x1908, 0x1401, g.out)
    sc += g.call("Sleep", 130) + swap
    # frame 8: guest code for at least 150 ms (GetTickCount between batches
    # of a million loop iterations)
    # (a multiplicative recurrence the compiler cannot fold away)
    sc += g.call("GetTickCount") + f"  mov dword ptr [{g.tmp + 8:#x}], eax\ns_busy:\n  mov ecx, 1000000\n"
    sc += f"  mov eax, dword ptr [{g.tmp + 16:#x}]\ns_spin:\n  imul eax, eax, 1103515245\n  add eax, 12345\n"
    sc += f"  dec ecx\n  jnz s_spin\n  mov dword ptr [{g.tmp + 16:#x}], eax\n" + g.call("GetTickCount")
    sc += f"  sub eax, dword ptr [{g.tmp + 8:#x}]\n  cmp eax, 150\n  jb s_busy\n" + swap
    g.s_code = sc
    # mode T: two million GetCommandLineA calls (a cheap import the recorder
    # times), timed by GetTickCount ("T<ms>"): the per-import overhead.
    tc = g.call("GetTickCount") + f"  mov dword ptr [{g.tmp + 8:#x}], eax\n  mov dword ptr [{g.tmp + 12:#x}], 2000000\n"
    tc += "t_loop:\n" + g.call("GetCommandLineA") + f"  dec dword ptr [{g.tmp + 12:#x}]\n  jnz t_loop\n"
    tc += g.call("GetTickCount") + f"  sub eax, dword ptr [{g.tmp + 8:#x}]\n"
    tc += g.call("wsprintfA", g.out, g.str("T%u"), "eax") + "  add esp, 12\n" + g.call("OutputDebugStringA", g.out)
    g.t_code = tc
    planes = mkclass + win("q", 0x80000000, 0, 0, 64, 64) + "  mov esi, eax\n" + g.call("GetDC", "esi")
    planes += "  mov esi, eax\n" + g.call("ChoosePixelFormat", "esi", g.pfd) + g.call("SetPixelFormat", "esi", "eax", g.pfd)
    planes += g.call("wglCreateContext", "esi") + g.call("wglMakeCurrent", "esi", "eax")
    planes += g.call("wglSwapLayerBuffers", "esi", 2) + g.call("ExitProcess", 9)

    stops = [
        g.call("EnumDisplayDevicesA", g.str("\\\\.\\DISPLAY1"), 0, g.dd, 0),
        g.call("ChangeDisplaySettingsExA", 0, 0, 0x1234, 0, 0),
        g.call("CreateEventA", 0, 1, 0, 0) + g.call("CreateIoCompletionPort", "eax", 0, 0, 0),
        g.call("GetProfileStringA", 0, 0, 0, g.tmp, 64),
        mkclass + win("z", 0xA0000000, 0, 0, 64, 64),
        g.call("FillRect", 0x00D00001, g.r4, 0x00E00004),
        g.call("DrawTextA", 0x00D00001, g.str("hi"), -1, g.r4, 0x25),
        g.call("InvalidateRect", 0, 0, 1),
        g.call("RegisterClassA", g.wc4) + g.call("CreateWindowExA", 0, g.str("T4"), g.str("b"), 0x90000000,
                                                0, 0, 64, 64, 0, 0, EXE, 0) + pump(),
        g.call(23, 2, 1, 0) + g.call("WriteFile", "eax", g.tmp, 1, g.n, g.ovl),
        g.call(23, 2, 1, 0) + g.call("ReadFile", "eax", g.tmp, 1, g.n, 0),
        g.call("AcceptEx", 0, 0, g.tmp, 4, 32, 32, 0, g.ovl),
    ]
    g.stop_modes = "".join(f"  cmp eax, {0x31 + i:#x}\n  je stop_{i}\n" for i in range(len(stops)))
    g.stop_code = "".join(f"stop_{i}:\n{code}" + g.call("ExitProcess", 9) for i, code in enumerate(stops))

    finish = f"""  mov ecx, dword ptr [{g.n:#x}]
  mov byte ptr [{g.buf:#x}+ecx], 0x0A
""" + g.call("OutputDebugStringA", g.buf) + g.call("ExitProcess", 0)

    return f"""
  jmp main
.org {WORKER:#x}, 0xCC
worker:
  push 0xFFFFFFFF
  push {v['ovl']:#x}
  push {v['wkey']:#x}
  push {v['bytes']:#x}
  push dword ptr [esp+20]
  call dword ptr [{g.iat[('kernel32.dll', 'GetQueuedCompletionStatus')]:#x}]
  ret 4
.org {WNDPROC:#x}, 0xCC
wndproc:
  mov ecx, dword ptr [{v['logn']:#x}]
  cmp ecx, 64
  jae 1f
  mov edx, ecx
  shl edx, 4
  mov eax, dword ptr [esp+8]
  mov dword ptr [{g.logbuf:#x}+edx], eax
  mov eax, dword ptr [esp+12]
  mov dword ptr [{g.logbuf:#x}+edx+4], eax
  mov eax, dword ptr [esp+16]
  mov dword ptr [{g.logbuf:#x}+edx+8], eax
  inc ecx
  mov dword ptr [{v['logn']:#x}], ecx
1:
  jmp dword ptr [{g.iat[('user32.dll', 'DefWindowProcA')]:#x}]
.org {TRYCS:#x}, 0xCC
trycs:
  push dword ptr [esp+4]
  call dword ptr [{g.iat[('kernel32.dll', 'TryEnterCriticalSection')]:#x}]
  mov dword ptr [{v['tryres']:#x}], eax
  ret 4
.org {PAINTPROC:#x}, 0xCC
paintproc:
  cmp dword ptr [esp+8], 0x14
  jne 1f
  inc dword ptr [{v['ecount']:#x}]
1:
  cmp dword ptr [esp+8], 0xF
  jne 2f
  push {g.ps:#x}
  push dword ptr [esp+8]
  call dword ptr [{g.iat[('user32.dll', 'BeginPaint')]:#x}]
  mov dword ptr [{v['phdc']:#x}], eax
  inc dword ptr [{v['pcount']:#x}]
  mov eax, dword ptr [{g.ps + 4:#x}]
  mov dword ptr [{v['perase']:#x}], eax
  mov eax, dword ptr [{g.ps + 8:#x}]
  mov dword ptr [{v['pl']:#x}], eax
  mov eax, dword ptr [{g.ps + 12:#x}]
  mov dword ptr [{v['pt']:#x}], eax
  mov eax, dword ptr [{g.ps + 16:#x}]
  mov dword ptr [{v['pr']:#x}], eax
  mov eax, dword ptr [{g.ps + 20:#x}]
  mov dword ptr [{v['pb']:#x}], eax
  push {g.ps:#x}
  push dword ptr [esp+8]
  call dword ptr [{g.iat[('user32.dll', 'EndPaint')]:#x}]
  xor eax, eax
  ret 16
2:
  jmp dword ptr [{g.iat[('user32.dll', 'DefWindowProcA')]:#x}]
.org {WAVEPROC:#x}, 0xCC
waveproc:
  cmp dword ptr [esp+12], 0x77
  jne 1f
  mov ecx, dword ptr [{g.wn:#x}]
  cmp ecx, 16
  jae 1f
  lea edx, [ecx+ecx*2]
  mov eax, dword ptr [esp+8]
  mov dword ptr [{g.wlog:#x}+edx*4], eax
  mov eax, dword ptr [esp+16]
  mov dword ptr [{g.wlog + 4:#x}+edx*4], eax
  inc dword ptr [{g.wn:#x}]
  push edx
  call dword ptr [{g.iat[('kernel32.dll', 'GetCurrentThreadId')]:#x}]
  pop edx
  mov dword ptr [{g.wlog + 8:#x}+edx*4], eax
1:
  ret 20
.org {MAIN:#x}, 0xCC
main:
{g.call("GetCommandLineA")}
2:
  cmp byte ptr [eax+1], 0
  je 5f
  inc eax
  jmp 2b
5:
  movzx eax, byte ptr [eax]
  cmp eax, 0x57
  je mode_w
  cmp eax, 0x4C
  je mode_l
  cmp eax, 0x50
  je mode_p
  cmp eax, 0x44
  je mode_d
  cmp eax, 0x4D
  je mode_m
  cmp eax, 0x4F
  je mode_o
  cmp eax, 0x4E
  je mode_n
  cmp eax, 0x51
  je mode_q
  cmp eax, 0x42
  je mode_b
  cmp eax, 0x52
  je mode_r
  cmp eax, 0x56
  je mode_v
  cmp eax, 0x46
  je mode_f
  cmp eax, 0x58
  je mode_x
  cmp eax, 0x53
  je mode_s
  cmp eax, 0x54
  je mode_t
{g.stop_modes}{a}{finish}
mode_d:
{g.d_code}{finish}
mode_m:
{g.m_code}
mode_o:
{g.o_code}{finish}
mode_n:
{g.n_code}{finish}
mode_q:
{g.q_code}{finish}
mode_b:
{g.b_code}{finish}
mode_r:
{g.r_code}{finish}
mode_v:
{g.v_code}{finish}
mode_f:
{g.f_code}
mode_w:
{w}
mode_l:
{gl}{finish}
mode_p:
{planes}
mode_s:
{g.s_code}{finish}
mode_t:
{g.t_code}{finish}
mode_x:
  mov dword ptr [{g.var['xself']:#x}], {g.var['xself']:#x}
  mov ebx, 0x22222222
  mov esi, 0x55555555
  mov edi, 0x66666666
  call fault_3c
  int3
fault_3c:
  push ebp
  mov ebp, esp
  mov eax, dword ptr [0x3C]
  pop ebp
  ret
{g.stop_code}
flag:
  sete al
  add al, 0x30
  mov ecx, dword ptr [{g.n:#x}]
  mov byte ptr [{g.buf:#x}+ecx], al
  inc ecx
  mov dword ptr [{g.n:#x}], ecx
  ret
"""


HARNESS = r"""
#include <string>
#include "runtime/runtime.h"
int main(int argc, char** argv) {
  recomp::GameConfig g;
  g.id = "win32test";
  g.guest_dir = "C:\\T";
  g.exe_name = "t.exe";
  g.registry_dwords.push_back({"HKCU\\@KEY@", "@VALUE@", @DWORD@u});
  return recomp::RunProcess(g, std::string(argv[1]) + "/t.exe", argv[1], argv[2]);
}
"""


def build_and_link(tmp):
    g = Guest()
    text = tl.assemble(tmp, build_text(g))
    inst = os.path.join(tmp, "install")
    os.makedirs(inst, exist_ok=True)
    with open(os.path.join(inst, "t.exe"), "wb") as f:
        f.write(image(text, g.d, g.imp))
    sym = os.path.join(tmp, "sym")
    os.makedirs(sym, exist_ok=True)
    with open(os.path.join(sym, "functions.tsv"), "w") as f:
        f.write("entry\tmin\tmax\tchunks\tthunk\tnoreturn\tcallconv\tname\n")
        for o in (0, WORKER, WNDPROC, TRYCS, PAINTPROC, WAVEPROC):
            e = TEXT + o
            f.write(f"{e:08X}\t{e:08X}\t{e:08X}\t1\t0\t0\t__stdcall\tFUN_{e:08X}\n")
    for n, h in (("exports.tsv", "va\tkind\tmangled\tdemangled\n"), ("jumptables.tsv", "jmp\ttargets\n")):
        with open(os.path.join(sym, n), "w") as f:
            f.write(h)
    man = os.path.join(sym, "m.manifest")
    open(man, "w").close()
    gen = os.path.join(tmp, "gen")
    r = subprocess.run([tl.LIFT, "--exe", os.path.join(inst, "t.exe"), "--symbols", sym, "--manifest", man,
                        "--out", gen], capture_output=True, text=True)
    check("lift succeeds", r.returncode, 0)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return None, g
    harness = (HARNESS.replace("@KEY@", REG_KEY.replace("\\", "\\\\")).replace("@VALUE@", REG_VALUE)
               .replace("@DWORD@", f"{REG_DWORD:#x}"))
    with open(os.path.join(tmp, "harness.cpp"), "w") as f:
        f.write(harness)
    binp = os.path.join(tmp, "win32test")
    srcs = [os.path.join(gen, n) for n in sorted(os.listdir(gen)) if n.endswith(".cpp")]
    cmd = [tl.CXX, "-std=c++20", "-O1", "-w", "-fno-strict-aliasing", "-fnon-call-exceptions",
           "-ffp-contract=off", "-fno-omit-frame-pointer", "-I", os.path.join(tl.X86, "src"),
           os.path.join(tmp, "harness.cpp"), *srcs,
           os.path.join(tl.X86, "src", "runtime", "lifted_table.cpp"),
           "-L", tl.BUILD, "-lrecomp_runtime", "-lrecomp_opengl", "-lrecomp_x87", "-lrecomp_image",
           "-Wl,-rpath," + tl.BUILD, "-o", binp]
    cached = CACHE and os.path.join(CACHE, link_key(cmd, tmp))
    if cached and os.path.exists(cached):
        shutil.copy2(cached, binp)
        cc = subprocess.CompletedProcess(cmd, 0, "", "")
    else:
        cc = subprocess.run(cmd, capture_output=True, text=True)
        if cached and cc.returncode == 0:
            os.makedirs(CACHE, exist_ok=True)
            shutil.copy2(binp, cached + ".tmp")
            os.replace(cached + ".tmp", cached)
    check("links with the runtime and recomp_opengl", cc.returncode, 0)
    if cc.returncode:
        print(cc.stderr[:3000])
        return None, g
    return binp, g


def link_key(cmd, tmp):
    """Every input of the test program's compile and link: the compiler (its
    real path names its version), the command with this run's temporary paths
    made relative, the sources it names, every header below x86recomp/src, and
    the symbols the four runtime libraries export. Equal keys: the same
    program."""
    h = hashlib.sha256(os.path.realpath(tl.CXX).encode())
    for a in cmd:
        h.update(b"\0" + (os.path.relpath(a, tmp) if a.startswith(tmp + os.sep) else a).encode())
        if a.endswith(".cpp"):
            with open(a, "rb") as f:
                h.update(f.read())
    src = os.path.join(tl.X86, "src")
    for d, subdirs, files in sorted(os.walk(src)):
        subdirs.sort()
        for n in sorted(files):
            if n.endswith((".h", ".hpp", ".inc", ".def")):
                with open(os.path.join(d, n), "rb") as f:
                    h.update(b"\0" + os.path.relpath(os.path.join(d, n), src).encode() + b"\0" + f.read())
    for lib in ("runtime", "opengl", "x87", "image"):
        r = subprocess.run(["nm", "-gUj", os.path.join(tl.BUILD, f"librecomp_{lib}.dylib")],
                           capture_output=True, check=True)
        h.update(b"\0" + r.stdout)
    return h.hexdigest()


def run(tmp, binp, mode, during=None, **extra):
    data = os.path.join(tmp, "data")
    # WIN.INI for GetProfileStringA (the per-user drive C).
    ini = os.path.join(data, "win32test", "drive_c", "WINDOWS")
    os.makedirs(ini, exist_ok=True)
    with open(os.path.join(ini, "win.ini"), "w") as f:
        f.write("[fonts]\n[Mss]\n  MSSDebug = \"Yes\"  \n")
    env = dict(os.environ, XDG_DATA_HOME=data, WIN32TEST_BACKGROUND="1",
               **{"WIN32TEST_" + k: v for k, v in extra.items()})
    if during is None:
        r = subprocess.run([binp, os.path.join(tmp, "install"), mode], capture_output=True, text=True, env=env,
                           timeout=120)
    else:
        # during(): runs while the program does (e.g. appends to a follow file).
        proc = subprocess.Popen([binp, os.path.join(tmp, "install"), mode], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        during()
        stdout, stderr = proc.communicate(timeout=120)
        r = subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)
    out = re.findall(r"\[guest\] (.*)", r.stderr)
    fatal = re.search(r"FATAL: (.*)", r.stderr)
    run.stderr = r.stderr
    return r.returncode, out, fatal.group(1) if fatal else None


STALL_RE = re.compile(r"stall: frame (\d+) took ([\d.]+) ms at t=([\d.]+) s \[(\w+)[^\]]*\]: ([^|]*)(?:\| imports: ([^|]*))?(?:\| untimed: [^|]*)?(?:\| samples (\d+)(?:, guest fn: ([^,]*))?)?")


def stalls(log):
    """{frame: report} of the recorder's reports: ms, phase, {category: ms},
    the category text, the imports text, samples and the guest functions."""
    found = {}
    for m in STALL_RE.finditer(log):
        cats = {}
        for part in m.group(5).split(","):
            c = re.match(r"\s*([a-z-]+) ([\d.]+)", part)
            if c:
                cats[c.group(1)] = float(c.group(2))
        found[int(m.group(1))] = dict(ms=float(m.group(2)), t=float(m.group(3)), phase=m.group(4), cats=cats,
                                      text=m.group(5), imports=m.group(6) or "", samples=int(m.group(7) or 0),
                                      guest=(m.group(8) or "").split(), raw=m.group(0))
    return found


def fit_point(sw, sh, dw, dh, x, y):
    """A point of a dw x dh window -> the sw x sh frame shown in it with its
    aspect kept: the fitted side is round(other side * aspect), the bars
    split the rest (left/top the floor), and the point maps through that
    rectangle, clamped to the frame (exact rationals)."""
    from fractions import Fraction as Q
    w, h = dw, dh
    if dw * sh > dh * sw:
        w = int(Q(dh * sw, sh) + Q(1, 2))
    else:
        h = int(Q(dw * sh, sw) + Q(1, 2))
    left, top = (dw - w) // 2, (dh - h) // 2
    fx = (Q(x) - left) * sw / w
    fy = (Q(y) - top) * sh / h
    return (min(max(int(fx // 1), 0), sw - 1), min(max(int(fy // 1), 0), sh - 1))


def lan_broadcast_errno():
    """errno of one UDP broadcast from this process (None: sent). Mode N's
    broadcast check needs a process allowed on the LAN; macOS answers
    EHOSTUNREACH to one that is not, e.g. a process left running after its
    ssh session ended (OBSERVED 2026-10-28: such a process failed 499 of 500
    broadcasts, the same program run attached 0 of 500)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(b"x", ("255.255.255.255", 6112))
        return None
    except OSError as e:
        return e.errno
    finally:
        s.close()


def flags(names, out, prefix):
    got = out[0] if out else ""
    check(f"{prefix}: one flag per check", len(got), len(names))
    for i, name in enumerate(names):
        check(name, got[i:i + 1], "1")


def sizes(log):
    """[(msg, wparam, lparam)] of the size-related messages, as ints."""
    keep = {0x81, 0x01, 0x05, 0x03}
    return [m for m in log if m[0] in keep]


MODE_GROUPS = ("A", "W", "V", "O", "N", "Q", "B", "F", "X", "S", "T", "M", "D", "L", "P", "stops")
SELECTED = None  # None: every group
CACHE = None  # --cache DIR


def selected(group):
    return SELECTED is None or group in SELECTED


def main():
    global SELECTED, CACHE
    args = sys.argv[1:]
    while args:
        if args[0] == "--modes" and len(args) > 1:
            SELECTED = set(args[1].split(","))
            unknown = SELECTED - set(MODE_GROUPS)
            if unknown or not SELECTED:
                sys.exit(f"--modes: unknown group(s) {sorted(unknown)}; groups: {' '.join(MODE_GROUPS)}")
        elif args[0] == "--cache" and len(args) > 1:
            CACHE = os.path.abspath(args[1])
        else:
            sys.exit("usage: test_win32.py [--modes A,N,...] [--cache DIR]")
        args = args[2:]
    with tempfile.TemporaryDirectory() as tmp:
        binp, g = build_and_link(tmp)
        if binp:
            if selected("A"):
                code, out, fatal = run(tmp, binp, "A")
                check("A: runs to the end", (code, fatal), (0, None))
                flags(g.names, out, "A")

            if selected("W"):
                code, out, fatal = run(tmp, binp, "W")
                check("W: runs to the end", (code, fatal), (0, None))
                m = re.match(r"R([0-9A-F]+),([0-9A-F]+) S([0-9A-F]+),([0-9A-F]+),([0-9A-F]+),([0-9A-F]+):(.*)",
                             out[0] if out else "")
                check("W: log printed", bool(m), True)
                if m:
                    work_w, work_h = int(m.group(1), 16), int(m.group(2), 16)
                    cuts = [0] + [int(x, 16) for x in m.groups()[2:6]]
                    log = [tuple(int(x, 16) for x in e.split("/")) for e in m.group(7).split()]
                    segs = [sizes(log[cuts[i]:cuts[i + 1]]) for i in range(4)]
                    mk = lambda lo, hi: lo | (hi << 16)
                    # Wine msg.c WmCreateChildSeq / WmCreateMaxPopupSeq /
                    # WmCreateOverlappedSeq, verified there on Windows. The
                    # maximized popup takes the work area (SPI_GETWORKAREA: the
                    # runtime's screen), at its origin.
                    s0 = segs[0]
                    check("W: popup: NCCREATE, CREATE, SIZE(RESTORED), MOVE",
                          [(x[0], x[1]) for x in s0], [(0x81, 0), (0x01, 0), (0x05, 0), (0x03, 0)])
                    check("W: popup: WM_SIZE is the 100x50 client", s0[2][2] if len(s0) > 2 else None, mk(100, 50))
                    check("W: popup: WM_MOVE is the client origin (10,20)", s0[3][2] if len(s0) > 3 else None,
                          mk(10, 20))
                    s1 = segs[1]
                    check("W: maximized popup: ... SIZE(RESTORED), MOVE, then MOVE, SIZE(MAXIMIZED)",
                          [(x[0], x[1]) for x in s1], [(0x81, 0), (0x01, 0), (0x05, 0), (0x03, 0), (0x03, 0), (0x05, 2)])
                    check("W: maximized popup: the maximized move is to the work area origin",
                          s1[4][2] if len(s1) > 4 else None, mk(0, 0))
                    check("W: maximized popup: the maximized size is the work area's",
                          s1[5][2] if len(s1) > 5 else None, mk(work_w, work_h))
                    check("W: overlapped, invisible: no WM_SIZE/WM_MOVE at creation",
                          [x[0] for x in segs[2]], [0x81, 0x01])
                    check("W: overlapped: its first ShowWindow ends with SIZE(RESTORED), MOVE",
                          [(x[0], x[1]) for x in segs[3]][-2:], [(0x05, 0), (0x03, 0)])

            if selected("V"):
                code, out, fatal = run(tmp, binp, "V")
                check("V: runs to the end", (code, fatal), (0, None))
                flags(g.v_names, out, "V")

            if selected("O"):
                code, out, fatal = run(tmp, binp, "O")
                check("O: runs to the end", (code, fatal), (0, None))
                flags(g.o_names, out, "O")

            if selected("N"):
                # Mode N: Winsock 1.1 sockets on loopback (patch 0023), and one
                # broadcast on the LAN, which needs this process to be allowed there.
                check("N: precondition: this process may broadcast on the LAN (run attached, not detached from ssh)",
                      lan_broadcast_errno(), None)
                code, out, fatal = run(tmp, binp, "N", NET_LOG="1")
                check("N: runs to the end", (code, fatal), (0, None))
                before = failures
                flags(g.n_names, out, "N")
                if failures > before:  # the host errors behind them (<ID>_NET_LOG)
                    print("".join(l + "\n" for l in run.stderr.splitlines() if l.startswith("wsock32:")), end="")

            if selected("Q"):
                # Mode Q: completion ports on sockets (patch 0024).
                code, out, fatal = run(tmp, binp, "Q", NET_LOG="1")
                check("Q: runs to the end", (code, fatal), (0, None))
                before = failures
                flags(g.q_names, out, "Q")
                if failures > before:
                    print("".join(l + "\n" for l in run.stderr.splitlines() if l.startswith("wsock32:")), end="")

            if selected("B"):
                # Modes B and R: LAN discovery broadcasts (patch 0025); a LAN
                # broadcast again, so the same precondition.
                check("B: precondition: this process may broadcast on the LAN (run attached, not detached from ssh)",
                      lan_broadcast_errno(), None)
                code, out, fatal = run(tmp, binp, "B", NET_LOG="1")
                check("B: runs to the end", (code, fatal), (0, None))
                flags(g.b_names, out, "B")
                code, out, fatal = run(tmp, binp, "R", NET_LOG="1", TEST_NO_LIMITED_BROADCAST="1")
                check("R: runs to the end", (code, fatal), (0, None))
                flags(g.r_names, out, "R")

            if selected("F"):
                # Mode F: the screen the game sees is the desktop (W x H pixels);
                # fullscreen on the simulated screen is a 1000x500-point window,
                # windowed is the client scaled to fit it (min(1, 1000/W, 500/H)).
                # Pointer positions are window points.
                script = os.path.join(tmp, "f_input.txt")
                with open(script, "w") as fh:
                    fh.write("1.0 pointer 520 260\n1.3 click\n1.6 pointer 20 100\n1.9 click\n"
                             "2.5 chord ctrl+gui F\n3.2 pointer 300 200\n3.5 click\n"
                             "4.2 chord ctrl+gui F\n4.9 pointer 990 490\n5.2 click\n")
                code, out, fatal = run(tmp, binp, "F", TEST_SCREEN="1000x500", TEST_INPUT=script)
                log = run.stderr
                check("F: runs to the end", (code, fatal), (0, None))
                mf = re.match(r"R([0-9A-F]+),([0-9A-F]+) C([0-9A-F]+):([0-9A-F]+),([0-9A-F]+),([0-9A-F]+),([0-9A-F]+)",
                              out[0] if out else "")
                check("F: clicks printed", bool(mf), True)
                check("F: a maximized popup goes fullscreen on the simulated screen, and again after the toggles",
                      len(re.findall(r"simulated fullscreen 1000x500 for a", log)), 2)
                check("F: Ctrl+Cmd+F: windowed, then fullscreen",
                      re.findall(r"user32: (windowed|fullscreen) \(Ctrl\+Cmd\+F\)", log), ["windowed", "fullscreen"])
                if mf:
                    W, H = int(mf.group(1), 16), int(mf.group(2), 16)
                    s = min(1, 1000 / W, 500 / H)
                    ww, wh = max(round(W * s), 1), max(round(H * s), 1)
                    pt = lambda lp: (lp & 0xFFFF, lp >> 16)
                    got = [pt(int(mf.group(i), 16)) for i in range(4, 8)]
                    check("F: four clicks reached the window", int(mf.group(3), 16), 4)
                    check("F: fullscreen: a click inside the frame", got[0], fit_point(W, H, 1000, 500, 520, 260))
                    check("F: fullscreen: a click on a bar is at the frame's edge", got[1],
                          fit_point(W, H, 1000, 500, 20, 100))
                    check("F: windowed (Ctrl+Cmd+F): the scaled window maps to the client", got[2],
                          fit_point(W, H, ww, wh, 300, 200))
                    check("F: fullscreen again: past the frame clamps to its last pixel", got[3],
                          fit_point(W, H, 1000, 500, 990, 490))

                # Mode F with TEST_INPUT_FOLLOW: lines appended while it runs are
                # queued, "+<s>" times relative to when they are read; a partly
                # written line waits until it is complete.
                follow = os.path.join(tmp, "f_follow.txt")
                open(follow, "w").close()

                def feed():
                    time.sleep(2.0)
                    with open(follow, "a") as fh:
                        fh.write("+0.2 pointer 520 260\n+0.5 click\n+0.8 pointer 20")
                    time.sleep(1.0)
                    with open(follow, "a") as fh:
                        fh.write(" 100\n+1.1 click\n")
                code, out, fatal = run(tmp, binp, "F", during=feed, TEST_SCREEN="1000x500", TEST_INPUT_FOLLOW=follow)
                log = run.stderr
                check("FF: runs to the end", (code, fatal), (0, None))
                check("FF: each complete appended line read once",
                      re.findall(r"TEST_INPUT_FOLLOW: at [0-9.]+ s: (.*)", log),
                      ["+0.2 pointer 520 260", "+0.5 click", "+0.8 pointer 20 100", "+1.1 click"])
                reads = [float(x) for x in re.findall(r"TEST_INPUT_FOLLOW: at ([0-9.]+) s", log)]
                check("FF: the split line read after its second part (>= 0.9 s after the first lines)",
                      len(reads) == 4 and reads[2] - reads[0] >= 0.9, True)
                mf = re.match(r"R([0-9A-F]+),([0-9A-F]+) C([0-9A-F]+):([0-9A-F]+),([0-9A-F]+)", out[0] if out else "")
                check("FF: clicks printed", bool(mf), True)
                if mf:
                    W, H = int(mf.group(1), 16), int(mf.group(2), 16)
                    pt = lambda lp: (lp & 0xFFFF, lp >> 16)
                    check("FF: two appended clicks reached the window", int(mf.group(3), 16), 2)
                    check("FF: an appended click lands where its pointer line put it",
                          [pt(int(mf.group(4), 16)), pt(int(mf.group(5), 16))],
                          [fit_point(W, H, 1000, 500, 520, 260), fit_point(W, H, 1000, 500, 20, 100)])

            if selected("X"):
                # Mode X: a guest read of address 0x3C with no exception handler
                # installed (a null object's field). The fatal report must say
                # why it was not handled and show the guest's registers (spilled
                # at the call) and its EBP chain, on stderr and in the crash file.
                # FATAL_DUMP: guest memory named by expressions, dumped in the report.
                # Expected values from the PE format: "MZ" at the image base, the
                # PE signature at base + e_lfanew (read through a dereference).
                # Patch 0019's arithmetic, checked against the image this test
                # writes: e_lfanew (0x3C) = 0x40, ImageBase at PE + 0x34 = 0x400000;
                # 32-bit wrapping; "*" before "+"/"-", left to right; xself holds
                # its own address (mode X stores it), so nested reads stay readable.
                xs = f"{g.var['xself']:#x}"
                deep = lambda n: "[" * n + xs + "]" * n
                dumps = {
                    "sub": "0x400040-4", "prec": "0x400000+0xF*4", "sum": "0x400000+[0x40003C]",
                    "mixed": "[0x400000+[0x40003C]+0x34]*2-0x400000+0x3C",
                    "wrap_add": "0xFFFFFFFF+0x400001", "wrap_mul": "0x80100000*2+0x200000",
                    "too_big": "0x100000000+0x400000", "signed": "0x400000++4", "mul_expr": "0x10*[0x40003C]",
                    "trailing": "0x400000)", "unclosed": "[0x40003C",
                    "deep8": deep(8), "deep9": deep(9), "side9": "+".join([deep(1)] * 9),
                }
                spec = ",".join(["0x400000:16", "[0x40003C]+0x400000:4", "[0x10]+4:8", "0x400000:0x2000"] +
                                [f"{e}:4" for e in dumps.values()])
                code, out, fatal = run(tmp, binp, "X", FATAL_DUMP=spec)
                log = run.stderr
                check("X: an unhandled guest fault is fatal", code != 0 and bool(fatal), True)
                check("X: the fault address and the reason", bool(re.search(
                    r"guest memory fault at guest 0000003C \(not handled by the guest's exception handlers\)", log)), True)
                check("X: the guest thread", bool(re.search(r"guest thread [0-9A-F]{4}", log)), True)
                check("X: the guest registers (as of the call)",
                      bool(re.search(r"ebx=22222222", log)) and bool(re.search(r"esi=55555555 edi=66666666", log)), True)
                check("X: the guest backtrace along the EBP chain", "guest backtrace (ebp chain)" in log, True)
                def first_value(label):
                    m = re.search(re.escape(f"dump {label} = ") + r"([0-9A-F]{8}) \(\d+ bytes\):\n +[0-9A-F]{8}: ([0-9A-F]{8})", log)
                    return (m.group(1), m.group(2)) if m else None
                v = first_value("0x400000")
                check("X: FATAL_DUMP: a plain address is dumped (the DOS header's \"MZ\" in its low word)",
                      (v[0], v[1][4:]) if v else None, ("00400000", "5A4D"))
                v = first_value("[0x40003C]+0x400000")
                check("X: FATAL_DUMP: a dereferenced address (base + e_lfanew) reaches the PE signature",
                      v[1] if v else None, "00004550")
                check("X: FATAL_DUMP: an unreadable address is noted, not faulted",
                      "dump [0x10]+4: unreadable or malformed" in log, True)
                check("X: FATAL_DUMP: a dump is at most 0x1000 bytes",
                      ("dump 0x400000 = 00400000 (4096 bytes):" in log,
                       len(re.findall(r"^    00400[0-9A-F]{3}:", log, re.M)) >= 256,
                       bool(re.search(r"^    00401000:", log, re.M))), (True, True, False))
                v = first_value(dumps["sub"])
                check("X: FATAL_DUMP: subtraction (0x400040 - 4 = e_lfanew's address, 0x40 there)",
                      v, ("0040003C", "00000040"))
                v = first_value(dumps["prec"])
                check("X: FATAL_DUMP: \"*\" binds tighter than \"+\"", v[0] if v else None, "0040003C")
                v = first_value(dumps["sum"])
                check("X: FATAL_DUMP: the sum of two expressions (base + [e_lfanew]) reaches the PE signature",
                      v, ("00400040", "00004550"))
                v = first_value(dumps["mixed"])
                check("X: FATAL_DUMP: a read, a product and a difference, left to right (ImageBase*2 - base + 0x3C)",
                      v, ("0040003C", "00000040"))
                v = first_value(dumps["wrap_add"])
                check("X: FATAL_DUMP: addition wraps at 32 bits", v[0] if v else None, "00400000")
                v = first_value(dumps["wrap_mul"])
                check("X: FATAL_DUMP: multiplication wraps at 32 bits", v[0] if v else None, "00400000")
                for k, why in (("too_big", "a number over 32 bits"), ("signed", "a signed number"),
                               ("mul_expr", "a product by a non-constant"), ("trailing", "trailing text"),
                               ("unclosed", "an unclosed read")):
                    check(f"X: FATAL_DUMP: {why} is malformed", f"dump {dumps[k]}: unreadable or malformed" in log, True)
                v = first_value(dumps["deep8"])
                check("X: FATAL_DUMP: reads nest 8 deep", v[0] if v else None, f"{g.var['xself']:08X}")
                check("X: FATAL_DUMP: a 9th nested read is refused",
                      f"dump {dumps['deep9']}: unreadable or malformed" in log, True)
                m9 = re.search(re.escape(f"dump {dumps['side9']} = ") + r"([0-9A-F]{8})", log)
                check("X: FATAL_DUMP: reads side by side do not count as nested (nine summed)",
                      m9.group(1) if m9 else None, f"{g.var['xself'] * 9 & 0xFFFFFFFF:08X}")
                crashes = os.path.join(tmp, "data", "win32test", "crashes")
                reports = [open(os.path.join(crashes, f)).read() for f in sorted(os.listdir(crashes))] \
                    if os.path.isdir(crashes) else []
                check("X: the same report in the crash file",
                      any("guest memory fault at guest 0000003C" in r and "ebx=22222222" in r for r in reports), True)

            if selected("S"):
                # Mode S: the stall recorder (patch 0018). The make-up of each frame
                # comes from the program: Sleep waits at least its argument (MSDN),
                # the busy loop runs guest code until GetTickCount has advanced 150
                # ms, the reads and the texture are counted by the program.
                with open(os.path.join(tmp, "install", "data.bin"), "wb") as f:
                    f.write(bytes(range(256)) * 16)
                code, out, fatal = run(tmp, binp, "S", STALL="100")
                log = run.stderr
                st = stalls(log)
                check("S: runs to the end", (code, fatal), (0, None))
                check("S: the recorder says it is on", "stall: recording frames over 100.0 ms" in log, True)
                check("S: a short frame is not reported", 3 in st, False)
                check("S: the first frame is timed from the start (t = its length)",
                      1 in st and abs(st[1]["ms"] - st[1]["t"] * 1000) <= 10 + st[1]["t"] * 5, True)
                f3, f4, f5, f6, f7 = (st.get(i, dict(ms=0, phase="", cats={}, text="", imports="", samples=0, guest=[],
                                                     raw=""))
                                      for i in (4, 5, 6, 7, 8))
                check("S: Sleep(160) frames are reported", all(f["ms"] >= 160 for f in (f3, f4, f5)), True)
                check("S: phase before any message is pumped: startup", f3["phase"], "startup")
                check("S: phase of a frame that pumped messages: interactive", f4["phase"], "interactive")
                check("S: phase of a frame without pumping, after pumping: loading", f5["phase"], "loading")
                check("S: the sleep is charged to waits", all(f["cats"].get("wait", 0) >= 155 for f in (f3, f4, f5)), True)
                check("S: and to the Sleep import, called from guest code",
                      bool(re.match(r"\s*Sleep (1[5-9]\d|[2-9]\d\d)\.\d x1 \(longest [\d.]+ from 0040[0-9A-F]{4}\)", f3["imports"])), True)
                check("S: the categories partition the frame",
                      all(abs(sum(f["cats"].values()) - f["ms"]) <= max(1.0, f["ms"] * 0.01) for f in st.values()), True)
                check("S: file reads counted (3 ops, 3 KB)", "file" in f6["cats"] and "(3 ops, 3.0 KB)" in f6["text"], True)
                check("S: the texture upload is texture work", bool(re.search(r"texture [\d.]+ x[1-9]", f6["text"])), True)
                # (GetTickCount counts whole milliseconds: 150 of them may be 149.x ms.)
                check("S: the guest loop is charged to guest code", f7["ms"] >= 145 and
                      f7["cats"].get("guest", 0) >= 0.9 * f7["ms"], True)
                check("S: pure getters are counted, not timed (GetTickCount in the loop)",
                      bool(re.search(r"\| untimed: GetTickCount x([3-9]|\d\d+)", f7["raw"])) and
                      "GetTickCount " not in f7["imports"], True)
                check("S: the sampler names the guest function waiting in Sleep", f3["guest"][:1], ["00401000"])
                check("S: the sampler names the guest function looping", f7["guest"][:1], ["00401000"])
                check("S: samples cover the frame (about one per 2 ms)", f3["samples"] >= 40, True)
                # A report that takes 150 ms (test aid): the next frame shows it as
                # recorder time but is a stall only by its own content.
                code, out, fatal = run(tmp, binp, "S", STALL="100", TEST_STALL_REPORT_MS="150")
                st = stalls(run.stderr)
                check("S: the recorder's own time is shown", st.get(5, {}).get("cats", {}).get("recorder", 0) >= 150, True)
                check("S: and never makes a stall (every report is over 100 ms without it)",
                      bool(st) and all(f["ms"] - f["cats"].get("recorder", 0) > 100 for f in st.values()), True)
                code, out, fatal = run(tmp, binp, "S", STALL="100", STALL_MAX="1")
                log = run.stderr
                check("S: STALL_MAX=1: one report", len(stalls(log)), 1)
                check("S: STALL_MAX=1: then counted only",
                      "stall: 1 reports made; further stalls are counted, not reported" in log, True)
                code, out, fatal = run(tmp, binp, "S")
                check("S: without STALL nothing is recorded", (code, "stall:" in run.stderr), (0, False))
            if selected("T"):
                # Mode T: the recorder's cost per import call (2 million calls;
                # the fastest of three alternating runs each, against noise).
                times = {False: [], True: []}
                for _ in range(3):
                    for recording in (False, True):
                        code, out, fatal = run(tmp, binp, "T", **({"STALL": "100"} if recording else {}))
                        m = re.match(r"T(\d+)", out[0]) if out else None
                        if m:
                            times[recording].append(int(m.group(1)))
                t_off = min(times[False]) if len(times[False]) == 3 else None
                t_on = min(times[True]) if len(times[True]) == 3 else None
                if t_off is not None and t_on is not None:
                    print(f"note: 2M timed import calls: {t_off} ms off, {t_on} ms recording "
                          f"({(t_on - t_off) / 2e6 * 1e6:.0f} ns per call)")
                check("T: recording costs under 1 us per timed import call",
                      t_off is not None and t_on is not None and (t_on - t_off) / 2e6 < 1e-3, True)

            if selected("M"):
                code, out, fatal = run(tmp, binp, "M")
                check("M: runs to the end", (code, fatal), (0, None))
                mm = re.match(r"S([0-9A-F]+),([0-9A-F]+),([0-9A-F]+),([0-9A-F]+):(.*)", out[0] if out else "")
                check("M: log printed", bool(mm), True)
                if mm:
                    cuts = [int(x, 16) for x in mm.groups()[:4]]
                    log = [tuple(int(x, 16) for x in e.split("/")) for e in mm.group(5).split()]
                    cuts.append(len(log))
                    keep = {0x05, 0x06, 0x07, 0x08, 0x1C}  # SIZE, ACTIVATE, SETFOCUS, KILLFOCUS, ACTIVATEAPP
                    segs = [[x for x in log[cuts[i]:cuts[i + 1]] if x[0] in keep] for i in range(4)]
                    # Wine msg.c's minimize/restore sequences (verified there on
                    # Windows): minimized, WM_SIZE(SIZE_MINIMIZED) with an empty
                    # client, then deactivation (WM_ACTIVATE(WA_INACTIVE) with the
                    # minimized flag, WM_ACTIVATEAPP(FALSE), WM_KILLFOCUS); restored,
                    # activation and WM_SIZE(SIZE_RESTORED) with the 100x50 client.
                    minimized = [(0x05, 1, 0), (0x06, 0x10000, 0), (0x1C, 0, 0), (0x08, 0, 0)]
                    restored = [(0x1C, 1, 0), (0x06, 1, 0), (0x07, 0, 0), (0x05, 0, 100 | 50 << 16)]
                    check("M: ShowWindow(SW_MINIMIZE)", segs[0], minimized)
                    check("M: ShowWindow(SW_RESTORE)", segs[1], restored)
                    check("M: DefWindowProc(SC_MINIMIZE) minimizes", segs[2], minimized)
                    check("M: DefWindowProc(SC_RESTORE) restores", segs[3], restored)

            if selected("D"):
                code, out, fatal = run(tmp, binp, "D")
                check("D: runs to the end", (code, fatal), (0, None))
                flags(g.d_names, out, "D")

            if selected("L"):
                code, out, fatal = run(tmp, binp, "L")
                check("L: runs to the end", (code, fatal), (0, None))
                flags(g.gl_names, out, "L")

            if selected("P"):
                code, out, fatal = run(tmp, binp, "P")
                check("P: a plane that does not exist stops the process", code != 0 and code != 9, True)
                check("P: diagnostic", fatal, "wglSwapLayerBuffers(planes 00000002): only the main plane exists")

            if selected("stops"):
                for i, want in enumerate([
                        'EnumDisplayDevicesA("\\\\.\\DISPLAY1"): monitor enumeration is not implemented',
                        "ChangeDisplaySettingsExA: hwnd 00001234 / CDS_VIDEOPARAMETERS not supported",
                        "CreateIoCompletionPort: associating a handle that is not a file is not implemented",
                        "GetProfileStringA: enumerating sections or keys is not implemented",
                        "CreateWindowExA: WS_MINIMIZE (created minimized) is not implemented",
                        "FillRect(hdc 00D00001, (1,2)-(3,4), brush 00E00004): GDI drawing is not implemented",
                        'DrawTextA(hdc 00D00001, "hi", format 00000025): GDI drawing is not implemented',
                        "InvalidateRect(NULL, ...): invalidating the whole desktop is not implemented",
                        "DefWindowProc(WM_ERASEBKGND): erasing with class brush 00E00004 is GDI drawing, "
                        "which is not implemented",
                        "WriteFile on a socket is not implemented",
                        "ReadFile on a socket without an OVERLAPPED is not implemented",
                        "AcceptEx receiving data with the connection is not implemented"]):
                    code, out, fatal = run(tmp, binp, chr(0x31 + i))
                    check(f"stop {i + 1}: an unimplemented form stops the process", code != 0 and code != 9, True)
                    check(f"stop {i + 1}: diagnostic", fatal, want)
    subset = "" if SELECTED is None else f" (modes {','.join(g for g in MODE_GROUPS if g in SELECTED)} only)"
    print(("ALL PASS" if not failures else f"{failures} FAILED") + subset)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
