#!/usr/bin/env python3
"""The runtime's VirtualAlloc reservations (x86recomp GuestAllocator,
patch 0021) against its earlier implementation:

  /opt/homebrew/bin/python3 -I tests/test_guest_alloc.py

Builds x86recomp's tests/guest_alloc_test.cpp with this tree's allocator and
runs it: random sequences of reservations (lowest free, top down, at an
address), releases and permanent reservations, each compared with the
earlier implementation kept verbatim in the test (every reservation's
address, Find and FreeGap). Prints a FAIL line per failing check.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
CXX = "/opt/homebrew/opt/llvm/bin/clang++"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        binp = os.path.join(tmp, "guest_alloc_test")
        rt = os.path.join(X86, "src", "runtime")
        cc = subprocess.run([CXX, "-std=c++20", "-O2", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(X86, "tests", "guest_alloc_test.cpp"), os.path.join(rt, "guest_memory.cpp"),
                             os.path.join(rt, "guest_alloc.cpp"), "-o", binp], capture_output=True, text=True)
        if cc.returncode:
            print("FAIL guest_alloc_test builds\n" + cc.stderr[:3000])
            return 1
        r = subprocess.run([binp], capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
