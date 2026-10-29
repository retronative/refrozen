#!/usr/bin/env python3
"""The experimental first-run builder and the launcher's module checks
(scripts/poc/, src/main.cpp with REFROZEN_DYNAMIC_MODULE):

  /opt/homebrew/bin/python3 -I tests/test_builder_poc.py [--modes clt,missing,...] [--cache DIR]

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
(game/poc/appsupport). About 4 minutes (three lifts). Prints a FAIL line per
failing check.

--modes runs only the named cases of test_errors.sh (the mutation gate's
focused runs): clt missing disk compile cancel space launcher; the last line
says so. --cache DIR reuses the compiled launcher from DIR when every input of
its compile is unchanged (see launcher_key); with --modes, the cases that lift
also reuse the real lifter's output from DIR when every input of the lift is
unchanged (test_errors.sh, REFROZEN_POC_LIFT_CACHE). A run without --modes
always lifts.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.environ.get("REFROZEN_ROOT", ROOT)
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))
KIT = os.environ.get("REFROZEN_POC_KIT", os.path.join(REAL, "build", "poc-kit"))
INSTALL = os.path.join(REAL, "game", "native-install")
DATA = os.environ.get("REFROZEN_POC_DATA", os.path.join(REAL, "game", "poc", "appsupport"))
CASES = ("clt", "missing", "disk", "compile", "cancel", "space", "launcher")


def launcher_key(cmd, tmp):
    """Every input of the launcher's compile: the compiler, the command with this run's
    temporary paths made relative, src/main.cpp, every header below x86recomp/src and
    the kit's libraries. Equal keys: the same launcher."""
    h = hashlib.sha256(subprocess.run(["/usr/bin/xcrun", "--find", "clang++"], capture_output=True,
                                      text=True).stdout.encode())
    for a in cmd:
        h.update(b"\0" + (os.path.relpath(a, tmp) if a.startswith(tmp + os.sep) else a).encode())
    with open(os.path.join(ROOT, "src", "main.cpp"), "rb") as f:
        h.update(f.read())
    for base in (os.path.join(X86, "src"), os.path.join(KIT, "lib")):
        for d, subdirs, files in sorted(os.walk(base)):
            subdirs.sort()
            for n in sorted(files):
                if base.endswith("lib") or n.endswith((".h", ".hpp", ".inc", ".def")):
                    with open(os.path.join(d, n), "rb") as f:
                        h.update(b"\0" + os.path.relpath(os.path.join(d, n), base).encode() + b"\0" + f.read())
    return h.hexdigest()


def main():
    cases, cache = None, None
    args = sys.argv[1:]
    while args:
        if args[0] == "--modes" and len(args) > 1:
            cases = args[1].split(",")
            if not cases or set(cases) - set(CASES):
                sys.exit(f"--modes: unknown case(s) {sorted(set(cases) - set(CASES))}; cases: {' '.join(CASES)}")
        elif args[0] == "--cache" and len(args) > 1:
            cache = os.path.abspath(args[1])
        else:
            sys.exit("usage: test_builder_poc.py [--modes clt,missing,...] [--cache DIR]")
        args = args[2:]
    for path in (KIT, INSTALL, os.path.join(DATA, "build", "current", "war3.dylib")):
        if not os.path.exists(path):
            print(f"FAIL prerequisite missing: {path}")
            return 1
    stamp = open(os.path.join(KIT, "stamp.txt")).read().strip()
    with tempfile.TemporaryDirectory() as tmp:
        launcher = os.path.join(tmp, "refrozen")
        cmd = ["/usr/bin/xcrun", "clang++", "-std=gnu++20", "-O1", "-DREFROZEN_DYNAMIC_MODULE",
               f'-DREFROZEN_MODULE_STAMP="{stamp}"', f'-DREFROZEN_DEFAULT_GAME_DIR="{INSTALL}"',
               "-I", os.path.join(X86, "src"), os.path.join(ROOT, "src", "main.cpp"),
               "-L", os.path.join(KIT, "lib"), "-lrecomp_runtime", "-lrecomp_opengl",
               "-Wl,-rpath," + os.path.join(KIT, "lib"), "-o", launcher]
        cached = cache and os.path.join(cache, "launcher-" + launcher_key(cmd, tmp))
        if cached and os.path.exists(cached):
            shutil.copy2(cached, launcher)
            cc = subprocess.CompletedProcess(cmd, 0, "", "")
        else:
            cc = subprocess.run(cmd, capture_output=True, text=True)
            if cached and cc.returncode == 0:
                os.makedirs(cache, exist_ok=True)
                shutil.copy2(launcher, cached + ".tmp")
                os.replace(cached + ".tmp", cached)
        if cc.returncode:
            print("FAIL the launcher compiles\n" + cc.stderr[-2000:])
            return 1
        env = dict(os.environ, REFROZEN_POC_LAUNCHER=launcher)
        env.pop("REFROZEN_POC_CASES", None)
        env.pop("REFROZEN_POC_LIFT_CACHE", None)
        if cases:
            env["REFROZEN_POC_CASES"] = ",".join(cases)
            if cache:
                env["REFROZEN_POC_LIFT_CACHE"] = os.path.join(cache, "lift")
        r = subprocess.run(["/bin/bash", os.path.join(ROOT, "scripts", "poc", "test_errors.sh"), KIT, INSTALL, DATA],
                           capture_output=True, text=True, env=env, timeout=1800)
    print(r.stdout, end="")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
