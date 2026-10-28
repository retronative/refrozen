#!/usr/bin/env python3
"""LAN discovery broadcasts (x86recomp lan_broadcast, patch 0025):

  /opt/homebrew/bin/python3 -I tests/test_lan_broadcast.py

Builds x86recomp's tests/lan_broadcast_test.cpp with this tree's
lan_broadcast.cpp and runs it: which datagrams are LAN discovery
(255.255.255.255:6112), which interfaces of a getifaddrs list get them
(interface flags and addresses as getifaddrs(3) and netintro(4) define
them: a Mac with a VPN, each excluded property alone, several networks,
none), and what the send reports. Prints a FAIL line per failing check.
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
        binp = os.path.join(tmp, "lan_broadcast_test")
        cc = subprocess.run([CXX, "-std=c++20", "-O2", "-Wall", "-I", os.path.join(X86, "src"),
                             os.path.join(X86, "tests", "lan_broadcast_test.cpp"),
                             os.path.join(X86, "src", "runtime", "hle", "lan_broadcast.cpp"), "-o", binp],
                            capture_output=True, text=True)
        if cc.returncode:
            print("FAIL lan_broadcast_test builds\n" + cc.stderr[:3000])
            return 1
        r = subprocess.run([binp], capture_output=True, text=True, timeout=60)
        sys.stdout.write(r.stdout)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
