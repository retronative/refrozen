#!/usr/bin/env python3
"""The GL context's state tests from x86recomp (M4), built and run here so the
mutation gate can use them on its scratch tree (no game data):

  /opt/homebrew/bin/python3 -I tests/test_gl_context.py

  gl_fog_test      the fog factor the device gets from glFog/GL_FOG against
                   GL 1.5's fog equations (section 3.10)
  gl_texture_test  texel precision of sized internal formats (RGBA4,
                   RGB5_A1, RGB4, RGB5) against GL's fixed-point conversion

Each is compiled with the context sources of REFROZEN_X86RECOMP (default
tools/x86recomp) and prints a FAIL line per failing check; ctest runs the same
programs from the x86recomp build. Needs Homebrew LLVM.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
CXX = "/opt/homebrew/opt/llvm/bin/clang++"


def main():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("gl_fog_test", "gl_texture_test"):
            binp = os.path.join(tmp, name)
            cc = subprocess.run([CXX, "-std=c++20", "-O1", "-w", "-I", os.path.join(X86, "src"),
                                 os.path.join(X86, "tests", name + ".cpp"),
                                 os.path.join(X86, "src", "runtime", "gl", "context.cpp"),
                                 os.path.join(X86, "src", "runtime", "gfx", "format.cpp"), "-o", binp],
                                capture_output=True, text=True)
            if cc.returncode:
                print(f"FAIL {name} builds")
                print(cc.stderr[:3000])
                failures += 1
                continue
            r = subprocess.run([binp], capture_output=True, text=True, timeout=120)
            sys.stdout.write(r.stdout)
            print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {name}")
            failures += r.returncode != 0
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
