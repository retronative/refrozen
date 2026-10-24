#!/usr/bin/env python3
"""Tests for scripts/jumptable_corrections.py (lift input: case targets removed
from pinned jump tables, with errors for corrections that match nothing).

  /opt/homebrew/bin/python3 -I tests/test_jumptable_corrections.py
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.environ.get("REFROZEN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.environ.get("REFROZEN_SCRIPTS", os.path.join(ROOT, "scripts"))  # tests/mutate.py
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


def run(tables, fixes, module):
    with tempfile.TemporaryDirectory() as tmp:
        t, f = os.path.join(tmp, "t.tsv"), os.path.join(tmp, "f.tsv")
        open(t, "w").write(tables)
        open(f, "w").write(fixes)
        r = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "jumptable_corrections.py"), t, f, module],
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr.strip()


TABLES = "jmp\ttargets\n100\tA0,A8,B0\n200\tC0\n"
FIX = "module\tjmp\tremoved_target\treason\n"


def main():
    check("no corrections: unchanged", run(TABLES, FIX, "m"), (0, TABLES, ""))
    check("a correction removes its target",
          run(TABLES, FIX + "m\t100\tA0\twhy\n", "m"), (0, "jmp\ttargets\n100\tA8,B0\n200\tC0\n", ""))
    check("another module's correction is ignored", run(TABLES, FIX + "x\t100\tA0\twhy\n", "m")[:2], (0, TABLES))
    code, _, err = run(TABLES, FIX + "m\t100\tA4\twhy\n", "m")
    check("a target the table lacks is an error", (code != 0, "no case" in err), (True, True))
    code, _, err = run(TABLES, FIX + "m\t300\tA0\twhy\n", "m")
    check("a jump with no table is an error", (code != 0, "no jump table" in err), (True, True))
    print("jumptable corrections: ok" if not failures else f"jumptable corrections: {failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
