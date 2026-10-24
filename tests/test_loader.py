#!/usr/bin/env python3
"""End-to-end tests for reFrozen's x86recomp loader patch 0007 (no game data).

  /opt/homebrew/bin/python3 -I tests/test_loader.py

Three tiny PE32 modules are assembled here (llvm-mc), lifted together with
recomp_lift, linked with the runtime and run as one process, the way war3.exe,
Storm.dll and game.dll are:

  a.dll  exports Log (named, #1) and Buf (ordinal only, #2); its DllMain logs
         'A' on attach, 'a' on detach
  b.dll  imports a.dll!Log by name; DllMain logs 'B' / 'b'; exports BFn ('F')
  c.dll  imports a.dll!Log; DllMain 'C' / 'c'; loaded only with LoadLibrary
  t.exe  imports b.dll!BFn, then a.dll #2 by ordinal and a.dll!Log; logs
         'E', calls BFn, loads and frees c.dll, frees a.dll and b.dll (static
         loads: pinned), then prints the log (and a newline) with
         OutputDebugStringA

and its last command-line character picks a failure to provoke: S calls a
kernel32 import with no handler, J branches into the middle of a function, N
calls an address where nothing is mapped; H checks the kernel32 functions of
patch 0008 and logs 1 (or 0) per check.

Needs scripts/setup_tools.sh (tools/x86recomp built) and Homebrew LLVM.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.path.join(ROOT, "tools", "x86recomp")
BUILD = os.path.join(X86, "out", "build", "debug")
LIFT = os.path.join(BUILD, "tools", "lifter", "recomp_lift")
LLVM = "/opt/homebrew/opt/llvm/bin"
CXX = os.path.join(LLVM, "clang++")
EXEC, RW = 0x60000020, 0xC0000040
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    if not ok:
        failures += 1
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


class Data:
    """The .data section (RVA 0x2000): import and export directories, strings."""

    def __init__(self, base):
        self.base, self.va0, self.b = base, base + 0x2000, bytearray()

    def put(self, blob, align=4):
        self.b += b"\0" * (-len(self.b) % align)
        va = self.va0 + len(self.b)
        self.b += blob
        return va

    def rva(self, va):
        return va - self.base

    def imports(self, dlls):
        """dlls: [(name, [symbol name or ordinal int])]; returns the IAT slot VA
        of each (dll, symbol) and the import directory (rva, size)."""
        desc = self.put(b"\0" * 20 * (len(dlls) + 1))
        iat = {}
        for i, (dll, syms) in enumerate(dlls):
            entries = []
            for s in syms:
                entries.append(0x80000000 | s if isinstance(s, int)
                               else self.rva(self.put(b"\0\0" + s.encode() + b"\0", 2)))
            ilt = self.put(struct.pack(f"<{len(entries) + 1}I", *entries, 0))
            slots = self.put(struct.pack(f"<{len(entries) + 1}I", *entries, 0))
            for k, s in enumerate(syms):
                iat[(dll, s)] = slots + 4 * k
            name = self.put(dll.encode() + b"\0")
            off = desc - self.va0 + 20 * i
            self.b[off:off + 20] = struct.pack("<IIIII", self.rva(ilt), 0, 0, self.rva(name), self.rva(slots))
        return iat, (self.rva(desc), 20 * (len(dlls) + 1))

    def exports(self, dll, funcs):
        """funcs: [(ordinal from 1, name or None, rva)]; returns (rva, size)."""
        start = len(self.b) + (-len(self.b) % 4)
        named = sorted((n, o) for o, n, _ in funcs if n)
        eat = [0] * max(o for o, _, _ in funcs)
        for o, _, r in funcs:
            eat[o - 1] = r
        d = self.put(b"\0" * 40)
        eat_va = self.put(struct.pack(f"<{len(eat)}I", *eat))
        names = [self.rva(self.put(n.encode() + b"\0", 1)) for n, _ in named]
        names_va = self.put(struct.pack(f"<{len(names)}I", *names))
        ords_va = self.put(struct.pack(f"<{len(named)}H", *[o - 1 for _, o in named]), 2)
        dll_name = self.put(dll.encode() + b"\0", 1)
        off = d - self.va0
        self.b[off:off + 40] = struct.pack("<IIHHIIIIII", 0, 0, 0, 0, self.rva(dll_name), 1, len(eat),
                                           len(named), self.rva(eat_va), self.rva(names_va)) + \
            struct.pack("<I", self.rva(ords_va))
        return self.rva(d), len(self.b) - start


def assemble(tmp, src):
    s, o, b = (os.path.join(tmp, "m." + x) for x in ("s", "o", "bin"))
    with open(s, "w") as f:
        f.write(".intel_syntax noprefix\n.text\n" + src)
    subprocess.run([os.path.join(LLVM, "llvm-mc"), "-triple=i386-unknown-linux-gnu", "-filetype=obj",
                    "-o", o, s], check=True)
    subprocess.run([os.path.join(LLVM, "llvm-objcopy"), "-O", "binary", "--only-section=.text", o, b],
                   check=True)
    return open(b, "rb").read()


def image(base, text, data, dll, import_dir, export_dir=(0, 0)):
    pad = lambda blob: blob + b"\0" * (-len(blob) % 0x200)
    secs = [(b".text", 0x1000, pad(text), EXEC), (b".data", 0x2000, pad(bytes(data.b)), RW)]
    hdr = bytearray(0x200)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, 0x40)
    hdr[0x40:0x44] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", hdr, 0x44, 0x14C, 2, 0, 0, 0, 0xE0, 0x2102 if dll else 0x0102)
    opt = 0x58
    struct.pack_into("<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII", hdr, opt,
                     0x10B, 8, 0, len(secs[0][2]), len(secs[1][2]), 0, 0x1000, 0x1000, 0x2000,
                     base, 0x1000, 0x200, 4, 0, 0, 0, 4, 0, 0, 0x3000, 0x200, 0, 2, 0,
                     0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    struct.pack_into("<II", hdr, opt + 96, *export_dir)
    struct.pack_into("<II", hdr, opt + 96 + 8, *import_dir)
    raw, body = 0x200, b""
    for i, (name, rva, blob, ch) in enumerate(secs):
        o = opt + 0xE0 + 40 * i
        hdr[o:o + 8] = name.ljust(8, b"\0")
        struct.pack_into("<IIIIIIHHI", hdr, o + 8, 0x1000, rva, len(blob), raw + len(body), 0, 0, 0, 0, ch)
        body += blob
    return bytes(hdr) + body


A, B, C, EXE = 0x10000000, 0x10100000, 0x10200000, 0x00400000

# DllMain(h, reason, reserved) at .text+0 logging `ch` on attach, lower case
# on detach (stdcall, returns TRUE).
DLLMAIN = """
dllmain:
  mov eax, 0x{ch:02X}
  cmp dword ptr [esp+8], 1
  je 1f
  or eax, 0x20
1:
  push eax
  call dword ptr [{log}]
  mov eax, 1
  ret 12
"""


def build(tmp):
    """Writes the four modules into tmp/install; returns their function entries."""
    os.makedirs(os.path.join(tmp, "install"), exist_ok=True)
    entries = {}

    def emit(name, base, src, data, import_dir, export_dir=(0, 0), funcs=(0,)):
        text = assemble(tmp, src)
        with open(os.path.join(tmp, "install", name), "wb") as f:
            f.write(image(base, text, data, name != "t.exe", import_dir, export_dir))
        entries[name] = [base + 0x1000 + o for o in funcs]

    # a.dll: buf at .data+0x800 (32 bytes), n at +0x820. The log is written
    # here; DllMain calls Log through an internal call.
    d = Data(A)
    buf, n = A + 0x2800, A + 0x2820
    exports = d.exports("a.dll", [(1, "Log", 0x1040), (2, None, 0x1080)])
    d.b += b"\0" * (0x828 - len(d.b))
    src = f"""
  mov eax, 0x41
  cmp dword ptr [esp+8], 1
  je 1f
  or eax, 0x20
1:
  push eax
  call log
  mov eax, 1
  ret 12
.org 0x40, 0xCC
log:
  mov ecx, dword ptr [{n:#x}]
  mov al, byte ptr [esp+4]
  mov byte ptr [{buf:#x}+ecx], al
  inc ecx
  mov dword ptr [{n:#x}], ecx
  ret 4
.org 0x80, 0xCC
  mov eax, {buf:#x}
  ret
"""
    emit("a.dll", A, src, d, (0, 0), exports, (0, 0x40, 0x80))

    d = Data(B)
    iat, imp = d.imports([("a.dll", ["Log"])])
    exports = d.exports("b.dll", [(1, "BFn", 0x1040)])
    src = DLLMAIN.format(ch=ord("B"), log=hex(iat[("a.dll", "Log")])) + f"""
.org 0x40, 0xCC
  push 0x46
  call dword ptr [{iat[("a.dll", "Log")]:#x}]
  ret
"""
    emit("b.dll", B, src, d, imp, exports, (0, 0x40))

    d = Data(C)
    iat, imp = d.imports([("a.dll", ["Log"])])
    emit("c.dll", C, DLLMAIN.format(ch=ord("C"), log=hex(iat[("a.dll", "Log")])), d, imp)

    d = Data(EXE)
    k32 = ["LoadLibraryA", "FreeLibrary", "GetModuleHandleA", "OutputDebugStringA", "ExitProcess",
           "GetCommandLineA", "Beep", "GetLastError", "InterlockedCompareExchange", "GetWindowsDirectoryA",
           "SetCurrentDirectoryA", "DisableThreadLibraryCalls", "GetCommandLineW"]
    # b.dll first: a.dll must still attach first, being b.dll's dependency.
    iat, imp = d.imports([("b.dll", ["BFn"]), ("a.dll", [2, "Log"]), ("kernel32.dll", k32)])
    s = {k: d.put(k.encode() + b"\0", 1) for k in ("a.dll", "b.dll", "c.dll", "C:\\T", "C:\\T\\a.dll")}
    var, wbuf = d.put(b"\0" * 4), d.put(b"\0" * 64)
    I = lambda dll, sym: f"dword ptr [{iat[(dll, sym)]:#x}]"
    K = lambda sym: I("kernel32.dll", sym)
    src = f"""
  push 0x45
  call {I("a.dll", "Log")}
  call {I("b.dll", "BFn")}
  push {s["c.dll"]:#x}
  call {K("LoadLibraryA")}
  push eax
  call {K("FreeLibrary")}
  push {s["a.dll"]:#x}
  call {K("GetModuleHandleA")}
  push eax
  call {K("FreeLibrary")}
  push {s["b.dll"]:#x}
  call {K("GetModuleHandleA")}
  push eax
  call {K("FreeLibrary")}
  push 0x0A
  call {I("a.dll", "Log")}
  call {I("a.dll", 2)}
  push eax
  call {K("OutputDebugStringA")}
  call {K("GetCommandLineA")}
1:
  cmp byte ptr [eax+1], 0
  je 2f
  inc eax
  jmp 1b
2:
  movzx eax, byte ptr [eax]
  cmp eax, 0x53
  je stub
  cmp eax, 0x4A
  je jump
  cmp eax, 0x4E
  je nowhere
  cmp eax, 0x48
  je hle
  push 0
  call {K("ExitProcess")}
stub:
  push 100
  push 440
  call {K("Beep")}
  push 1
  call {K("ExitProcess")}
jump:
  call 3f
3:
  pop eax
  inc eax
  call eax
  push 2
  call {K("ExitProcess")}
nowhere:
  mov eax, 0x7FFF0000
  call eax
  push 3
  call {K("ExitProcess")}
flag:
  sete al
  movzx eax, al
  add eax, 0x30
  push eax
  call {I("a.dll", "Log")}
  ret
hle:
  mov dword ptr [{var:#x}], 5
  push 5
  push 7
  push {var:#x}
  call {K("InterlockedCompareExchange")}
  cmp eax, 5
  call flag
  cmp dword ptr [{var:#x}], 7
  call flag
  push 5
  push 9
  push {var:#x}
  call {K("InterlockedCompareExchange")}
  cmp eax, 7
  call flag
  cmp dword ptr [{var:#x}], 7
  call flag
  push 64
  push {wbuf:#x}
  call {K("GetWindowsDirectoryA")}
  cmp eax, 10
  call flag
  cmp dword ptr [{wbuf:#x}], 0x575C3A43
  call flag
  push 4
  push {wbuf:#x}
  call {K("GetWindowsDirectoryA")}
  cmp eax, 11
  call flag
  push {s["C:\\T"]:#x}
  call {K("SetCurrentDirectoryA")}
  cmp eax, 1
  call flag
  push {s["C:\\T\\a.dll"]:#x}
  call {K("SetCurrentDirectoryA")}
  cmp eax, 0
  call flag
  call {K("GetLastError")}
  cmp eax, 267
  call flag
  push {A:#x}
  call {K("DisableThreadLibraryCalls")}
  cmp eax, 1
  call flag
  push 0x12340000
  call {K("DisableThreadLibraryCalls")}
  cmp eax, 0
  call flag
  call {K("GetLastError")}
  cmp eax, 126
  call flag
  call {K("GetCommandLineW")}
  mov esi, eax
  call {K("GetCommandLineA")}
  movzx ecx, byte ptr [eax]
  movzx edx, word ptr [esi]
  cmp ecx, edx
  call flag
  push 0x0A
  call {I("a.dll", "Log")}
  call {I("a.dll", 2)}
  push eax
  call {K("OutputDebugStringA")}
  push 0
  call {K("ExitProcess")}
"""
    emit("t.exe", EXE, src, d, imp)
    return entries


HARNESS = r"""
#include <string>
#include "runtime/runtime.h"
int main(int argc, char** argv) {
  recomp::GameConfig g;
  g.id = "loadertest";
  g.guest_dir = "C:\\T";
  g.exe_name = "t.exe";
  for (int i = 3; i < argc; i++) g.lifted_dlls.push_back({argv[i]});
  return recomp::RunProcess(g, std::string(argv[1]) + "/t.exe", argv[1], argv[2]);
}
"""


def lift_and_link(tmp, entries):
    inst, gen = os.path.join(tmp, "install"), os.path.join(tmp, "gen")
    args = []
    for name in ("t.exe", "a.dll", "b.dll", "c.dll"):
        sym = os.path.join(tmp, "sym", name)
        os.makedirs(sym, exist_ok=True)
        with open(os.path.join(sym, "functions.tsv"), "w") as f:
            f.write("entry\tmin\tmax\tchunks\tthunk\tnoreturn\tcallconv\tname\n")
            for e in entries[name]:
                f.write(f"{e:08X}\t{e:08X}\t{e:08X}\t1\t0\t0\t__stdcall\tFUN_{e:08X}\n")
        for n, h in (("exports.tsv", "va\tkind\tmangled\tdemangled\n"), ("jumptables.tsv", "jmp\ttargets\n")):
            with open(os.path.join(sym, n), "w") as f:
                f.write(h)
        man = os.path.join(sym, "m.manifest")
        open(man, "w").close()
        args += ["--exe" if name == "t.exe" else "--module", os.path.join(inst, name), "--symbols", sym,
                 "--manifest", man]
    r = subprocess.run([LIFT, *args, "--out", gen], capture_output=True, text=True)
    check("lift of the four modules succeeds", r.returncode, 0)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return None
    with open(os.path.join(tmp, "harness.cpp"), "w") as f:
        f.write(HARNESS)
    binp = os.path.join(tmp, "loadertest")
    srcs = [os.path.join(gen, n) for n in sorted(os.listdir(gen)) if n.endswith(".cpp")]
    cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-fno-strict-aliasing", "-fnon-call-exceptions",
                         "-ffp-contract=off", "-fno-omit-frame-pointer", "-I", os.path.join(X86, "src"),
                         os.path.join(tmp, "harness.cpp"), *srcs,
                         os.path.join(X86, "src", "runtime", "lifted_table.cpp"),
                         "-L", BUILD, "-lrecomp_runtime", "-lrecomp_x87", "-lrecomp_image",
                         "-Wl,-rpath," + BUILD, "-o", binp], capture_output=True, text=True)
    check("lifted modules link with the runtime", cc.returncode, 0)
    if cc.returncode:
        print(cc.stderr[:3000])
        return None
    return binp


def run(tmp, binp, mode, dlls=("a.dll", "b.dll", "c.dll")):
    env = dict(os.environ, XDG_DATA_HOME=os.path.join(tmp, "data"), LOADERTEST_BACKGROUND="1")
    r = subprocess.run([binp, os.path.join(tmp, "install"), mode, *dlls], capture_output=True, text=True,
                       env=env, timeout=60)
    err = r.stderr
    log = re.search(r"\[guest\] (\S*)", err)
    fatal = re.search(r"FATAL: (.*)", err)
    return r.returncode, log.group(1) if log else None, fatal.group(1) if fatal else None, err


def main():
    with tempfile.TemporaryDirectory() as tmp:
        binp = lift_and_link(tmp, build(tmp))
        if binp:
            code, log, fatal, err = run(tmp, binp, "-")
            # Static imports: a.dll (imported by b.dll and t.exe) attaches first,
            # then b.dll, before the EXE entry. c.dll attaches on LoadLibrary and
            # detaches on FreeLibrary; FreeLibrary of a.dll and b.dll does not
            # unload a static import. #2 resolved by ordinal returned the buffer.
            check("DllMain order, ordinal + name binding, pinned static loads", log, "ABEFCc")
            check("clean exit", (code, fatal), (0, None))

            code, log, fatal, err = run(tmp, binp, "S")
            check("no-handler import stops the process", code != 0, True)
            check("no-handler import diagnostic", re.sub(r"\(return address [0-9A-F]+\)", "", fatal or ""),
                  "unimplemented import kernel32.dll!Beep called ")

            code, log, fatal, err = run(tmp, binp, "J")
            check("branch into a function stops the process", code != 0, True)
            want = re.compile(r"indirect branch from 004010[0-9A-F]{2} \(t\.exe\+0x10[0-9A-F]{2}\) to "
                              r"004010[0-9A-F]{2} \(t\.exe\+0x10[0-9A-F]{2}\): not a lifted function entry; "
                              r"it lies after f_00401000 \(t\.exe\+0x1000\)\. If it is one, add \"entry "
                              r"004010[0-9A-F]{2}\" to the module's manifest")
            check("branch into a function diagnostic", bool(fatal and want.match(fatal)), True)
            if not (fatal and want.match(fatal)):
                print("   ", fatal)

            code, log, fatal, err = run(tmp, binp, "N")
            check("branch to unmapped memory stops the process", code != 0, True)
            check("branch to unmapped memory diagnostic",
                  bool(fatal and re.match(r"indirect branch from 004010[0-9A-F]{2} \(t\.exe\+0x10[0-9A-F]{2}\) "
                                          r"to 7FFF0000: not in any lifted module's code", fatal)), True)

            code, log, fatal, err = run(tmp, binp, "H")
            # InterlockedCompareExchange swaps on a match (returns 5, now 7) and
            # not on a mismatch (returns 7); GetWindowsDirectoryA gives
            # "C:\WINDOWS" (10) or the size it needs (11); SetCurrentDirectoryA
            # takes a directory, refuses a file with ERROR_DIRECTORY (267);
            # DisableThreadLibraryCalls takes a loaded DLL, refuses anything else
            # with ERROR_MOD_NOT_FOUND (126); GetCommandLineW matches the A form.
            check("patch 0008 kernel32 functions", code, 0)
            check("patch 0008 kernel32 results", re.findall(r"^[01]+$", err, re.M), ["1" * 14])

            # An importer listed before what it imports cannot bind.
            code, log, fatal, err = run(tmp, binp, "-", ("b.dll", "a.dll", "c.dll"))
            check("importer mapped before its import is refused",
                  fatal, "import a.dll!Log: a.dll is not mapped yet (list it before its importers "
                         "in lifted_dlls)")
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
