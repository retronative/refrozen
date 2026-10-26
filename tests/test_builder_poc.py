#!/usr/bin/env python3
"""The experimental first-run builder and the launcher's module checks
(scripts/poc/, src/main.cpp with REFROZEN_DYNAMIC_MODULE):

  /opt/homebrew/bin/python3 -I tests/test_builder_poc.py

Compiles a launcher from this tree's src/main.cpp against the kit's runtime
libraries and runs scripts/poc/test_errors.sh with it: no Command Line
Tools, a missing installed file, low disk, a compile failure, a cancelled
build, and the launcher refusing a module from another build, a missing one
and a swapped library. Expected behaviour: the builder's documented exit
codes and its rule that a failed or cancelled build leaves nothing partial
and keeps the previous module.

Needs, from the real tree (REFROZEN_ROOT): a kit (build/poc-kit, from
scripts/poc/make_kit.sh on a REFROZEN_DYNAMIC_MODULE build), the player's
install (game/native-install) and a data folder holding a built module
(game/poc/appsupport). About 4 minutes (two lifts). Prints a FAIL line per
failing check.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.environ.get("REFROZEN_ROOT", ROOT)
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
KIT = os.environ.get("REFROZEN_POC_KIT", os.path.join(REAL, "build", "poc-kit"))
INSTALL = os.path.join(REAL, "game", "native-install")
DATA = os.environ.get("REFROZEN_POC_DATA", os.path.join(REAL, "game", "poc", "appsupport"))


def main():
    for path in (KIT, INSTALL, os.path.join(DATA, "build", "current", "war3.dylib")):
        if not os.path.exists(path):
            print(f"FAIL prerequisite missing: {path}")
            return 1
    stamp = open(os.path.join(KIT, "stamp.txt")).read().strip()
    with tempfile.TemporaryDirectory() as tmp:
        launcher = os.path.join(tmp, "refrozen")
        cc = subprocess.run(["/usr/bin/xcrun", "clang++", "-std=gnu++20", "-O1", "-DREFROZEN_DYNAMIC_MODULE",
                             f'-DREFROZEN_MODULE_STAMP="{stamp}"', f'-DREFROZEN_DEFAULT_GAME_DIR="{INSTALL}"',
                             "-I", os.path.join(X86, "src"), os.path.join(ROOT, "src", "main.cpp"),
                             "-L", os.path.join(KIT, "lib"), "-lrecomp_runtime", "-lrecomp_opengl",
                             "-Wl,-rpath," + os.path.join(KIT, "lib"), "-o", launcher],
                            capture_output=True, text=True)
        if cc.returncode:
            print("FAIL the launcher compiles\n" + cc.stderr[-2000:])
            return 1
        r = subprocess.run(["/bin/bash", os.path.join(ROOT, "scripts", "poc", "test_errors.sh"), KIT, INSTALL, DATA],
                           capture_output=True, text=True, env=dict(os.environ, REFROZEN_POC_LAUNCHER=launcher),
                           timeout=1800)
    print(r.stdout, end="")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
