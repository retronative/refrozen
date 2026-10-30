#!/usr/bin/env python3
"""Mutation gate: plant each fault of tests/mutants.py in a scratch copy of
the sources and check that its test catches it (ReCarbon's practice).

  /opt/homebrew/bin/python3 -I tests/mutate.py [--only ID,...] [--milestone M3] [--tsv OUT]
                                               [--changed REF] [--focused [--jobs N]]

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

Without --focused this is the release-level gate: every selected
mutant, its whole test, one at a time.

--focused: a mutant of test_win32, test_first_run_setup or test_builder_poc
runs only the --modes group of its test that prints its expected check
(FOCUS_GROUPS in mutants.py). Compiled test programs are reused while every
input of their compile is unchanged (test_win32 and test_builder_poc --cache),
and test_builder_poc's focused cases reuse the real lifter's output while every
input of the lift is unchanged. Before a group is used on a scratch tree, its
unmutated run there must pass and print the mutant's expected check as ok;
otherwise the mutant runs its whole test. A focused run counts only when it is
KILLED by the expected check: any other outcome (survived, another check, a
timeout, a crash) is decided by the whole test, which never reuses a lift, and
the result says so.

--jobs N (with --focused): N scratch trees (build/mutate, build/mutate-2, ...),
each with its own sources, build, test caches and bytecode. First every mutant
that may share the Mac runs, one per tree at a time; then, on build/mutate with
nothing else running, the mutants that must run alone (SERIAL_TESTS and
SERIAL_GROUPS in mutants.py: real-time waits and measurements, the network and
fixed ports, every core) and the whole-test runs of tests with such groups.

--changed REF: only the mutants that the changes since REF (committed, not
yet committed, or in new files not yet added) can affect: those in changed files (a changed patches/x86recomp patch
counts as the files it changes), those of changed tests and of the tests that
import them, those changed in mutants.py, and CHANGE_SCOPE's rules.

Python tests run with -B and the scratch tree's __pycache__ is purged before
each run: two mutants of equal size written within one second would
otherwise share stale bytecode.
"""
import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.path.join(ROOT, "build", "mutate")
SRC_X86 = os.path.join(ROOT, "tools", "x86recomp")
DEPS = os.path.join(SRC_X86, "out", "build", "debug", "_deps")
PY = "/opt/homebrew/bin/python3"
LLVM = "/opt/homebrew/opt/llvm"
X86_TARGETS = ["recomp_lift", "recomp_runtime", "recomp_x87", "recomp_image", "recomp_opengl"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutants import (CHANGE_SCOPE, FOCUS_GROUPS, MUTANTS, SERIAL_GROUPS, SERIAL_TESTS, TEST_IMPORTS,  # noqa: E402
                     TESTS)
CACHED = ("win32", "builder")  # tests that take --cache DIR


def sync(scratch=SCRATCH):
    """Copy sources into the scratch tree (rsync: unchanged files keep their
    mtimes, so rebuilds stay incremental)."""
    os.makedirs(scratch, exist_ok=True)
    for src, dst, excl in ((SRC_X86 + "/", "x86recomp/", ["out/", ".git/"]),
                           (os.path.join(ROOT, "scripts") + "/", "scripts/", ["__pycache__/"]),
                           (os.path.join(ROOT, "tests") + "/", "tests/", ["__pycache__/"]),
                           (os.path.join(ROOT, "src") + "/", "src/", []),
                           (os.path.join(ROOT, "app") + "/", "app/", []),
                           (os.path.join(ROOT, "config") + "/", "config/", [])):
        if not os.path.isdir(src):
            continue
        cmd = ["rsync", "-a", "--delete", "--checksum"] + [f"--exclude={e}" for e in excl]
        subprocess.run(cmd + [src, os.path.join(scratch, dst)], check=True)
    for name in ("VERSION", "CMakeLists.txt"):  # read from the root: the release scripts, test_event_data
        if os.path.exists(os.path.join(ROOT, name)):
            shutil.copy2(os.path.join(ROOT, name), os.path.join(scratch, name))
    # rsync gives a restored mutant file its source's (older) mtime again,
    # which would leave the mutant's object in the build: touch it.
    for rel in restored_unbuilt(scratch):
        if os.path.exists(os.path.join(scratch, rel)):
            os.utime(os.path.join(scratch, rel))


def restored_unbuilt(scratch):
    """Mutated files restored since the scratch build last succeeded."""
    marker = os.path.join(scratch, ".restored-unbuilt")
    return open(marker).read().split() if os.path.exists(marker) else []


def mark_restored(scratch, rel):
    with open(os.path.join(scratch, ".restored-unbuilt"), "a") as f:
        f.write(rel + "\n")


def configure(scratch=SCRATCH):
    build = os.path.join(scratch, "build")
    if os.path.exists(os.path.join(build, "build.ninja")):
        return
    subprocess.run(["cmake", "-S", os.path.join(scratch, "x86recomp"), "-B", build, "-G", "Ninja",
                    "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_C_COMPILER=clang", "-DCMAKE_CXX_COMPILER=clang++",
                    f"-DRECOMP_LLVM_ROOT={LLVM}", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                    f"-DFETCHCONTENT_SOURCE_DIR_SOFTFLOAT={DEPS}/softfloat-src",
                    f"-DFETCHCONTENT_SOURCE_DIR_ZYDIS={DEPS}/zydis-src"],
                   check=True, stdout=subprocess.DEVNULL)


def build(scratch=SCRATCH):
    r = subprocess.run(["ninja", "-C", os.path.join(scratch, "build")] + X86_TARGETS,
                       capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(os.path.join(scratch, ".restored-unbuilt")):
        os.remove(os.path.join(scratch, ".restored-unbuilt"))  # restored files are compiled now
    return r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]


def env(scratch=SCRATCH):
    return dict(os.environ, REFROZEN_ROOT=ROOT, REFROZEN_X86RECOMP=os.path.join(scratch, "x86recomp"),
                REFROZEN_X86RECOMP_BUILD=os.path.join(scratch, "build"),
                REFROZEN_SCRIPTS=os.path.join(scratch, "scripts"))


def purge_bytecode(scratch=SCRATCH):
    for d, subdirs, _ in os.walk(scratch):
        if "__pycache__" in subdirs:
            shutil.rmtree(os.path.join(d, "__pycache__"))
            subdirs.remove("__pycache__")


def run_test(name, timeout, scratch=SCRATCH, args=()):
    purge_bytecode(scratch)
    cmd = [PY, "-I", "-B", os.path.join(scratch, "tests", TESTS[name]), *args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env(scratch), timeout=timeout, cwd=ROOT)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or b"").decode("latin-1", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")


def classify(m, code, out, timeout):
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    if code is None:
        return "TIMEOUT", f"no result in {timeout} s"
    if code == 0:
        return ("EQUIVALENT", m["equivalent"]) if m.get("equivalent") else ("SURVIVED", "test passed")
    if m.get("equivalent"):
        return "WRONG-EQUIVALENT", (fails[0] if fails else "test failed")[:150]
    if any(m["expect"] in l for l in fails):
        return "KILLED", next(l for l in fails if m["expect"] in l)[:150]
    return "KILLED-OTHER", (fails[0] if fails else out.strip().splitlines()[-1])[:150]


def mutate_one(m, timeout, scratch=SCRATCH, args=()):
    """Plant m in the scratch tree, rebuild, run its test (with args), restore."""
    rel = m["file"].replace("tools/x86recomp/", "x86recomp/", 1)
    path = os.path.join(scratch, rel)
    orig = open(path, encoding="utf-8").read()
    n = orig.count(m["old"])
    if n != 1:
        return "INVALID", f"old text found {n} times"
    with open(path, "w", encoding="utf-8") as f:
        f.write(orig.replace(m["old"], m["new"]))
    try:
        ok, log = build(scratch) if rel.startswith("x86recomp/") else (True, "")
        if not ok:
            return "INVALID", "build failed: " + log.strip().splitlines()[-1][:150]
        code, out = run_test(m["test"], timeout, scratch, args)
        return classify(m, code, out, timeout)
    finally:
        with open(path, "w", encoding="utf-8") as f:
            f.write(orig)
        if rel.startswith("x86recomp/"):
            mark_restored(scratch, rel)


PRINT = threading.Lock()


def report(m, status, detail, t0):
    with PRINT:
        print(f"{status:12} {m['id']:10} {m['milestone']} {m['area']}: {m['fault']}  [{time.time() - t0:.0f} s]")
        print(f"             expected: {m['expect']}")
        print(f"             observed: {detail}", flush=True)


# --- focused runs -------------------------------------------------------

def group_of(m):
    """The --modes group of m's test that prints m's expected check, or None."""
    return next((g for prefix, g in FOCUS_GROUPS.get(m["test"], ()) if m["expect"].startswith(prefix)), None)


def serial(m, whole=False):
    """Whether m's run must have the Mac to itself: its test, its focused group or,
    for a whole-test run, any group of its test (SERIAL_TESTS, SERIAL_GROUPS)."""
    groups = SERIAL_GROUPS.get(m["test"], {})
    return m["test"] in SERIAL_TESTS or bool(groups) and (whole or group_of(m) is None or group_of(m) in groups)


class Baseline(Exception):
    pass


class Tree:
    """The scratch tree and the unmutated runs made on it."""

    def __init__(self, needs_x86, timeout, path=SCRATCH):
        self.path, self.needs_x86, self.timeout = path, needs_x86, timeout
        self.cache = os.path.join(path, "test-cache")
        self.ok = {}  # (test, args) -> the ok lines of its passing unmutated run

    def prepare(self):
        sync(self.path)
        if self.needs_x86:
            configure(self.path)
            ok, log = build(self.path)
            if not ok:
                raise Baseline("baseline build of the scratch tree failed:\n" + log)

    def args(self, test, group):
        return ("--modes", group) + (("--cache", self.cache) if test in CACHED else ())

    def baseline(self, test, args):
        """The ok lines of the unmutated run; Baseline if it does not pass."""
        key = (test, args)
        if key not in self.ok:
            if self.needs_x86:
                ok, log = build(self.path)  # the previous mutant's file was restored
                if not ok:
                    raise Baseline("rebuild of the unmutated scratch tree failed:\n" + log)
            code, out = run_test(test, self.timeout, self.path, args)
            shown = f"--modes {args[1]}" if args[:1] == ("--modes",) else ""
            shown += f" ({os.path.basename(self.path)})" if self.path != SCRATCH else ""
            if code != 0:
                raise Baseline(f"baseline: {TESTS[test]} {shown} does not pass on the unmutated tree:\n"
                               f"{out[-3000:]}")
            self.ok[key] = [l for l in out.splitlines() if l.startswith("ok  ")]
            with PRINT:
                print(f"baseline {TESTS[test]} {shown}".rstrip() + ": pass", flush=True)
        return self.ok[key]

    def whole_args(self, m):
        return ("--cache", self.cache) if m["test"] in CACHED else ()

    def focused(self, m):
        """(status, detail, decided): decided False means the whole test must decide."""
        g = group_of(m)
        if g is not None and not any(m["expect"] in l for l in self.baseline(m["test"], self.args(m["test"], g))):
            g = None  # the mapping does not hold for this check: the whole test
        if g is None:
            return None, "no focused group", False
        status, detail = mutate_one(m, self.timeout, self.path, self.args(m["test"], g))
        if status == "KILLED":
            return status, detail, True
        if status == "INVALID":  # does not apply or does not build: the same for the whole test
            return status, detail, True
        return status, detail, False

    def whole(self, m):
        self.baseline(m["test"], self.whole_args(m))
        return mutate_one(m, self.timeout, self.path, self.whole_args(m))


def decide(tree, m, focused_status=None, t0=None):
    """m's result on tree: its focused run, then its whole test if that does not decide
    (focused_status: the focused run already made, the whole test still to run)."""
    t0 = t0 or time.time()
    if focused_status is None:
        status, detail, decided = tree.focused(m)
        if decided:
            report(m, status, detail, t0)
            return status, detail
        focused_status = status or "none"
    status, detail = tree.whole(m)
    detail += f"  (whole test; focused: {focused_status})"
    report(m, status, detail, t0)
    return status, detail


def run_focused(sel, needs_x86, timeout, jobs=1):
    trees = [Tree(needs_x86, timeout, SCRATCH if i == 0 else f"{SCRATCH}-{i + 1}") for i in range(jobs)]
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(Tree.prepare, trees))
    results = {}
    if jobs == 1:
        alone, shared = sel, []
    else:
        alone, shared = [m for m in sel if serial(m)], [m for m in sel if not serial(m)]
    later = []  # (m, focused status, t0): whole tests that must run alone

    def worker(tree):
        while True:
            with PRINT:
                if not shared:
                    return
                m = shared.pop(0)
            t0 = time.time()
            try:
                status, detail, decided = tree.focused(m)
                if decided:
                    report(m, status, detail, t0)
                    results[m["id"]] = (status, detail)
                elif serial(m, whole=True):
                    with PRINT:
                        later.append((m, status or "none", t0))
                else:
                    results[m["id"]] = decide(tree, m, status or "none", t0)
            except Baseline:
                with PRINT:
                    shared.clear()  # the other workers stop after their current mutant
                raise

    if shared:
        with ThreadPoolExecutor(jobs) as ex:
            list(ex.map(worker, trees))  # re-raises a worker's Baseline
        if jobs > 1:
            with PRINT:
                print(f"parallel phase done: {len(results)} decided, {len(later)} whole tests to run alone, "
                      f"{len(alone)} mutants to run alone", flush=True)
    for m in alone:
        results[m["id"]] = decide(trees[0], m)
    for m, fs, t0 in later:
        results[m["id"]] = decide(trees[0], m, fs, t0)
    if needs_x86:
        for tree in trees:
            build(tree.path)  # leave the scratch builds matching the sources
    return [(m, *results[m["id"]]) for m in sel]


# --- selection by change ------------------------------------------------

def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout


def changed_mutants(ref, mutants):
    names = set(git("diff", "--name-only", ref).split())
    names |= set(git("ls-files", "--others", "--exclude-standard").split())  # new, not yet added
    files = set(names)
    for n in names:
        if n.startswith("patches/x86recomp/") and n.endswith(".patch"):
            texts = [git("show", f"{ref}:{n}") if git("ls-tree", ref, n) else ""]
            if os.path.exists(os.path.join(ROOT, n)):
                texts.append(open(os.path.join(ROOT, n), encoding="utf-8", errors="replace").read())
            for t in texts:
                files |= {"tools/x86recomp/" + l[6:].strip() for l in t.splitlines() if l.startswith("+++ b/")}
    tests = {k for k, v in TESTS.items() if "tests/" + v in files}
    for v, keys in TEST_IMPORTS.items():
        if "tests/" + v in files:
            tests |= set(keys)
    changed_ids = set()
    if "tests/mutants.py" in files and git("ls-tree", ref, "tests/mutants.py"):
        old = {}
        src = git("show", f"{ref}:tests/mutants.py")
        exec(compile(src, "mutants.py@" + ref, "exec"), old)
        before = {m["id"]: m for m in old["MUTANTS"]}
        changed_ids = {m["id"] for m in mutants if before.get(m["id"]) != m}
    elif "tests/mutants.py" in files:
        changed_ids = {m["id"] for m in mutants}
    prefixes, scope_tests = set(), set()
    for path, suffix, target in CHANGE_SCOPE:
        if any(f.startswith(path) and f.endswith(suffix) for f in files):
            if target.startswith("test:"):
                scope_tests.add(target[5:])
            else:
                prefixes.add(target)
    sel = [m for m in mutants
           if m["file"] in files or m["test"] in tests | scope_tests or m["id"] in changed_ids
           or any(m["file"].startswith(p) for p in prefixes)]
    print(f"--changed {ref}: {len(names)} changed paths, {len(files) - len(names)} files through patches; "
          f"{len(sel)} mutants")
    return sel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="comma-separated mutant ids")
    ap.add_argument("--milestone", help="only mutants of this milestone (e.g. M3)")
    ap.add_argument("--tsv", help="write the results here")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--changed", metavar="REF", help="only the mutants that changes since REF can affect")
    ap.add_argument("--focused", action="store_true", help="focused runs (see above)")
    ap.add_argument("--jobs", type=int, default=1, help="with --focused: parallel scratch trees (see above)")
    a = ap.parse_args()
    if a.jobs < 1 or a.jobs > 1 and not a.focused:
        sys.exit("--jobs N: N >= 1, and more than one only with --focused")
    sel = [m for m in MUTANTS
           if (not a.only or m["id"] in a.only.split(",")) and (not a.milestone or m["milestone"] == a.milestone)]
    if a.changed:
        sel = [m for m in changed_mutants(a.changed, MUTANTS) if m in sel]
    if not sel:
        sys.exit("no mutants selected")
    ids = [m["id"] for m in MUTANTS]
    if len(ids) != len(set(ids)):
        sys.exit("duplicate mutant ids in tests/mutants.py")
    needs_x86 = any(m["file"].startswith("tools/x86recomp/") for m in sel)

    if a.focused:
        try:
            results = run_focused(sel, needs_x86, a.timeout, a.jobs)
        except Baseline as e:
            sys.exit(str(e))
    else:
        sync()
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
            t0 = time.time()
            status, detail = mutate_one(m, a.timeout)
            results.append((m, status, detail))
            report(m, status, detail, t0)
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
