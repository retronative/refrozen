#!/usr/bin/env python3
"""The mutation gate's own rules (tests/mutate.py), no x86recomp build:

  /opt/homebrew/bin/python3 -I tests/test_mutate.py

- A restored mutant file is rebuilt even when the next sync gives it its
  source's older mtime again (a fixture tree with rsync and a real ninja file).
- A focused run decides a mutant only when it is KILLED by the expected check;
  anything else goes to the whole test, and so does a mutant whose group's
  unmutated run does not print its expected check.
- classify never turns a timeout or a crash into KILLED.
- --changed: a file's mutants, a patch's files, a runtime header, an imported
  test, a changed registry entry.
- Every test_win32, test_first_run_setup and test_builder_poc mutant maps to a
  group its test's --modes knows.
- --jobs: which mutants run alone; a mutant or whole test that must run alone
  overlaps no other run; each worker has its own scratch tree; results keep the
  selection's order.
- The focused runs' reused fixtures are invalidated by any change of their
  inputs: test_builder_poc's launcher (launcher_key) and the lift
  (scripts/poc/lift_fixture.sh: a changed input file, a file added to an input
  folder, an argument, the lifter, the kit's stamp; a failed lift is not kept).
Prints a FAIL line per failing check.
"""
import ast
import os
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutate  # noqa: E402
import test_builder_poc  # noqa: E402
from mutants import MUTANTS  # noqa: E402

SCRIPTS = os.environ.get("REFROZEN_SCRIPTS",
                         os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


def write(path, text, mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def ninja_has_work(scratch):
    r = subprocess.run(["ninja", "-C", os.path.join(scratch, "build"), "-n"] + mutate.X86_TARGETS,
                       capture_output=True, text=True)
    return "no work to do" not in r.stdout


def stale(tmp):
    root, scratch = os.path.join(tmp, "root"), os.path.join(tmp, "scratch")
    old = time.time() - 3600
    write(os.path.join(root, "tools", "x86recomp", "src", "a.cpp"), "int x = 1;\n", old)
    for d in ("scripts", "tests", "src", "app"):
        os.makedirs(os.path.join(root, d))
    targets = "".join(f"build {t}: phony stamp\n" for t in mutate.X86_TARGETS)
    write(os.path.join(scratch, "build", "build.ninja"),
          "rule touch\n  command = touch $out\nbuild stamp: touch ../x86recomp/src/a.cpp\n" + targets)
    saved = mutate.ROOT, mutate.SRC_X86, mutate.run_test
    mutate.ROOT, mutate.SRC_X86 = root, os.path.join(root, "tools", "x86recomp")
    mutate.run_test = lambda *a, **k: (1, "FAIL E: got 1, want 2")
    try:
        mutate.sync(scratch)
        check("stale: the unmutated build", mutate.build(scratch)[0], True)
        m = dict(id="T1", file="tools/x86recomp/src/a.cpp", old="x = 1", new="x = 2", test="loader", expect="E")
        check("stale: the mutant is killed", mutate.mutate_one(m, 60, scratch)[0], "KILLED")
        check("stale: the restored file is recorded", mutate.restored_unbuilt(scratch), ["x86recomp/src/a.cpp"])
        mutate.sync(scratch)  # rsync: the restored file gets the source's older mtime
        check("stale: after a sync, the restored file is rebuilt", ninja_has_work(scratch), True)
        check("stale: a successful build", mutate.build(scratch)[0], True)
        check("stale: a successful build clears the record", mutate.restored_unbuilt(scratch), [])
        mutate.sync(scratch)
        check("stale: then a sync leaves nothing to rebuild", ninja_has_work(scratch), False)
    finally:
        mutate.ROOT, mutate.SRC_X86, mutate.run_test = saved


def focused():
    m = dict(id="T2", test="win32", expect="Q: the read completes", file="x")
    check("group: by prefix", mutate.group_of(m), "Q")
    check("group: mode A's flags", mutate.group_of(dict(m, expect="iocp: a post wakes")), "A")
    check("group: none for another test", mutate.group_of(dict(m, test="loader")), None)
    check("group: none for an unknown prefix", mutate.group_of(dict(m, expect="zz: x")), None)
    tree = mutate.Tree(False, 60)
    printed = ["ok   Q: the read completes"]
    tree.baseline = lambda test, args: printed
    saved = mutate.mutate_one
    calls = []
    try:
        for status, decided in (("KILLED", True), ("SURVIVED", False), ("KILLED-OTHER", False),
                                ("TIMEOUT", False), ("INVALID", True)):
            mutate.mutate_one = lambda *a, s=status, **k: (calls.append(a) or (s, "d"))
            check(f"focused: {status} " + ("decides" if decided else "goes to the whole test"),
                  tree.focused(m)[2], decided)
        printed[:] = ["ok   Q: something else"]
        calls.clear()
        r = tree.focused(m)
        check("focused: a group that does not print the expected check: the whole test",
              (r[2], len(calls)), (False, 0))
    finally:
        mutate.mutate_one = saved


def classify():
    m = dict(expect="E: x")
    check("classify: a timeout is never KILLED", mutate.classify(m, None, "FAIL E: x", 60)[0], "TIMEOUT")
    check("classify: a crash without the check", mutate.classify(m, 1, "Traceback", 60)[0], "KILLED-OTHER")
    check("classify: the expected check", mutate.classify(m, 1, "ok   a\nFAIL E: x: got 1", 60)[0], "KILLED")
    check("classify: a pass", mutate.classify(m, 0, "", 60)[0], "SURVIVED")
    check("classify: a documented equivalent", mutate.classify(dict(m, equivalent="why"), 0, "", 60)[0], "EQUIVALENT")


def changed(tmp):
    root = os.path.join(tmp, "root2")
    write(os.path.join(root, "patches", "x86recomp", "0099-t.patch"),
          "--- a/src/runtime/hle/x.cpp\n+++ b/src/runtime/hle/x.cpp\n@@ -1 +1 @@\n")
    ms = [dict(id="C1", file="tools/x86recomp/src/runtime/hle/x.cpp", test="win32"),
          dict(id="C2", file="tools/x86recomp/src/runtime/y.cpp", test="loader"),
          dict(id="C3", file="scripts/z.py", test="font", new="a")]
    names = []
    old_registry = repr([ms[0], ms[1], dict(ms[2], new="b")])

    def git(*args):
        if args[0] == "diff":
            return "\n".join(n for n in names if not n.startswith("new:"))
        if args[0] == "ls-files":
            return "\n".join(n[4:] for n in names if n.startswith("new:"))
        if args[0] == "ls-tree":
            return "x" if args[2] == "tests/mutants.py" else ""
        if args[0] == "show":
            return "MUTANTS = " + old_registry
        raise AssertionError(args)
    saved = mutate.git, mutate.ROOT
    mutate.git, mutate.ROOT = git, root
    try:
        for paths, want, what in (
                (["tools/x86recomp/src/runtime/hle/x.cpp"], ["C1"], "a changed file selects its mutants"),
                (["patches/x86recomp/0099-t.patch"], ["C1"], "a changed patch selects the mutants in the files it changes"),
                (["tools/x86recomp/src/runtime/log.h"], ["C1", "C2"], "a runtime header selects every runtime mutant"),
                (["tests/test_loader.py"], ["C1", "C2"], "a changed test_loader.py selects test_win32's mutants"),
                (["tests/mutants.py"], ["C3"], "a changed registry entry is selected"),
                (["new:patches/x86recomp/0099-t.patch"], ["C1"], "a new patch not yet added selects the mutants in the files it changes"),
                (["README.md"], [], "an unrelated change selects nothing")):
            names[:] = paths
            check(f"changed: {what}", [m["id"] for m in mutate.changed_mutants("REF", ms)], want)
    finally:
        mutate.git, mutate.ROOT = saved


def registry_groups():
    for test, name in (("win32", "MODE_GROUPS"), ("setup", "GROUPS"), ("builder", "CASES")):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), mutate.TESTS[test])).read()
        groups = next(ast.literal_eval(n.value) for n in ast.parse(src).body
                      if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name)
        unmapped = [m["id"] for m in MUTANTS if m["test"] == test and mutate.group_of(m) not in groups]
        check(f"registry: every {mutate.TESTS[test]} mutant maps to a --modes group", unmapped, [])


def parallel():
    w = lambda expect, test="win32", **k: dict(id=expect[:2] + test, test=test, expect=expect, file="x", **k)
    check("serial: a stall-recorder group runs alone", mutate.serial(w("S: a frame")), True)
    check("serial: a window-message group may share", mutate.serial(w("W: popup")), False)
    check("serial: a test_win32 mutant without a group runs alone", mutate.serial(w("zz: x")), True)
    check("serial: a whole test_win32 run runs alone", mutate.serial(w("W: popup"), whole=True), True)
    check("serial: the setup's install runs alone", mutate.serial(w("install: x", "setup")), True)
    check("serial: the setup's input checks may share", mutate.serial(w("key: x", "setup")), False)
    check("serial: every builder case runs alone", mutate.serial(w("launcher: x", "builder")), True)
    check("serial: the LAN broadcast test runs alone", mutate.serial(w("x", "bcast")), True)
    check("serial: a loader mutant may share, whole or not", mutate.serial(w("x", "loader"), whole=True), False)

    runs, lock = [], threading.Lock()
    # P10's and P11's whole tests (the parallel phase) wait for P13's whole test_win32 run (0.5 s at
    # most), so that run overlaps them whenever it is started in the parallel phase, whatever the timing.
    p13_whole = threading.Event()

    class Fake:
        def __init__(self, needs_x86, timeout, path):
            self.path = path

        def prepare(self):
            pass

        def _run(self, m, kind):
            t0 = time.time()
            if kind == "whole" and m["id"] == "P13":
                p13_whole.set()
            elif kind == "whole" and m["id"] in ("P10", "P11"):
                p13_whole.wait(0.5)
            time.sleep(0.03)
            with lock:
                runs.append((self.path, kind, m["id"], t0, time.time()))

        def focused(self, m):
            self._run(m, "focused")
            return ("KILLED", "d", True) if m.get("kill", True) else ("SURVIVED", "d", False)

        def whole(self, m):
            self._run(m, "whole")
            return "KILLED", "d"

    sel = ([w(f"W: {i}") for i in range(6)] + [w(f"S: {i}") for i in range(3)] + [w("x", "bcast")]
           + [w(f"x{i}", "loader", kill=False) for i in range(3)] + [w("W: survives", kill=False)])
    for i, m in enumerate(sel):
        m["id"] = f"P{i}"
    alone = {m["id"] for m in sel if mutate.serial(m)} | {"P13"}  # P13: its whole test_win32 run
    saved, saved_report = mutate.Tree, mutate.report
    mutate.Tree, mutate.report = Fake, lambda *a: None
    try:
        out = mutate.run_focused(sel, False, 60, jobs=3)
        check("parallel: results in the selection's order", [m["id"] for m, _, _ in out], [m["id"] for m in sel])
        check("parallel: each worker has its own scratch tree", len({r[0] for r in runs}), 3)
        clash = [(a[2], a[1], b[2], b[1]) for a in runs for b in runs if a is not b and
                 (a[2] in alone and (a[1] == "whole" or a[2] != "P13")) and a[3] < b[4] and b[3] < a[4]]
        check("parallel: a mutant that must run alone runs with nothing else", clash, [])
        whole13 = [r for r in runs if r[2] == "P13" and r[1] == "whole"]
        check("parallel: a whole test of test_win32 runs alone, on build/mutate",
              [(r[0] == mutate.SCRATCH, any(o[3] < r[4] and r[3] < o[4] for o in runs if o is not r))
               for r in whole13], [(True, False)])
        check("parallel: a sharing test's whole test runs in the parallel phase",
              sorted(r[2] for r in runs if r[1] == "whole" and r[2] != "P13"), ["P10", "P11", "P12"])
        runs.clear()
        mutate.run_focused(sel[:4], False, 60, jobs=1)
        check("parallel: --jobs 1 runs every mutant in order on build/mutate",
              [(r[0], r[2]) for r in runs], [(mutate.SCRATCH, m["id"]) for m in sel[:4]])
    finally:
        mutate.Tree, mutate.report = saved, saved_report


def lift_fixture(tmp):
    d = os.path.join(tmp, "lf")
    lifter, stamp, cache, inp, count = (os.path.join(d, n) for n in ("lifter.sh", "stamp.txt", "cache", "in", "count"))
    lifter_text = ("#!/bin/bash\necho x >> " + count + "\nfor a; do [ \"$p\" = --out ] && o=$a; p=$a; done\n"
                   "[ -e " + os.path.join(d, "fail") + " ] && exit 3\ncat " + os.path.join(inp, "*.tsv") +
                   " > \"$o/gen.cpp\"\n")
    write(lifter, lifter_text)
    os.chmod(lifter, 0o755)
    write(stamp, "s1\n")
    write(os.path.join(inp, "f.tsv"), "one\n")
    write(os.path.join(d, "m.manifest"), "m1\n")

    def lift(arg="A"):
        out = tempfile.mkdtemp(dir=d)
        r = subprocess.run(["/bin/bash", os.path.join(SCRIPTS, "poc", "lift_fixture.sh"), lifter, stamp, cache,
                            "--symbols", inp, "--manifest", os.path.join(d, "m.manifest"), "--x", arg, "--out", out],
                           capture_output=True, text=True)
        got = open(os.path.join(out, "gen.cpp")).read() if os.path.exists(os.path.join(out, "gen.cpp")) else None
        return r.returncode, got, len(open(count).read().split()) if os.path.exists(count) else 0

    check("lift fixture: the first lift runs the lifter", lift(), (0, "one\n", 1))
    check("lift fixture: the same inputs reuse its output", lift(), (0, "one\n", 1))
    write(os.path.join(inp, "f.tsv"), "two\n")
    check("lift fixture: a changed file in an input folder lifts again", lift(), (0, "two\n", 2))
    write(os.path.join(inp, "g.tsv"), "")
    check("lift fixture: a file added to an input folder lifts again", lift()[2], 3)
    write(os.path.join(d, "m.manifest"), "m2\n")
    check("lift fixture: a changed input file lifts again", lift()[2], 4)
    check("lift fixture: another argument lifts again", lift("B")[2], 5)
    write(stamp, "s2\n")
    check("lift fixture: another kit stamp lifts again", lift("B")[2], 6)
    write(lifter, lifter_text + "# another lifter\n")
    check("lift fixture: another lifter lifts again", lift("B")[2], 7)
    write(os.path.join(d, "fail"), "")
    write(stamp, "s3\n")
    check("lift fixture: a failed lift fails", lift("B")[0], 3)
    os.remove(os.path.join(d, "fail"))
    check("lift fixture: a failed lift is not kept", lift("B")[2], 9)


def launcher_cache(tmp):
    d = os.path.join(tmp, "lk")
    for rel, text in (("root/src/main.cpp", "int main(){}"), ("x86/src/runtime/a.h", "#pragma once"),
                      ("x86/src/runtime/a.cpp", "int a;"), ("kit/lib/librecomp_runtime.dylib", "lib1")):
        write(os.path.join(d, rel), text)
    saved = test_builder_poc.ROOT, test_builder_poc.X86, test_builder_poc.KIT
    test_builder_poc.ROOT, test_builder_poc.X86, test_builder_poc.KIT = (os.path.join(d, n) for n in ("root", "x86", "kit"))
    try:
        key = lambda: test_builder_poc.launcher_key(["clang++", os.path.join(d, "t", "refrozen")], os.path.join(d, "t"))
        k0 = key()
        check("launcher key: unchanged inputs, the same key", key(), k0)
        write(os.path.join(d, "x86/src/runtime/a.cpp"), "int b;")
        check("launcher key: a runtime source the launcher does not compile", key(), k0)
        for rel, text, what in (("root/src/main.cpp", "int main(){return 1;}", "a changed main.cpp"),
                                ("x86/src/runtime/a.h", "#pragma once\n#define X", "a changed runtime header"),
                                ("kit/lib/librecomp_runtime.dylib", "lib2", "a changed kit library")):
            write(os.path.join(d, rel), text)
            k1 = key()
            check(f"launcher key: {what}", k1 != k0, True)
            k0 = k1
        k1 = test_builder_poc.launcher_key(["clang++", "-O2", os.path.join(d, "t", "refrozen")], os.path.join(d, "t"))
        check("launcher key: another compile command", k1 != k0, True)
    finally:
        test_builder_poc.ROOT, test_builder_poc.X86, test_builder_poc.KIT = saved


def main():
    with tempfile.TemporaryDirectory() as tmp:
        stale(tmp)
        focused()
        classify()
        changed(tmp)
        registry_groups()
        parallel()
        lift_fixture(tmp)
        launcher_cache(tmp)
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
