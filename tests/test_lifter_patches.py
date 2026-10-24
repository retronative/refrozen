#!/usr/bin/env python3
"""End-to-end, hand-computed tests for reFrozen's x86recomp patches 0002 and
0003 (no game data): tiny PE32 images are written here, lifted with
recomp_lift, and for 0003 compiled for the host and run.

  /opt/homebrew/bin/python3 -I tests/test_lifter_patches.py

Needs scripts/setup_tools.sh (tools/x86recomp built) and Homebrew LLVM.
Expected values come from the Intel SDM, worked out in the comments.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# tests/mutate.py points these at its scratch tree.
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
BUILD = os.environ.get("REFROZEN_X86RECOMP_BUILD", os.path.join(X86, "out", "build", "debug"))
LIFT = os.path.join(BUILD, "tools", "lifter", "recomp_lift")
CXX = "/opt/homebrew/opt/llvm/bin/clang++"
BASE = 0x00100000            # image base: everything below the 4 MiB test arena
TEXT, DATA = BASE + 0x1000, BASE + 0x2000
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    if not ok:
        failures += 1
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


EXEC, RW = 0x60000020, 0xC0000040


def pad(b, n):
    return b + b"\0" * (-len(b) % n)


def pe(text, data, relocs=None):
    """PE32 image: .text at TEXT, .data at DATA, optional .reloc (HIGHLOW
    sites given as VAs)."""
    return pe_sections([(b".text", text, EXEC), (b".data", data, RW)], relocs)


def pe_sections(sections, relocs=None, export=None):
    """PE32 image with the given (name, bytes, characteristics) sections at
    RVA 0x1000, 0x2000, ...; export = (name, rva, rva of a writable section to
    hold the export directory) adds one named export."""
    secs = [(name, 0x1000 * (i + 1), pad(blob, 0x200), ch) for i, (name, blob, ch) in enumerate(sections)]
    export_dir = (0, 0)
    if export:
        name, target, at = export
        # IMAGE_EXPORT_DIRECTORY, then EAT, name pointers, ordinals, strings
        d = at + 40
        blob = struct.pack("<IIHHIIIIIII", 0, 0, 0, 0, d + 12, 1, 1, 1, d, d + 4, d + 8)
        blob += struct.pack("<IIHH", target, d + 20, 0, 0) + b"t.exe\0\0\0" + name.encode() + b"\0"
        i = next(k for k, s in enumerate(secs) if s[1] == at)
        n, rva, raw, ch = secs[i]
        secs[i] = (n, rva, pad(blob, 0x200), ch)
        export_dir = (at, len(blob))
    reloc_dir = (0, 0)
    if relocs is not None:
        blocks = b""
        pages = sorted({(va - BASE) & ~0xFFF for va in relocs})
        for page in pages:
            ents = [0x3000 | ((va - BASE) & 0xFFF) for va in relocs if (va - BASE) & ~0xFFF == page]
            if len(ents) % 2:
                ents.append(0)
            blocks += struct.pack("<II", page, 8 + 2 * len(ents)) + struct.pack(f"<{len(ents)}H", *ents)
        reloc_rva = 0x1000 * (len(secs) + 1)
        secs.append((b".reloc", reloc_rva, pad(blocks, 0x200), 0x42000040))
        reloc_dir = (reloc_rva, len(blocks))
    image_size = 0x1000 * (len(secs) + 1)
    hdr = bytearray(0x200)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, 0x40)
    hdr[0x40:0x44] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", hdr, 0x44, 0x14C, len(secs), 0, 0, 0, 0xE0, 0x0102)
    opt = 0x58
    struct.pack_into("<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII", hdr, opt,
                     0x10B, 8, 0, len(secs[0][2]), len(secs[1][2]), 0, 0x1000, 0x1000, 0x2000,
                     BASE, 0x1000, 0x200, 4, 0, 0, 0, 4, 0, 0, image_size, 0x200, 0, 2, 0,
                     0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    struct.pack_into("<II", hdr, opt + 96, *export_dir)
    struct.pack_into("<II", hdr, opt + 96 + 5 * 8, *reloc_dir)
    raw = 0x200
    body = b""
    for i, (name, rva, blob, ch) in enumerate(secs):
        o = opt + 0xE0 + 40 * i
        hdr[o:o + 8] = name.ljust(8, b"\0")
        struct.pack_into("<IIIIIIHHI", hdr, o + 8, 0x1000, rva, len(blob), raw + len(body), 0, 0, 0, 0, ch)
        body += blob
    return bytes(hdr) + body


def lift(tmp, image, entries, manifest="", jumptables=()):
    exe = os.path.join(tmp, "t.exe")
    sym = os.path.join(tmp, "sym")
    out = os.path.join(tmp, "gen")
    os.makedirs(sym, exist_ok=True)
    with open(exe, "wb") as f:
        f.write(image)
    with open(os.path.join(sym, "functions.tsv"), "w") as f:
        f.write("entry\tmin\tmax\tchunks\tthunk\tnoreturn\tcallconv\tname\n")
        for e in entries:
            f.write(f"{e:08X}\t{e:08X}\t{e:08X}\t1\t0\t0\t__cdecl\tFUN_{e:08X}\n")
    for n, h in (("exports.tsv", "va\tkind\tmangled\tdemangled\n"), ("jumptables.tsv", "jmp\ttargets\n")):
        with open(os.path.join(sym, n), "w") as f:
            f.write(h)
    with open(os.path.join(sym, "jumptables.tsv"), "a") as f:
        for jmp, targets in jumptables:
            f.write(f"{jmp:08X}\t" + ",".join(f"{t:08X}" for t in targets) + "\n")
    with open(os.path.join(tmp, "m.manifest"), "w") as f:
        f.write(manifest)
    r = subprocess.run([LIFT, "--exe", exe, "--symbols", sym, "--manifest", os.path.join(tmp, "m.manifest"),
                        "--out", out], capture_output=True, text=True)
    fns = set()
    if os.path.isdir(out):
        for n in os.listdir(out):
            if n.startswith("gen_"):
                fns |= {int(v, 16) for v in re.findall(r"^void f_([0-9A-F]{8})\(", open(os.path.join(out, n)).read(), re.M)}
    return r, fns, out


# ---- 0002: pointer scans only take relocated pointers -------------------------

def test_reloc_discovery():
    # main at TEXT: mov eax, TEXT+0x400 (relocated); mov ecx, TEXT+0x500 (not); ret
    main = b"\xB8" + struct.pack("<I", TEXT + 0x400) + b"\xB9" + struct.pack("<I", TEXT + 0x500) + b"\xC3"
    text = bytearray(b"\xCC" * 0x600)
    text[0:len(main)] = main
    for off in (0x200, 0x300, 0x400, 0x500):  # four plausible functions: xor eax,eax; ret
        text[off:off + 3] = b"\x31\xC0\xC3"
    # .data: dword 0 -> TEXT+0x200 (relocated), dword 1 -> TEXT+0x300 (not)
    data = struct.pack("<II", TEXT + 0x200, TEXT + 0x300)
    relocs = [DATA, TEXT + 1]  # the data slot and main's first immediate
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, _ = lift(tmp, pe(bytes(text), data, relocs), [TEXT])
        check("0002 lift succeeds", r.returncode, 0)
        check("0002 relocated data pointer is an entry", TEXT + 0x200 in fns, True)
        check("0002 unrelocated data dword is not", TEXT + 0x300 in fns, False)
        check("0002 relocated immediate is an entry", TEXT + 0x400 in fns, True)
        check("0002 unrelocated immediate is not", TEXT + 0x500 in fns, False)
    with tempfile.TemporaryDirectory() as tmp:  # no .reloc: the plain heuristic
        r, fns, _ = lift(tmp, pe(bytes(text), data, None), [TEXT])
        check("0002 without relocations every candidate counts",
              all(TEXT + o in fns for o in (0x200, 0x300, 0x400, 0x500)), True)
    with tempfile.TemporaryDirectory() as tmp:  # manifest "data" refuses a candidate
        r, fns, _ = lift(tmp, pe(bytes(text), data, None), [TEXT], f"data {TEXT + 0x300:08X}\n")
        check("0002 manifest data refuses the candidate", TEXT + 0x300 in fns, False)
    with tempfile.TemporaryDirectory() as tmp:  # ...and may not name a real entry
        r, _, _ = lift(tmp, pe(bytes(text), data, None), [TEXT], f"data {TEXT:08X}\n")
        check("0002 manifest data on an entry fails the lift", r.returncode != 0, True)


# ---- 0003: MMX, x87 run boundary, movhps/movntps/sfence -------------------------

# ebx = DATA on entry. Data layout:
#   +0  dword 80FF7F01   +8  qword F0E0D0C090807060   +16 qword 0F0F0F0FF0F0F0F0
#   +24 (out qword)      +32 qword 8877665544332211  +48 (out, 16-aligned)
MMX_CODE = bytes([
    0x0F, 0x6E, 0xC0,              # movd mm0, eax          mm0 = 0000000011223344
    0x0F, 0x6E, 0x0B,              # movd mm1, [ebx]        mm1 = 0000000080FF7F01
    0x0F, 0x6F, 0xD0,              # movq mm2, mm0
    0x0F, 0x73, 0xF2, 0x20,        # psllq mm2, 32          mm2 = 1122334400000000
    0x0F, 0xEB, 0xD1,              # por mm2, mm1           mm2 = 1122334480FF7F01
    0x0F, 0x6F, 0x5B, 0x08,        # movq mm3, [ebx+8]      mm3 = F0E0D0C090807060
    0x0F, 0xDC, 0xDA,              # paddusb mm3, mm2       bytes 60+01=61, 70+7F=EF,
                                   #   80+FF, 90+80, C0+44, D0+33, E0+22, F0+11 saturate:
                                   #   mm3 = FFFFFFFFFFFFEF61
    0x0F, 0xDB, 0x5B, 0x10,        # pand mm3, [ebx+16]     mm3 = 0F0F0F0FF0F0E060
    0x0F, 0x73, 0xD2, 0x40,        # psrlq mm2, 64          count > 63: mm2 = 0
    0x0F, 0x7F, 0x5B, 0x18,        # movq [ebx+24], mm3
    0x0F, 0x7E, 0xD9,              # movd ecx, mm3          ecx = F0F0E060
    0xC3])
EMMS_CODE = bytes([0x0F, 0x77, 0xC3])                     # emms; ret
RUN_CODE = bytes([0xD9, 0xE8,                             # fld1
                  0x0F, 0x6F, 0x43, 0x08,                 # movq mm0, [ebx+8]
                  0xD9, 0xE8,                             # fld1
                  0xC3])
# +64 qword FFFF000000012345 (dwords 00012345, FFFF0000)
PACK_CODE = bytes([
    0x0F, 0x6F, 0x63, 0x40,        # movq mm4, [ebx+64]
    0x0F, 0x6F, 0xEC,              # movq mm5, mm4
    0x0F, 0x72, 0xE4, 0x04,        # psrad mm4, 4    dwords 00001234, FFFFF000
    0x0F, 0x72, 0xE5, 0x28,        # psrad mm5, 40   count > 31: sign fill 00000000, FFFFFFFF
    0x0F, 0x6B, 0xE5,              # packssdw mm4, mm5  words 1234 F000 | 0000 FFFF:
                                   #   mm4 = FFFF0000F0001234 (all in range)
    0x0F, 0x6F, 0x73, 0x40,        # movq mm6, [ebx+64]
    0x0F, 0x6B, 0x73, 0x40,        # packssdw mm6, [ebx+64]  00012345 -> 7FFF, FFFF0000 -> 8000:
                                   #   mm6 = 80007FFF80007FFF
    0x0F, 0x6F, 0xFC,              # movq mm7, mm4
    0x0F, 0x71, 0xE7, 0x08,        # psraw mm7, 8    words 0012 FFF0 0000 FFFF
    0x0F, 0x63, 0xFC,              # packsswb mm7, mm4  bytes 12 F0 00 FF | 7F 80 00 FF:
                                   #   mm7 = FF00807FFF00F012
    0xC3])
SSE_CODE = bytes([0x0F, 0x16, 0x43, 0x20,                 # movhps xmm0, [ebx+32]
                  0x0F, 0x2B, 0x43, 0x30,                 # movntps [ebx+48], xmm0
                  0x0F, 0xAE, 0xF8,                       # sfence
                  0xC3])

HARNESS = r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "runtime/lifted.h"
namespace recomp {
uint8_t* g_guest_base = nullptr;
void Unimplemented(Ctx&, uint32_t va, const char* w) { std::printf("unimplemented %08X %s\n", va, w); std::exit(3); }
void BadJump(Ctx&, uint32_t a, uint32_t b) { std::printf("bad jump %08X %08X\n", a, b); std::exit(3); }
void RaiseDivideError(Ctx&, uint32_t) { std::exit(3); }
namespace gen { void f_@MMX@(Ctx&); void f_@EMMS@(Ctx&); void f_@RUN@(Ctx&); void f_@SSE@(Ctx&); void f_@PACK@(Ctx&); }
}
using namespace recomp;
static Ctx Fresh() {
  Ctx c{};
  c.esp = 0x2FFFF0; lift::Wr<uint32_t>(g_guest_base, c.esp, 0xDEADBEEF);
  c.ebx = 0x@DATA@; c.eflags = 0x202; c.mxcsr = 0x1F80;
  c.fpu.cw = 0x27F; c.fpu.top = 5; c.fpu.empty = 0xFF;
  for (auto& r : c.fpu.r) { r.sig = 0x0123456789ABCDEFull; r.se = 0x1234; }
  return c;
}
int main() {
  g_guest_base = static_cast<uint8_t*>(std::calloc(1, 0x400000));
  uint8_t* d = g_guest_base + 0x@DATA@;
  lift::Wr<uint32_t>(g_guest_base, 0x@DATA@, 0x80FF7F01u);
  lift::Wr<uint64_t>(g_guest_base, 0x@DATA@ + 8, 0xF0E0D0C090807060ull);
  lift::Wr<uint64_t>(g_guest_base, 0x@DATA@ + 16, 0x0F0F0F0FF0F0F0F0ull);
  lift::Wr<uint64_t>(g_guest_base, 0x@DATA@ + 32, 0x8877665544332211ull);
  lift::Wr<uint64_t>(g_guest_base, 0x@DATA@ + 64, 0xFFFF000000012345ull);
  Ctx c = Fresh(); c.eax = 0x11223344;
  gen::f_@MMX@(c);
  std::printf("mm %016llX %016llX %016llX %016llX\n", (unsigned long long)c.fpu.r[0].sig,
              (unsigned long long)c.fpu.r[1].sig, (unsigned long long)c.fpu.r[2].sig, (unsigned long long)c.fpu.r[3].sig);
  std::printf("se %04X %04X %04X %04X %04X\n", c.fpu.r[0].se, c.fpu.r[1].se, c.fpu.r[2].se, c.fpu.r[3].se, c.fpu.r[4].se);
  std::printf("state top=%u empty=%02X ecx=%08X out=%016llX esp=%08X\n", c.fpu.top, c.fpu.empty, c.ecx,
              (unsigned long long)lift::Rd<uint64_t>(g_guest_base, 0x@DATA@ + 24), c.esp);
  gen::f_@EMMS@(c);
  std::printf("emms top=%u empty=%02X\n", c.fpu.top, c.fpu.empty);
  c = Fresh();
  gen::f_@RUN@(c);
  std::printf("run top=%u empty=%02X r4=%016llX/%04X r0=%016llX r7=%016llX/%04X sw=%04X\n", c.fpu.top,
              c.fpu.empty, (unsigned long long)c.fpu.r[4].sig, c.fpu.r[4].se, (unsigned long long)c.fpu.r[0].sig,
              (unsigned long long)c.fpu.r[7].sig, c.fpu.r[7].se, c.fpu.sw & 0x0241);
  c = Fresh();
  for (int i = 0; i < 16; i++) c.xmm[0].b[i] = uint8_t(0xA0 + i);
  gen::f_@SSE@(c);
  Ctx p = Fresh();
  gen::f_@PACK@(p);
  std::printf("pack %016llX %016llX %016llX %016llX\n", (unsigned long long)p.fpu.r[4].sig,
              (unsigned long long)p.fpu.r[5].sig, (unsigned long long)p.fpu.r[6].sig, (unsigned long long)p.fpu.r[7].sig);
  std::printf("sse");
  for (int i = 0; i < 16; i++) std::printf(" %02X", d[48 + i]);
  std::printf("\n");
}
"""


def test_mmx_sse():
    text = bytearray(b"\xCC" * 0x400)
    offs = {"MMX": 0x000, "EMMS": 0x100, "RUN": 0x180, "SSE": 0x200, "PACK": 0x280}
    for k, code in (("MMX", MMX_CODE), ("EMMS", EMMS_CODE), ("RUN", RUN_CODE), ("SSE", SSE_CODE),
                    ("PACK", PACK_CODE)):
        text[offs[k]:offs[k] + len(code)] = code
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, out = lift(tmp, pe(bytes(text), b"\0" * 0x40, None), [TEXT + o for o in offs.values()])
        check("0003 lift succeeds", r.returncode, 0)
        report = open(os.path.join(out, "lift_report.txt")).read() if os.path.isdir(out) else ""
        check("0003 no unimplemented sites", re.search(r"unimplemented:\n(\s+\S.*\n)*warnings", report).group(0).count("\n") - 1, 0)
        names = {k: f"{TEXT + o:08X}" for k, o in offs.items()}
        harness = HARNESS.replace("@DATA@", f"{DATA:X}")
        for k, v in names.items():
            harness = harness.replace(f"@{k}@", v)
        with open(os.path.join(tmp, "harness.cpp"), "w") as f:
            f.write(harness)
        srcs = [os.path.join(out, n) for n in sorted(os.listdir(out)) if n.startswith("gen_")]
        binp = os.path.join(tmp, "t")
        cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(tmp, "harness.cpp"), *srcs, "-L", BUILD, "-lrecomp_x87",
                             "-lrecomp_image", "-Wl,-rpath," + BUILD, "-o", binp], capture_output=True, text=True)
        check("0003 lifted code compiles", cc.returncode, 0)
        if cc.returncode:
            print(cc.stderr[:2000])
            return
        res = subprocess.run([binp], capture_output=True, text=True).stdout.splitlines()
        lines = {l.split()[0]: l for l in res}
        check("0003 MMX values", lines.get("mm"),
              "mm 0000000011223344 0000000080FF7F01 0000000000000000 0F0F0F0FF0F0E060")
        # Written registers get sign+exponent FFFF; r4 was never written.
        check("0003 MMX writes set sign/exponent", lines.get("se"), "se FFFF FFFF FFFF FFFF 1234")
        # Any MMX instruction: TOP 0, all tags valid. movd r32 / movq m64 results.
        check("0003 MMX state and stores", lines.get("state"),
              "state top=0 empty=00 ecx=F0F0E060 out=0F0F0F0FF0F0E060 esp=002FFFF4")
        check("0003 EMMS empties every tag", lines.get("emms"), "emms top=0 empty=FF")
        # fld1 with TOP 5 writes R4 = 1.0 (sig 8000000000000000, exp 3FFF), TOP 4;
        # movq sets TOP 0, all tags valid, R0 = the qword; the second fld1 pushes
        # onto a valid R7: masked stack overflow, R7 = real indefinite
        # (C000000000000000/FFFF), IE+SF+C1 (0x241), TOP 7. One x87 run spanning
        # the movq would end with TOP 3 instead.
        check("0003 x87 runs do not span MMX", lines.get("run"),
              "run top=7 empty=00 r4=8000000000000000/3FFF r0=F0E0D0C090807060 "
              "r7=C000000000000000/FFFF sw=0241")
        check("0003 psrad/psraw/packssdw/packsswb", lines.get("pack"),
              "pack FFFF0000F0001234 FFFFFFFF00000000 80007FFF80007FFF FF00807FFF00F012")
        # movhps: high qword from memory, low kept (A0..A7); movntps stores all 16.
        check("0003 movhps + movntps + sfence", lines.get("sse"),
              "sse A0 A1 A2 A3 A4 A5 A6 A7 11 22 33 44 55 66 77 88")


# ---- 0004: code in every executable section -----------------------------------

def test_code_span():
    mixer_va = BASE + 0x2000
    # .text: call the function in the second executable section, ret
    main = b"\xE8" + struct.pack("<i", mixer_va - (TEXT + 5)) + b"\xC3"
    mixer = b"\x31\xC0\xC3"  # xor eax, eax; ret
    good = pe_sections([(b".text", main, EXEC), (b"MIXER", mixer, EXEC), (b".data", b"\0" * 0x100, RW)],
                       export=("Mix", mixer_va - BASE, 0x3000))
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, _ = lift(tmp, good, [TEXT, mixer_va])
        check("0004 lift with two executable sections succeeds", r.returncode, 0)
        check("0004 function in the second executable section is lifted", mixer_va in fns, True)
        sym = os.path.join(tmp, "pe")
        p = subprocess.run([sys.executable, "-I", os.path.join(X86, "tools", "pe_symbols.py"),
                            os.path.join(tmp, "t.exe"), "--out", sym],
                           capture_output=True, text=True, env=dict(os.environ, PATH="/opt/homebrew/opt/llvm/bin:" + os.environ["PATH"]))
        rows = open(os.path.join(sym, "exports.tsv")).read().splitlines()[1:] if p.returncode == 0 else []
        check("0004 pe_symbols: export in MIXER is a function",
              [r.split("\t")[:3] for r in rows], [[f"{mixer_va:08X}", "func", "Mix"]])
    split = pe_sections([(b".text", main, EXEC), (b".data", b"\0" * 0x100, RW), (b"MIXER", mixer, EXEC)])
    with tempfile.TemporaryDirectory() as tmp:
        r, _, _ = lift(tmp, split, [TEXT])
        check("0004 data between executable sections fails the lift", r.returncode != 0, True)


# ---- 0005: switch tables completed from the bound check or from relocations ----

def switch_cases(out, jmp):
    """Case targets of the switch emitted for the jmp at `jmp`, or None."""
    for n in sorted(os.listdir(out)):
        if not n.startswith("gen_"):
            continue
        src = open(os.path.join(out, n)).read()
        at = src.find(f"// {jmp:08X} jmp")
        if at < 0:
            continue
        end = src.find("default:", at)
        block = src[at:end] if end > 0 else ""
        if "switch (t)" not in block:
            return None
        return sorted(int(x, 16) for x in re.findall(r"case 0x([0-9A-F]+)u:", block))
    return None


def test_jump_tables():
    t1, t2 = TEXT, TEXT + 0x100
    tbl1, tbl2 = TEXT + 0x20, TEXT + 0x120
    text = bytearray(b"\xCC" * 0x200)
    # f1: cmp ecx,2 / ja default (+10) / jmp [tbl1+ecx*4]; cases at +12..+14, default +15
    f1 = b"\x83\xF9\x02" + b"\x77\x0A" + b"\xFF\x24\x8D" + struct.pack("<I", tbl1) + b"\xC3\xC3\xC3\xC3"
    text[0:len(f1)] = f1
    text[0x20:0x2C] = struct.pack("<III", t1 + 12, t1 + 13, t1 + 14)
    # f2: jmp [tbl2+ecx*4] with no bound check; cases at +7, +8, +9
    f2 = b"\xFF\x24\x8D" + struct.pack("<I", tbl2) + b"\xC3\xC3\xC3"
    text[0x100:0x100 + len(f2)] = f2
    text[0x120:0x12C] = struct.pack("<III", t2 + 7, t2 + 8, t2 + 9)
    # Relocated: both jmp displacements, all of tbl1, the first two slots of tbl2.
    relocs = [t1 + 8, tbl1, tbl1 + 4, tbl1 + 8, t2 + 3, tbl2, tbl2 + 4]
    partial = [(t1 + 5, [t1 + 12, t1 + 13])]  # Ghidra missed the third case
    with tempfile.TemporaryDirectory() as tmp:
        r, _, out = lift(tmp, pe(bytes(text), b"\0" * 0x10, relocs), [t1, t2], jumptables=partial)
        check("0005 lift succeeds", r.returncode, 0)
        check("0005 bounded table completed past Ghidra's list", switch_cases(out, t1 + 5),
              [t1 + 12, t1 + 13, t1 + 14])
        check("0005 unbounded table taken from relocated slots only", switch_cases(out, t2),
              [t2 + 7, t2 + 8])
    with tempfile.TemporaryDirectory() as tmp:
        r, _, out = lift(tmp, pe(bytes(text), b"\0" * 0x10, None), [t1, t2], jumptables=partial)
        check("0005 without relocations an unbounded table is not guessed", switch_cases(out, t2), None)


# ---- 0006: SSE2 forms of the VC8 CRT's math paths -------------------------------

SSE2_CONV = bytes([
    0xF3, 0x0F, 0x5A, 0xC1,        # cvtss2sd xmm0, xmm1   1.5f -> 3FF8000000000000, xmm0[127:64] kept
    0xF2, 0x0F, 0x5A, 0xD3,        # cvtsd2ss xmm2, xmm3   0.1 -> 3DCCCCCD (inexact: PE), xmm2[127:32] kept
    0x0F, 0x5A, 0xE5,              # cvtps2pd xmm4, xmm5   SNaN 7F800001 -> 7FF8000020000000 (IE),
                                   #                       -2.0f -> C000000000000000
    0x66, 0x0F, 0x5A, 0xF7,        # cvtpd2ps xmm6, xmm7   1.0 -> 3F800000, 1e300 -> 7F800000
                                   #                       (overflow: OE, PE), upper half zeroed
    0xC3])
SSE2_MISC = bytes([
    0xF2, 0x0F, 0x5D, 0xC1,        # minsd xmm0, xmm1      +0, -0: both zeros -> source (-0)
    0xF2, 0x0F, 0x5D, 0xD3,        # minsd xmm2, xmm3      QNaN, 3.0 -> source 3.0, IE
    0xF3, 0x0F, 0x51, 0xE5,        # sqrtss xmm4, xmm5     2.25 -> 1.5 (exact)
    0xF3, 0x0F, 0x53, 0xF7,        # rcpss xmm6, xmm7      4.0 -> 0.25
    0x66, 0x0F, 0x50, 0xC1,        # movmskpd eax, xmm1    signs (lo -0, hi +1.0) -> 1
    0xC3])
SSE2_INT = bytes([
    0x66, 0x0F, 0xFE, 0xC1,        # paddd xmm0, xmm1      [FFFFFFFF,1,2,3]+[1,1,1,1] -> [0,2,3,4]
    0x66, 0x0F, 0xFD, 0xD3,        # paddw xmm2, xmm3      7FFF+1 -> 8000 in every word
    0x66, 0x0F, 0x72, 0xE4, 0x28,  # psrad xmm4, 40        [80000000,7FFFFFFF,FFFFFFFB,5] ->
                                   #                       [FFFFFFFF,0,FFFFFFFF,0]
    0xF3, 0x0F, 0x53, 0xEE,        # rcpss xmm5, xmm6      denormal 00000001 -> +inf 7F800000
    0xF3, 0x0F, 0x53, 0xFF,        # rcpss xmm7, xmm7      2^127 -> 2^-127, below normal -> +0
    0xC3])

SSE2_HARNESS = r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "runtime/lifted.h"
namespace recomp {
uint8_t* g_guest_base = nullptr;
void Unimplemented(Ctx&, uint32_t va, const char* w) { std::printf("unimplemented %08X %s\n", va, w); std::exit(3); }
void BadJump(Ctx&, uint32_t a, uint32_t b) { std::printf("bad jump %08X %08X\n", a, b); std::exit(3); }
void RaiseDivideError(Ctx&, uint32_t) { std::exit(3); }
namespace gen { void f_@CONV@(Ctx&); void f_@MISC@(Ctx&); void f_@INT@(Ctx&); }
}
using namespace recomp;
static void Set(Ctx& c, int r, uint64_t lo, uint64_t hi) {
  std::memcpy(c.xmm[r].b, &lo, 8); std::memcpy(c.xmm[r].b + 8, &hi, 8);
}
static void Dump(const char* tag, const Ctx& c) {
  std::printf("%s mxcsr=%04X eax=%08X", tag, c.mxcsr, c.eax);
  for (int r = 0; r < 8; r++) {
    uint64_t lo, hi;
    std::memcpy(&lo, c.xmm[r].b, 8); std::memcpy(&hi, c.xmm[r].b + 8, 8);
    std::printf(" x%d=%016llX:%016llX", r, (unsigned long long)hi, (unsigned long long)lo);
  }
  std::printf("\n");
}
static Ctx Fresh() {
  Ctx c{};
  c.esp = 0x2FFFF0; lift::Wr<uint32_t>(g_guest_base, c.esp, 0xDEADBEEF);
  c.eflags = 0x202; c.mxcsr = 0x1F80; c.fpu.cw = 0x27F; c.fpu.empty = 0xFF;
  for (int r = 0; r < 8; r++) Set(c, r, 0xAAAAAAAAAAAAAAAAull, 0xAAAAAAAAAAAAAAAAull);
  return c;
}
int main() {
  g_guest_base = static_cast<uint8_t*>(std::calloc(1, 0x400000));
  Ctx c = Fresh();
  Set(c, 1, 0xBBBBBBBB3FC00000ull, 0xBBBBBBBBBBBBBBBBull);  // 1.5f
  Set(c, 3, 0x3FB999999999999Aull, 0);                      // 0.1
  Set(c, 5, 0xC00000007F800001ull, 0);                      // [SNaN, -2.0f]
  Set(c, 7, 0x3FF0000000000000ull, 0x7E37E43C8800759Cull);  // [1.0, 1e300]
  gen::f_@CONV@(c); Dump("conv", c);
  c = Fresh();
  Set(c, 0, 0x0000000000000000ull, 0x1111111111111111ull);  // +0
  Set(c, 1, 0x8000000000000000ull, 0x3FF0000000000000ull);  // [-0, +1.0]
  Set(c, 2, 0x7FF8000000000000ull, 0x2222222222222222ull);  // QNaN
  Set(c, 3, 0x4008000000000000ull, 0);                      // 3.0
  Set(c, 5, 0x0000000040100000ull, 0);                      // 2.25f
  Set(c, 7, 0x0000000040800000ull, 0);                      // 4.0f
  gen::f_@MISC@(c); Dump("misc", c);
  c = Fresh();
  Set(c, 0, 0x00000001FFFFFFFFull, 0x0000000300000002ull);
  Set(c, 1, 0x0000000100000001ull, 0x0000000100000001ull);
  Set(c, 2, 0x7FFF7FFF7FFF7FFFull, 0x7FFF7FFF7FFF7FFFull);
  Set(c, 3, 0x0001000100010001ull, 0x0001000100010001ull);
  Set(c, 4, 0x7FFFFFFF80000000ull, 0x00000005FFFFFFFBull);
  Set(c, 6, 0x0000000000000001ull, 0);                      // smallest denormal
  Set(c, 7, 0x000000007F000000ull, 0);                      // 2^127
  gen::f_@INT@(c); Dump("int", c);
}
"""


def test_sse2():
    text = bytearray(b"\xCC" * 0x300)
    offs = {"CONV": 0x000, "MISC": 0x100, "INT": 0x200}
    for k, code in (("CONV", SSE2_CONV), ("MISC", SSE2_MISC), ("INT", SSE2_INT)):
        text[offs[k]:offs[k] + len(code)] = code
    with tempfile.TemporaryDirectory() as tmp:
        r, _, out = lift(tmp, pe(bytes(text), b"\0" * 0x10, None), [TEXT + o for o in offs.values()])
        report = open(os.path.join(out, "lift_report.txt")).read() if os.path.isdir(out) else ""
        check("0006 lift succeeds, no unimplemented sites",
              (r.returncode, re.search(r"unimplemented:\n(\s+\S.*\n)*warnings", report).group(0).count("\n") - 1), (0, 0))
        harness = SSE2_HARNESS
        for k, o in offs.items():
            harness = harness.replace(f"@{k}@", f"{TEXT + o:08X}")
        with open(os.path.join(tmp, "harness.cpp"), "w") as f:
            f.write(harness)
        srcs = [os.path.join(out, n) for n in sorted(os.listdir(out)) if n.startswith("gen_")]
        binp = os.path.join(tmp, "t")
        cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(tmp, "harness.cpp"), *srcs, "-L", BUILD, "-lrecomp_x87",
                             "-lrecomp_image", "-Wl,-rpath," + BUILD, "-o", binp], capture_output=True, text=True)
        check("0006 lifted code compiles", cc.returncode, 0)
        if cc.returncode:
            print(cc.stderr[:2000])
            return
        lines = {l.split()[0]: l.split() for l in subprocess.run([binp], capture_output=True, text=True).stdout.splitlines()}
        conv, misc, ints = lines.get("conv", []), lines.get("misc", []), lines.get("int", [])
        x = lambda row, r: row[3 + r].split("=")[1] if len(row) > 3 + r else None
        check("0006 cvtss2sd exact, destination bits 127:64 kept", x(conv, 0), "AAAAAAAAAAAAAAAA:3FF8000000000000")
        check("0006 cvtsd2ss rounds 0.1, destination bits 127:32 kept", x(conv, 2), "AAAAAAAAAAAAAAAA:AAAAAAAA3DCCCCCD")
        check("0006 cvtps2pd quiets an SNaN keeping its payload", x(conv, 4), "C000000000000000:7FF8000020000000")
        check("0006 cvtpd2ps overflow to +inf, upper half zeroed", x(conv, 6), "0000000000000000:7F8000003F800000")
        check("0006 conversion flags PE|IE|OE", conv[1] if conv else None, "mxcsr=1FA9")
        check("0006 minsd of two zeros returns the source", x(misc, 0), "1111111111111111:8000000000000000")
        check("0006 minsd with a QNaN returns the source", x(misc, 2), "2222222222222222:4008000000000000")
        check("0006 sqrtss", x(misc, 4), "AAAAAAAAAAAAAAAA:AAAAAAAA3FC00000")
        check("0006 rcpss 4 -> 0.25", x(misc, 6), "AAAAAAAAAAAAAAAA:AAAAAAAA3E800000")
        check("0006 movmskpd and minsd's IE", (misc[2] if misc else None, misc[1] if misc else None),
              ("eax=00000001", "mxcsr=1F81"))
        check("0006 paddd wraps", x(ints, 0), "0000000400000003:0000000200000000")
        check("0006 paddw wraps", x(ints, 2), "8000800080008000:8000800080008000")
        check("0006 psrad count > 31 fills with the sign", x(ints, 4), "00000000FFFFFFFF:00000000FFFFFFFF")
        check("0006 rcpss of a denormal is +inf", x(ints, 5), "AAAAAAAAAAAAAAAA:AAAAAAAA7F800000")
        check("0006 rcpss result below normal flushes to +0", x(ints, 7), "0000000000000000:0000000000000000")
        check("0006 integer ops and rcpss leave MXCSR alone", ints[1] if ints else None, "mxcsr=1F80")



# ---- 0010: switch through a register, table in .data -----------------------------

def test_jump_table_load():
    # f3: cmp eax,2 / ja default / mov eax,[eax*4+tbl] / jmp eax; cases at +14, +15, +16,
    # default +17. f4: the same, but jmp ecx (not the loaded register).
    t3, t4, tbl = TEXT, TEXT + 0x40, DATA
    text = bytearray(b"\xCC" * 0x100)
    for t, jmp in ((t3, b"\xFF\xE0"), (t4, b"\xFF\xE1")):
        f = b"\x83\xF8\x02" + b"\x77\x0C" + b"\x8B\x04\x85" + struct.pack("<I", tbl) + jmp + b"\xC3\xC3\xC3\xC3"
        text[t - TEXT:t - TEXT + len(f)] = f
    data = struct.pack("<III", t3 + 14, t3 + 15, t3 + 16) + b"\0" * 4
    slots = [tbl, tbl + 4, tbl + 8]
    with tempfile.TemporaryDirectory() as tmp:
        r, _, out = lift(tmp, pe(bytes(text), data, [t3 + 8, t4 + 8] + slots), [t3, t4])
        check("0010 lift succeeds", r.returncode, 0)
        check("0010 mov reg,[table+idx*4]; jmp reg: table in .data recovered", switch_cases(out, t3 + 12),
              [t3 + 14, t3 + 15, t3 + 16])
        check("0010 jmp through another register is not a table jump", switch_cases(out, t4 + 12), None)
    with tempfile.TemporaryDirectory() as tmp:
        r, _, out = lift(tmp, pe(bytes(text), data, [t3 + 8, t4 + 8]), [t3, t4])
        check("0010 a table outside .text needs relocated slots", switch_cases(out, t3 + 12), None)


# ---- 0010: stored addresses in every data section --------------------------------

def test_data_section_pointers():
    # Three functions only data refers to: f1 from an aligned relocated slot in
    # .data1 (a third data section), f2 from an unaligned relocated slot in
    # .data. Without relocations only .rdata/.data are scanned (by value).
    text = bytearray(b"\xCC" * 0x40)
    text[0] = 0xC3
    f1, f2 = TEXT + 0x10, TEXT + 0x20
    text[0x10] = text[0x20] = 0xC3
    data = b"\0" + struct.pack("<I", f2) + b"\0" * 3
    data1 = struct.pack("<I", f1) + b"\0" * 4
    secs = [(b".text", bytes(text), EXEC), (b".data", data, RW), (b".data1", data1, RW)]
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, out = lift(tmp, pe_sections(secs, [DATA + 1, DATA + 0x1000]), [TEXT])
        check("0010 lift succeeds", r.returncode, 0)
        check("0010 relocated slot in another data section lifts its target", f1 in fns, True)
        check("0010 unaligned relocated slot lifts its target", f2 in fns, True)
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, out = lift(tmp, pe_sections(secs, None), [TEXT])
        check("0010 without relocations .data1 is not scanned", f1 in fns, False)


# ---- 0010: packed-integer MMX/SSE2 forms, movhps store ------------------------
# Each case: (asm, kind, a, b, expected). kind "mm": mm0 = a, mm1 = b, result
# mm0; "xmm": xmm0 = a, xmm1 = b (each (hi, lo)), result xmm0; "mem": memory
# operand [ebx] = b (8 or 16 bytes), mm0/xmm0 = a; "store": xmm1 = b, result
# the qword at [ebx]. Expected values worked out by hand from the SDM's lane
# definitions (lanes listed low to high in the comments).
SIMD_CASES = [
    # paddw: 0001+FFFF=0000, FFFF+0001=0000, 8000+FFFF=7FFF, 7FFF+0001=8000 (wrap)
    ("paddw mm0, mm1", "mm", 0x7FFF8000FFFF0001, 0x0001FFFF0001FFFF, 0x80007FFF00000000),
    # paddd: 00000001+7FFFFFFF=80000000, FFFFFFFF+1=0
    ("paddd mm0, mm1", "mm", 0xFFFFFFFF00000001, 0x000000017FFFFFFF, 0x0000000080000000),
    # paddsw: 1+2=3, -1+-32768 -> -32768, -32768+-1 -> -32768, 32767+1 -> 32767
    ("paddsw mm0, mm1", "mm", 0x7FFF8000FFFF0001, 0x0001FFFF80000002, 0x7FFF800080000003),
    # paddusw: 1234+1=1235, 1+FFFE=FFFF, 8000+8000 -> FFFF, FFFF+1 -> FFFF
    ("paddusw mm0, mm1", "mm", 0xFFFF800000011234, 0x00018000FFFE0001, 0xFFFFFFFFFFFF1235),
    # psubw: 5-3=2, 1-2=FFFF, 8000-1=7FFF, 0-1=FFFF
    ("psubw mm0, mm1", "mm", 0x0000800000010005, 0x0001000100020003, 0xFFFF7FFFFFFF0002),
    # psubd: 80000000-1=7FFFFFFF, 0-1=FFFFFFFF
    ("psubd mm0, mm1", "mm", 0x0000000080000000, 0x0000000100000001, 0xFFFFFFFF7FFFFFFF),
    # psubsw: 5-7=-2, 0-(-32768) -> 32767, 32767-(-1) -> 32767, -32768-1 -> -32768
    ("psubsw mm0, mm1", "mm", 0x80007FFF00000005, 0x0001FFFF80000007, 0x80007FFF7FFFFFFE),
    # psubusb bytes: 04-03, 03-02, 02-01 = 1; 01-02 -> 0; 80-80 = 0; 10-20 -> 0; FF-01 = FE; 00-01 -> 0
    ("psubusb mm0, mm1", "mm", 0x00FF108001020304, 0x0101208002010203, 0x00FE000000010101),
    # psubusw: FFFF-1=FFFE, 1-1=0, 8000-1=7FFF, 5-6 -> 0
    ("psubusw mm0, mm1", "mm", 0x000580000001FFFF, 0x0006000100010001, 0x00007FFF0000FFFE),
    # pcmpeqb bytes 77 66 55/AA 44 33 22 11/FF 00
    ("pcmpeqb mm0, mm1", "mm", 0x0011223344556677, 0x00FF223344AA6677, 0xFF00FFFFFF00FFFF),
    # pcmpeqw: 8000/0000 no, FFFF/FFFF yes, 0000/0001 no, 1234/1234 yes
    ("pcmpeqw mm0, mm1", "mm", 0x12340000FFFF8000, 0x12340001FFFF0000, 0xFFFF0000FFFF0000),
    # pcmpgtw signed: 0>0 no, 7FFF>-32768 yes, -32768>7FFF no, 1>0 yes
    ("pcmpgtw mm0, mm1", "mm", 0x000180007FFF0000, 0x00007FFF80000000, 0xFFFF0000FFFF0000),
    # pmullw: 3*5=000F, 100*100=10000 -> 0000, -1*-1=0001, 8000*2=10000 -> 0000
    ("pmullw mm0, mm1", "mm", 0x8000FFFF01000003, 0x0002FFFF01000005, 0x000000010000000F),
    # pmulhw: 7FFF^2=3FFF0001 -> 3FFF, 4000^2=10000000 -> 1000, -1*2=-2 -> FFFF, (-32768)^2=40000000 -> 4000
    ("pmulhw mm0, mm1", "mm", 0x8000FFFF40007FFF, 0x8000000240007FFF, 0x4000FFFF10003FFF),
    # pmaddwd: 2*4+3*5=17h; (-32768)^2*2 = 80000000h (the one overflow)
    ("pmaddwd mm0, mm1", "mm", 0x8000800000030002, 0x8000800000050004, 0x8000000000000017),
    # pmaddwd: 3*6+(-2)*5=8; 1*4+(-1)*2=2
    ("pmaddwd mm0, mm1", "mm", 0xFFFF0001FFFE0003, 0x0002000400050006, 0x0000000200000008),
    # packuswb: 80, FF, 0100 -> FF, 7FFF -> FF | 00, 01, -1 -> 00, -32768 -> 00
    ("packuswb mm0, mm1", "mm", 0x7FFF010000FF0080, 0x8000FFFF00010000, 0x00000100FFFFFF80),
    # punpcklbw: a 11 22 33 44, b 88 99 AA BB interleaved
    ("punpcklbw mm0, mm1", "mm", 0x8877665544332211, 0xFFEEDDCCBBAA9988, 0xBB44AA3399228811),
    ("punpcklwd mm0, mm1", "mm", 0x4444333322221111, 0x8888777766665555, 0x6666222255551111),
    ("punpckldq mm0, mm1", "mm", 0x2222222211111111, 0x4444444433333333, 0x3333333311111111),
    # punpckhbw: a 55 66 77 88, b CC DD EE FF interleaved
    ("punpckhbw mm0, mm1", "mm", 0x8877665544332211, 0xFFEEDDCCBBAA9988, 0xFF88EE77DD66CC55),
    ("punpckhwd mm0, mm1", "mm", 0x4444333322221111, 0x8888777766665555, 0x8888444477773333),
    ("punpckhdq mm0, mm1", "mm", 0x2222222211111111, 0x4444444433333333, 0x4444444422222222),
    # pshufw 1Bh = words 3, 2, 1, 0 of the source; 00h = word 0 four times
    ("pshufw mm0, mm1, 0x1B", "mm", 0, 0x4444333322221111, 0x1111222233334444),
    ("pshufw mm0, mm1, 0x00", "mm", 0, 0x4444333322221111, 0x1111111111111111),
    # psllw 4: F00F->00F0, 00FF->0FF0, 1234->2340, 8001->0010; 16 clears
    ("psllw mm0, 4", "mm", 0x8001123400FFF00F, 0, 0x001023400FF000F0),
    ("psllw mm0, 16", "mm", 0x8001123400FFF00F, 0, 0),
    # pslld 8: 00FF00FF->FF00FF00, 80000001->00000100
    ("pslld mm0, 8", "mm", 0x8000000100FF00FF, 0, 0x00000100FF00FF00),
    # psrlw 4: F00F->0F00, 00FF->000F, 1234->0123, 8001->0800; by mm1 = 4 the same
    ("psrlw mm0, 4", "mm", 0x8001123400FFF00F, 0, 0x08000123000F0F00),
    ("psrlw mm0, mm1", "mm", 0x8001123400FFF00F, 4, 0x08000123000F0F00),
    # psrld 31: 7FFFFFFF->0, 80000000->1
    ("psrld mm0, 31", "mm", 0x800000007FFFFFFF, 0, 0x0000000100000000),
    # counts of exactly the lane width (32 for dwords) clear every lane
    ("pslld mm0, 32", "mm", 0x8000000100FF00FF, 0, 0),
    ("psrld mm0, 32", "mm", 0x800000007FFFFFFF, 0, 0),
    # memory forms (m64; PUNPCKLBW's is m32)
    ("paddd mm0, qword ptr [ebx]", "mem", 0x0000000100000002, 0x0000001000000020, 0x0000001100000022),
    ("pmaddwd mm0, qword ptr [ebx]", "mem", 0x8000800000030002, 0x8000800000050004, 0x8000000000000017),
    ("punpcklbw mm0, dword ptr [ebx]", "mem", 0x8877665544332211, 0xDEADBEEFBBAA9988, 0xBB44AA3399228811),
    # SSE2 (hi, lo): per 64-bit half
    ("paddsw xmm0, xmm1", "xmm", (0x7FFF, 0x7FFF8000FFFF0001), (0x0001, 0x0001FFFF80000002),
     (0x7FFF, 0x7FFF800080000003)),
    ("pmaddwd xmm0, xmm1", "xmm", (0x0001000100010001, 0x8000800000030002),
     (0x0002000200020002, 0x8000800000050004), (0x0000000400000004, 0x8000000000000017)),
    ("pmulhw xmm0, xmm1", "xmm", (0x0100, 0x8000FFFF40007FFF), (0x0100, 0x8000000240007FFF),
     (0x0001, 0x4000FFFF10003FFF)),
    ("pmullw xmm0, xmm1", "xmm", (0xFFFF, 0x8000FFFF01000003), (0x0002, 0x0002FFFF01000005),
     (0xFFFE, 0x000000010000000F)),
    ("psubsw xmm0, xmm1", "xmm", (0x8000, 0x80007FFF00000005), (0x0001, 0x0001FFFF80000007),
     (0x8000, 0x80007FFF7FFFFFFE)),
    # packssdw: dwords 1, 32768, -1, -32769 | 2, 7FFFFFFF, 3, 80000000 to words
    ("packssdw xmm0, xmm1", "xmm", (0xFFFF7FFFFFFFFFFF, 0x0000800000000001),
     (0x8000000000000003, 0x7FFFFFFF00000002), (0x800000037FFF0002, 0x8000FFFF7FFF0001)),
    # packuswb: words 80 FF 100 7FFF 0 FFFF 1 2 | 6 5 4 3 8 7 0 100 to bytes
    ("packuswb xmm0, xmm1", "xmm", (0x00020001FFFF0000, 0x7FFF010000FF0080),
     (0x0100000000070008, 0x0003000400050006), (0xFF00070803040506, 0x02010000FFFFFF80)),
    ("punpckldq xmm0, xmm1", "xmm", (0x4444444433333333, 0x2222222211111111),
     (0x8888888877777777, 0x6666666655555555), (0x6666666622222222, 0x5555555511111111)),
    ("punpckhdq xmm0, xmm1", "xmm", (0x4444444433333333, 0x2222222211111111),
     (0x8888888877777777, 0x6666666655555555), (0x8888888844444444, 0x7777777733333333)),
    ("pshuflw xmm0, xmm1, 0x1B", "xmm", (0, 0), (0x8888777766665555, 0x4444333322221111),
     (0x8888777766665555, 0x1111222233334444)),
    ("pshufhw xmm0, xmm1, 0x1B", "xmm", (0, 0), (0x8888777766665555, 0x4444333322221111),
     (0x5555666677778888, 0x4444333322221111)),
    ("psllw xmm0, 4", "xmm", (0x0001000200030004, 0x8001123400FFF00F), (0, 0),
     (0x0010002000300040, 0x001023400FF000F0)),
    # psrlw 15: 0001->0, FFFF->1, 7FFF->0, 8000->1; 16 clears
    ("psrlw xmm0, 15", "xmm", (0, 0x80007FFFFFFF0001), (0, 0), (0, 0x0001000000010000)),
    ("psrlw xmm0, 16", "xmm", (0x1234, 0x80007FFFFFFF0001), (0, 0), (0, 0)),
    # psraw 3: 0010->0002, FFF0->FFFE, 7FFF->0FFF, 8000->F000; FFFF->FFFF
    ("psraw xmm0, 3", "xmm", (0xFFFF000000000000, 0x80007FFFFFF00010), (0, 0),
     (0xFFFF000000000000, 0xF0000FFFFFFE0002)),
    # the 16-byte aligned memory form
    ("paddsw xmm0, xmmword ptr [ebx]", "mem", (0x7FFF, 0x7FFF8000FFFF0001), (0x0001, 0x0001FFFF80000002),
     (0x7FFF, 0x7FFF800080000003)),
    # movhps m64, xmm: the high quadword stored
    ("movhps qword ptr [ebx], xmm1", "store", 0, (0x0123456789ABCDEF, 0x1111111122222222), 0x0123456789ABCDEF),
]

SIMD_HARNESS = r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "runtime/lifted.h"
namespace recomp {
uint8_t* g_guest_base = nullptr;
void Unimplemented(Ctx&, uint32_t va, const char* w) { std::printf("unimplemented %08X %s\n", va, w); std::exit(3); }
void BadJump(Ctx&, uint32_t a, uint32_t b) { std::printf("bad jump %08X %08X\n", a, b); std::exit(3); }
void RaiseDivideError(Ctx&, uint32_t) { std::exit(3); }
void CheckAligned(Ctx&, uint32_t a, uint32_t va) { if (a & 15) { std::printf("misaligned %08X\n", va); std::exit(3); } }
namespace gen {
@DECLS@
}
}
using namespace recomp;
static void SetX(Xmm& x, unsigned long long hi, unsigned long long lo) {
  std::memcpy(x.b, &lo, 8); std::memcpy(x.b + 8, &hi, 8);
}
int main() {
  g_guest_base = static_cast<uint8_t*>(std::calloc(1, 0x400000));
  unsigned long long lo, hi;
@BODY@
}
"""


def test_simd():
    text = ""
    for i, (asm, *_rest) in enumerate(SIMD_CASES):
        text += f".org {16 * i:#x}, 0xCC\n  {asm}\n  ret\n"
    with tempfile.TemporaryDirectory() as tmp:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import test_loader
        code = test_loader.assemble(tmp, text)
        entries = [TEXT + 16 * i for i in range(len(SIMD_CASES))]
        r, fns, out = lift(tmp, pe(code + b"\xCC" * (-len(code) % 16), b"\0" * 0x40, None), entries)
        check("0010 lift succeeds", r.returncode, 0)
        report = open(os.path.join(out, "lift_report.txt")).read() if os.path.isdir(out) else ""
        unimpl = re.search(r"unimplemented:\n((\s+\S.*\n)*)warnings", report)
        check("0010 no unimplemented sites", unimpl.group(1).strip() if unimpl else "?", "")
        decls, body = "", ""
        for i, (asm, kind, a, b, want) in enumerate(SIMD_CASES):
            f = f"f_{TEXT + 16 * i:08X}"
            decls += f"void {f}(Ctx&);\n"
            body += "  { Ctx c{}; c.esp = 0x2FFFF0; lift::Wr<uint32_t>(g_guest_base, c.esp, 0xDEADBEEF);\n"
            body += f"    c.ebx = 0x{DATA:X}; c.fpu.cw = 0x27F; c.fpu.empty = 0xFF; c.mxcsr = 0x1F80;\n"
            body += f"    std::memset(g_guest_base + 0x{DATA:X}, 0, 32);\n"
            wide = isinstance(a, tuple) or isinstance(b, tuple)
            if kind == "mm":
                body += f"    c.fpu.r[0].sig = 0x{a:X}ull; c.fpu.r[1].sig = 0x{b:X}ull;\n"
            elif kind == "xmm":
                body += f"    SetX(c.xmm[0], 0x{a[0]:X}ull, 0x{a[1]:X}ull); SetX(c.xmm[1], 0x{b[0]:X}ull, 0x{b[1]:X}ull);\n"
            elif kind == "mem" and wide:
                body += (f"    SetX(c.xmm[0], 0x{a[0]:X}ull, 0x{a[1]:X}ull);\n"
                         f"    lift::Wr<uint64_t>(g_guest_base, 0x{DATA:X}, 0x{b[1]:X}ull);"
                         f" lift::Wr<uint64_t>(g_guest_base, 0x{DATA + 8:X}, 0x{b[0]:X}ull);\n")
            elif kind == "mem":
                body += (f"    c.fpu.r[0].sig = 0x{a:X}ull;"
                         f" lift::Wr<uint64_t>(g_guest_base, 0x{DATA:X}, 0x{b:X}ull);\n")
            else:  # store
                body += f"    SetX(c.xmm[1], 0x{b[0]:X}ull, 0x{b[1]:X}ull);\n"
            body += f"    gen::{f}(c);\n"
            if kind == "store":
                body += f"    std::printf(\"{i} %016llX\\n\", (unsigned long long)lift::Rd<uint64_t>(g_guest_base, 0x{DATA:X}));\n"
            elif wide:
                body += "    std::memcpy(&lo, c.xmm[0].b, 8); std::memcpy(&hi, c.xmm[0].b + 8, 8);\n"
                body += f"    std::printf(\"{i} %016llX:%016llX\\n\", hi, lo);\n"
            else:
                body += f"    std::printf(\"{i} %016llX\\n\", (unsigned long long)c.fpu.r[0].sig);\n"
            body += "  }\n"
        with open(os.path.join(tmp, "harness.cpp"), "w") as f:
            f.write(SIMD_HARNESS.replace("@DECLS@", decls).replace("@BODY@", body))
        srcs = [os.path.join(out, n) for n in sorted(os.listdir(out)) if n.startswith("gen_")]
        binp = os.path.join(tmp, "t")
        cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(tmp, "harness.cpp"), *srcs, "-L", BUILD, "-lrecomp_x87",
                             "-lrecomp_image", "-Wl,-rpath," + BUILD, "-o", binp], capture_output=True, text=True)
        check("0010 lifted code compiles", cc.returncode, 0)
        if cc.returncode:
            print(cc.stderr[:3000])
            return
        res = dict(l.split(" ", 1) for l in subprocess.run([binp], capture_output=True, text=True).stdout.splitlines()
                   if " " in l)
        for i, (asm, kind, a, b, want) in enumerate(SIMD_CASES):
            w = f"{want[0]:016X}:{want[1]:016X}" if isinstance(want, tuple) else f"{want:016X}"
            check(f"0010 {asm}", res.get(str(i)), w)


# ---- 0011: PUSH/POP slots are the instruction's operand size -------------------

# (name, bytes of the sequence, ESP change, top dword after it). Each case runs
#   mov ebp, esp; <sequence>; mov eax, esp; sub eax, ebp; mov ecx, [esp];
#   mov esp, ebp; ret
# on a stack filled with AAh below a DEADBEEFh top dword, with
# ebx = 11112222h, esi = 33334444h, eax = 5555BEEFh. SDM vol. 2 PUSH/POP: the
# slot is the operand size (32 unless 66h); a segment register pushed with a
# 32-bit operand size takes 4 bytes, recent Intel processors writing only its
# 16-bit selector (DS/ES read 0023h in a Win32 process), so AAAAh stays above.
STACK_CASES = [
    ("push ds", b"\x1E", -4, 0xAAAA0023),
    ("push es", b"\x06", -4, 0xAAAA0023),
    ("push es; pop es", b"\x06\x07", 0, 0xDEADBEEF),
    ("push ds; pop es", b"\x1E\x07", 0, 0xDEADBEEF),
    # Miles' MIXER_shutdown frame is balanced, so ebx and esi come back: pushed
    # again after it, they are the top dword
    ("frame; push ebx", b"\x53\x56\x1E\x06\x07\x1F\x5E\x5B\x53", -4, 0x11112222),
    ("frame; push esi", b"\x53\x56\x1E\x06\x07\x1F\x5E\x5B\x56", -4, 0x33334444),
    # 66h: two-byte slots; the old top dword's upper half shows through
    ("push ax", b"\x66\x50", -2, 0xBEEFBEEF),
    ("push word 1234h", b"\x66\x68\x34\x12", -2, 0xBEEF1234),
    ("push ax; pop ax", b"\x66\x50\x66\x58", 0, 0xDEADBEEF),
    ("pop ax", b"\x66\x58", 2, 0xAAAADEAD),
    # 32-bit forms unchanged
    ("push ebx", b"\x53", -4, 0x11112222),
    ("push 7Fh", b"\x6A\x7F", -4, 0x0000007F),
]


def test_stack_forms():
    code = b""
    for _name, seq, _d, _top in STACK_CASES:
        body = b"\x89\xE5" + seq + b"\x89\xE0\x29\xE8\x8B\x0C\x24\x89\xEC\xC3"
        code += body + b"\xCC" * (-len(body) % 32)
    entries = [TEXT + 32 * i for i in range(len(STACK_CASES))]
    with tempfile.TemporaryDirectory() as tmp:
        r, fns, out = lift(tmp, pe(code, b"\0" * 0x40, None), entries)
        check("0011 lift succeeds", r.returncode, 0)
        decls, body = "", ""
        for i in range(len(STACK_CASES)):
            f = f"f_{TEXT + 32 * i:08X}"
            decls += f"void {f}(Ctx&);\n"
            body += ("  { Ctx c{}; c.esp = 0x2FFF00; std::memset(g_guest_base + 0x2FFE00, 0xAA, 0x200);\n"
                     "    lift::Wr<uint32_t>(g_guest_base, c.esp, 0xDEADBEEF);\n"
                     "    c.ebx = 0x11112222; c.esi = 0x33334444; c.eax = 0x5555BEEF;\n"
                     f"    gen::{f}(c);\n"
                     f"    std::printf(\"{i} %d %08X\\n\", int(c.eax), c.ecx); }}\n")
        with open(os.path.join(tmp, "harness.cpp"), "w") as f:
            f.write(SIMD_HARNESS.replace("@DECLS@", decls).replace("@BODY@", body))
        srcs = [os.path.join(out, n) for n in sorted(os.listdir(out)) if n.startswith("gen_")]
        binp = os.path.join(tmp, "t")
        cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(tmp, "harness.cpp"), *srcs, "-L", BUILD, "-lrecomp_x87",
                             "-lrecomp_image", "-Wl,-rpath," + BUILD, "-o", binp], capture_output=True, text=True)
        check("0011 lifted code compiles", cc.returncode, 0)
        if cc.returncode:
            print(cc.stderr[:3000])
            return
        res = dict(l.split(" ", 1) for l in subprocess.run([binp], capture_output=True, text=True).stdout.splitlines()
                   if " " in l)
        for i, (name, _seq, delta, top) in enumerate(STACK_CASES):
            check(f"0011 {name}", res.get(str(i)), f"{delta} {top:08X}")


def main():
    test_reloc_discovery()
    test_mmx_sse()
    test_code_span()
    test_jump_tables()
    test_sse2()
    test_simd()
    test_jump_table_load()
    test_data_section_pointers()
    test_stack_forms()
    print("lifter patches:", "FAILED" if failures else "ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
