#!/usr/bin/env python3
"""Tests for src/replaced.cpp, the event-data helpers reFrozen replaces (no game data):
the replacements are compiled with a harness whose stand-ins for the translated bodies
record each call.

  /opt/homebrew/bin/python3 -I tests/test_event_data.py

A missing event data (ecx 0) must leave what the helper's own no-unit path leaves: eax 0,
ecx and the flags as on that path (a zero result: Intel SDM, CF=OF=0, ZF=1, PF=1, SF=0; AF
not checked), and a return (esp + 4); the translated body never runs. Any other ecx runs the translated body unchanged.
The game manifest replaces both helpers, and every build of the game module compiles
src/replaced.cpp; validate_lift.py counts a replaced function's translated body as lifted. Needs the x86recomp sources (tools/x86recomp) and Homebrew LLVM.
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
CXX = "/opt/homebrew/opt/llvm/bin/clang++"
HELPERS = (("6F40B6C0", 0x38), ("6F26FC10", 0x2C))  # each helper and its ecx on the no-unit path
CF, PF, ZF, SF, OF = 0x1, 0x4, 0x40, 0x80, 0x800
failures = 0


def check(name, got, want):
    global failures
    if got == want:
        print(f"ok   {name}")
    else:
        failures += 1
        print(f"FAIL {name}: got {got!r}, want {want!r}")


HARNESS = r"""
#include <cstdio>
#include "runtime/lifted.h"
namespace recomp { uint8_t* g_guest_base = nullptr; }
namespace recomp::gen {
uint32_t g_called;
#define STAND_IN(a) void f_##a##_lifted(::recomp::Ctx& c) { g_called = 0x##a##u; c.eax = 0x5EED0000u; c.esp += 4u; } \
                    void f_##a(::recomp::Ctx& c);
STAND_IN(6F40B6C0)
STAND_IN(6F26FC10)
}
using namespace recomp;
template <void (*Fn)(Ctx&)> void Run(const char* name, uint32_t ecx) {
  Ctx c{};
  c.eax = 0xAAAAAAAAu; c.ecx = ecx; c.esp = 0x2FFFF0u; c.eflags = 0x202u | 0x1u | 0x80u | 0x800u;
  gen::g_called = 0;
  Fn(c);
  std::printf("%s %08X %08X %08X %08X %08X %08X\n", name, ecx, gen::g_called, c.eax, c.ecx, c.esp, c.eflags);
}
int main() {
  Run<gen::f_6F40B6C0>("6F40B6C0", 0); Run<gen::f_6F40B6C0>("6F40B6C0", 0x1000);
  Run<gen::f_6F26FC10>("6F26FC10", 0); Run<gen::f_6F26FC10>("6F26FC10", 0x1000);
}
"""


def run():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "harness.cpp"), "w").write(HARNESS)
        binp = os.path.join(tmp, "t")
        cc = subprocess.run([CXX, "-std=c++20", "-O2", "-w", "-I", os.path.join(X86, "src"), os.path.join(tmp, "harness.cpp"),
                             os.path.join(ROOT, "src", "replaced.cpp"), "-o", binp], capture_output=True, text=True)
        if cc.returncode:
            check("replacements: compile", cc.stderr.strip()[-400:], "")
            return
        rows = {}
        for line in subprocess.run([binp], capture_output=True, text=True).stdout.splitlines():
            name, ecx, called, eax, ecx_out, esp, eflags = line.split()
            rows[(name, int(ecx, 16))] = (int(called, 16), int(eax, 16), int(ecx_out, 16), int(esp, 16), int(eflags, 16))
    for addr, link in HELPERS:
        called, eax, ecx, esp, eflags = rows.get((addr, 0), (None,) * 5)
        check(f"{addr}: no event data: the translated body is not run", called, 0)
        check(f"{addr}: no event data: eax 0 (no unit)", eax, 0)
        check(f"{addr}: no event data: ecx as on the no-unit path", ecx, link)
        check(f"{addr}: no event data: returns (esp + 4)", esp, 0x2FFFF4)
        check(f"{addr}: no event data: flags as on the no-unit path",
              (eflags or 0) & (CF | PF | ZF | SF | OF), PF | ZF)
        called, eax, ecx, esp, eflags = rows.get((addr, 0x1000), (None,) * 5)
        check(f"{addr}: event data present: the translated body runs", called, int(addr, 16))
        check(f"{addr}: event data present: its result and registers are kept", (eax, ecx, esp), (0x5EED0000, 0x1000, 0x2FFFF4))


def wiring():
    manifest = open(os.path.join(ROOT, "config", "game.manifest")).read().split("\n")
    for addr, _ in HELPERS:
        check(f"{addr}: game.manifest replaces it", any(l.split()[:2] == ["replace", addr] for l in manifest), True)
    def lines(path):
        return open(os.path.join(ROOT, path)).read().split("\n")
    wired = {"CMakeLists.txt": any("target_sources(war3_lifted" in l and "src/replaced.cpp" in l for l in lines("CMakeLists.txt")),
             "scripts/poc/make_kit.sh": any(l.startswith("cp ") and "/src/replaced.cpp" in l and '"$KIT/src/"' in l
                                            for l in lines("scripts/poc/make_kit.sh")),
             # the line that compiles: the files handed to xargs
             "scripts/poc/build_module.sh": any("| xargs" in l and '"$KIT/src/replaced.cpp"' in l
                                                for l in lines("scripts/poc/build_module.sh"))}
    for path, ok in wired.items():
        check(f"{path} builds src/replaced.cpp into the game module", ok, True)
    # The two kits (development: make_kit.sh; the release app: make_release_app.sh) copy every kit source
    # the builder compiles.
    compiled = set()
    for l in lines("scripts/poc/build_module.sh"):
        if "| xargs" in l:
            compiled |= set(re.findall(r'"\$KIT/src/([^"/]+)"', l))
    for path in ("scripts/poc/make_kit.sh", "scripts/release/make_release_app.sh"):
        copied = set()
        for l in lines(path):
            if l.startswith("cp ") and l.rstrip().endswith('"$KIT/src/"'):
                copied |= {os.path.basename(a.strip('"')) for a in re.findall(r'"[^"]+"', l)[:-1]}
        check(f"{path} copies every kit source the builder compiles", sorted(compiled - copied), [])


def audit():
    # validate_lift.py counts a replaced function's translated body (f_<address>_lifted) as lifted.
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import validate_lift
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "gen_game_000.cpp"), "w").write(
            "void f_6F40B6C0_lifted(::recomp::Ctx& c) {\n}\nvoid f_6F001000(::recomp::Ctx& c) {\n}\n")
        fns = validate_lift.parse_generated(tmp)[0]
    check("validate_lift.py: a replaced function's translated body counts as lifted", sorted(fns), [0x6F001000, 0x6F40B6C0])


run()
wiring()
audit()
print("ALL PASS" if not failures else f"{failures} FAILED")
sys.exit(1 if failures else 0)
