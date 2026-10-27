#!/usr/bin/env python3
"""The main guest stack's end frame (x86recomp RunOnStack, patch 0022):

  /opt/homebrew/bin/python3 -I tests/test_run_on_stack.py

Builds x86recomp's tests/run_on_stack_test.cpp with this tree's platform code
and runs it: a function on a stack switched to by RunOnStack (filled with a
non-zero pattern, an unmapped page above it) walks its own stack with
backtrace(); the walk must end inside the stack. Before the fix it read one
frame record past the stack's end: the intermittent launch crash (exit 4)
when Metal walks the stack while the game creates its device. Prints a FAIL
line per failing check.
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
        binp = os.path.join(tmp, "run_on_stack_test")
        cc = subprocess.run([CXX, "-std=c++20", "-O2", "-w", "-I", os.path.join(X86, "src"),
                             os.path.join(X86, "tests", "run_on_stack_test.cpp"),
                             os.path.join(X86, "src", "runtime", "platform.cpp"), "-o", binp],
                            capture_output=True, text=True)
        if cc.returncode:
            print("FAIL run_on_stack_test builds\n" + cc.stderr[:3000])
            return 1
        # Each run gets its own address layout; a few runs, as the crash depended on it.
        for _ in range(5):
            r = subprocess.run([binp], capture_output=True, text=True, timeout=60)
            if r.returncode:
                sys.stdout.write(r.stdout)
                return r.returncode
        sys.stdout.write(r.stdout)
        return 0


if __name__ == "__main__":
    sys.exit(main())
