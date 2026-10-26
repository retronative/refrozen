#!/usr/bin/env python3
"""Mutation gate: plant each fault of tests/mutants.py in a scratch copy of
the sources and check that its test catches it (ReCarbon's practice).

  /opt/homebrew/bin/python3 -I tests/mutate.py [--only ID,...] [--milestone M3] [--tsv OUT]

The real tree is never modified. build/mutate/ holds a copy of
tools/x86recomp (sources only), scripts/ and tests/, and its own x86recomp
build (configured offline from the fetched dependencies of
tools/x86recomp/out/build/debug). Each run re-syncs the copy, runs every
needed test unmutated (all must pass: a failing baseline aborts the run),
then for each mutant: apply it, rebuild, run its test, restore.

Results:
  KILLED        the test failed and printed the expected failing check
  KILLED-OTHER  the test failed, but not with the expected check (review it)
  TIMEOUT       the test did not finish (a hang caught by the deadline)
  SURVIVED      the test passed: a gap, to be fixed or explained
  EQUIVALENT    survived, and the mutant is documented as equivalent (its
                `equivalent` field says why the program cannot behave
                differently); a documented-equivalent mutant that is killed is
                reported as WRONG-EQUIVALENT
  INVALID       the mutant does not apply exactly once, or the build fails:
                never counted as a kill
Exit 0 iff every selected mutant is KILLED or EQUIVALENT.

Python tests run with -B and the scratch tree's __pycache__ is purged before
each run: two mutants of equal size written within one second would
otherwise share stale bytecode.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.path.join(ROOT, "build", "mutate")
SRC_X86 = os.path.join(ROOT, "tools", "x86recomp")
DEPS = os.path.join(SRC_X86, "out", "build", "debug", "_deps")
PY = "/opt/homebrew/bin/python3"
LLVM = "/opt/homebrew/opt/llvm"
X86_TARGETS = ["recomp_lift", "recomp_runtime", "recomp_x87", "recomp_image", "recomp_opengl"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutants import MUTANTS, TESTS  # noqa: E402


def sync():
    """Copy sources into the scratch tree (rsync: unchanged files keep their
    mtimes, so rebuilds stay incremental)."""
    os.makedirs(SCRATCH, exist_ok=True)
    for src, dst, excl in ((SRC_X86 + "/", "x86recomp/", ["out/", ".git/"]),
                           (os.path.join(ROOT, "scripts") + "/", "scripts/", ["__pycache__/"]),
                           (os.path.join(ROOT, "tests") + "/", "tests/", ["__pycache__/"]),
                           (os.path.join(ROOT, "src") + "/", "src/", []),
                           (os.path.join(ROOT, "app") + "/", "app/", [])):
        cmd = ["rsync", "-a", "--delete", "--checksum"] + [f"--exclude={e}" for e in excl]
        subprocess.run(cmd + [src, os.path.join(SCRATCH, dst)], check=True)


def configure():
    build = os.path.join(SCRATCH, "build")
    if os.path.exists(os.path.join(build, "build.ninja")):
        return
    subprocess.run(["cmake", "-S", os.path.join(SCRATCH, "x86recomp"), "-B", build, "-G", "Ninja",
                    "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_C_COMPILER=clang", "-DCMAKE_CXX_COMPILER=clang++",
                    f"-DRECOMP_LLVM_ROOT={LLVM}", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                    f"-DFETCHCONTENT_SOURCE_DIR_SOFTFLOAT={DEPS}/softfloat-src",
                    f"-DFETCHCONTENT_SOURCE_DIR_ZYDIS={DEPS}/zydis-src"],
                   check=True, stdout=subprocess.DEVNULL)


def build():
    r = subprocess.run(["ninja", "-C", os.path.join(SCRATCH, "build")] + X86_TARGETS,
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]


def env():
    return dict(os.environ, REFROZEN_ROOT=ROOT, REFROZEN_X86RECOMP=os.path.join(SCRATCH, "x86recomp"),
                REFROZEN_X86RECOMP_BUILD=os.path.join(SCRATCH, "build"),
                REFROZEN_SCRIPTS=os.path.join(SCRATCH, "scripts"))


def purge_bytecode():
    for d, subdirs, _ in os.walk(SCRATCH):
        if "__pycache__" in subdirs:
            shutil.rmtree(os.path.join(d, "__pycache__"))
            subdirs.remove("__pycache__")


def run_test(name, timeout):
    purge_bytecode()
    cmd = [PY, "-I", "-B", os.path.join(SCRATCH, "tests", TESTS[name])]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env(), timeout=timeout, cwd=ROOT)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or b"").decode("latin-1", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="comma-separated mutant ids")
    ap.add_argument("--milestone", help="only mutants of this milestone (e.g. M3)")
    ap.add_argument("--tsv", help="write the results here")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    sel = [m for m in MUTANTS
           if (not a.only or m["id"] in a.only.split(",")) and (not a.milestone or m["milestone"] == a.milestone)]
    if not sel:
        sys.exit("no mutants selected")
    ids = [m["id"] for m in MUTANTS]
    if len(ids) != len(set(ids)):
        sys.exit("duplicate mutant ids in tests/mutants.py")

    sync()
    needs_x86 = any(m["file"].startswith("tools/x86recomp/") for m in sel)
    if needs_x86:
        configure()
        ok, log = build()
        if not ok:
            sys.exit("baseline build of the scratch tree failed:\n" + log)
    for t in sorted({m["test"] for m in sel}):
        code, out = run_test(t, a.timeout)
        if code != 0:
            sys.exit(f"baseline: {TESTS[t]} does not pass on the unmutated tree:\n{out[-3000:]}")
        print(f"baseline {TESTS[t]}: pass")

    results = []
    for m in sel:
        rel = m["file"].replace("tools/x86recomp/", "x86recomp/", 1)
        path = os.path.join(SCRATCH, rel)
        orig = open(path, encoding="utf-8").read()
        n = orig.count(m["old"])
        t0 = time.time()
        if n != 1:
            status, detail = "INVALID", f"old text found {n} times"
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(orig.replace(m["old"], m["new"]))
            try:
                ok, log = build() if rel.startswith("x86recomp/") else (True, "")
                if not ok:
                    status, detail = "INVALID", "build failed: " + log.strip().splitlines()[-1][:150]
                else:
                    code, out = run_test(m["test"], a.timeout)
                    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
                    if code is None:
                        status, detail = "TIMEOUT", f"no result in {a.timeout} s"
                    elif code == 0:
                        status, detail = ("EQUIVALENT", m["equivalent"]) if m.get("equivalent") else \
                            ("SURVIVED", "test passed")
                    elif m.get("equivalent"):
                        status, detail = "WRONG-EQUIVALENT", (fails[0] if fails else "test failed")[:150]
                    elif any(m["expect"] in l for l in fails):
                        status, detail = "KILLED", next(l for l in fails if m["expect"] in l)[:150]
                    else:
                        status, detail = "KILLED-OTHER", (fails[0] if fails else out.strip().splitlines()[-1])[:150]
            finally:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(orig)
        results.append((m, status, detail))
        print(f"{status:12} {m['id']:10} {m['milestone']} {m['area']}: {m['fault']}  [{time.time() - t0:.0f} s]")
        print(f"             expected: {m['expect']}")
        print(f"             observed: {detail}")
    if needs_x86:
        build()  # leave the scratch build matching the sources

    counts = {}
    for _, s, _ in results:
        counts[s] = counts.get(s, 0) + 1
    print("\n" + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + f" (of {len(results)})")
    if a.tsv:
        with open(a.tsv, "w") as f:
            f.write("id\tmilestone\tarea\tfile\tfault\ttest\texpected\tresult\tobserved\n")
            for m, s, d in results:
                f.write("\t".join([m["id"], m["milestone"], m["area"], m["file"], m["fault"], TESTS[m["test"]],
                                   m["expect"], s, d.replace("\t", " ")]) + "\n")
    return 0 if all(s in ("KILLED", "EQUIVALENT") for _, s, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
