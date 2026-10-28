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
- Every test_win32 mutant maps to a group test_win32 --modes knows.
Prints a FAIL line per failing check.
"""
import ast
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutate  # noqa: E402
from mutants import MUTANTS  # noqa: E402

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
            return "\n".join(names)
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
                (["README.md"], [], "an unrelated change selects nothing")):
            names[:] = paths
            check(f"changed: {what}", [m["id"] for m in mutate.changed_mutants("REF", ms)], want)
    finally:
        mutate.git, mutate.ROOT = saved


def registry_groups():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_win32.py")).read()
    groups = next(ast.literal_eval(n.value) for n in ast.parse(src).body
                  if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MODE_GROUPS")
    unmapped = [m["id"] for m in MUTANTS if m["test"] == "win32" and mutate.group_of(m) not in groups]
    check("registry: every test_win32 mutant maps to a --modes group", unmapped, [])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        stale(tmp)
        focused()
        classify()
        changed(tmp)
        registry_groups()
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
