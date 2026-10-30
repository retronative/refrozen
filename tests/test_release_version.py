#!/usr/bin/env python3
"""The release version is one setting, VERSION, used by the release pipeline:

  /opt/homebrew/bin/python3 -I tests/test_release_version.py

- VERSION holds a version x.y.z;
- no release script names a version itself (the app's Info.plist, the dmg's
  name, the manifest, the release check);
- check_release.py accepts an Info.plist with VERSION's version and refuses
  another (run on a minimal bundle; only its version check is read);
- check_release.py refuses a kit missing a source its builder compiles, and
  accepts one that has them all (minimal bundles; only that check is read).
Prints a FAIL line per failing check.
"""
import os
import plistlib
import re
import subprocess
import sys
import tempfile

ROOT = os.environ.get("REFROZEN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.environ.get("REFROZEN_SCRIPTS", os.path.join(ROOT, "scripts"))
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


def release_line(app, what):
    r = subprocess.run(["/usr/bin/python3", "-I", os.path.join(SCRIPTS, "release", "check_release.py"), app],
                       capture_output=True, text=True)
    return next((l for l in r.stdout.splitlines() if what in l), r.stdout[-300:] + r.stderr[-300:])


def version_line(app):
    return release_line(app, "Info.plist: version")


def main():
    version = open(os.path.join(ROOT, "VERSION")).read().strip()
    check("VERSION: a version x.y.z", bool(re.fullmatch(r"\d+\.\d+\.\d+", version)), True)
    literal = re.compile(r"CFBundleShortVersionString</key><string>\d|reFrozen-\d+\.\d+\.\d+\.dmg|"
                         r"reFrozen \d+\.\d+\.\d+ release|== \"\d+\.\d+\.\d+\"")
    for rel in ("release/make_release_app.sh", "release/release_candidate.sh", "release/check_release.py",
                "poc/make_setup_app.sh"):
        text = open(os.path.join(SCRIPTS, rel)).read()
        check(f"{rel}: names no version itself", literal.findall(text), [])
    with tempfile.TemporaryDirectory() as tmp:
        for name, v, want in (("the version in VERSION", version, "ok  "), ("another version", "0.0.9", "FAIL")):
            app = os.path.join(tmp, name.replace(" ", "-"), "reFrozen.app")
            os.makedirs(os.path.join(app, "Contents"))
            with open(os.path.join(app, "Contents", "Info.plist"), "wb") as f:
                plistlib.dump({"CFBundleShortVersionString": v}, f)
            check(f"check_release: an Info.plist with {name}", version_line(app)[:4], want)
        for name, present, want in (("every source", ("a.cpp", "b.cpp"), "ok  "), ("a source missing", ("a.cpp",), "FAIL")):
            kit = os.path.join(tmp, name.replace(" ", "-"), "reFrozen.app", "Contents", "Resources", "kit")
            os.makedirs(os.path.join(kit, "scripts")); os.makedirs(os.path.join(kit, "src"))
            with open(os.path.join(kit, "scripts", "build_module.sh"), "w") as f:
                f.write('printf \'%s\\0\' "$TMP"/generated/*.cpp "$KIT/src/a.cpp" "$KIT/src/b.cpp" | xargs -0 -P 4 cc\n')
            for s in present:
                open(os.path.join(kit, "src", s), "w").close()
            line = release_line(os.path.dirname(os.path.dirname(os.path.dirname(kit))), "the kit has every source")
            check(f"check_release: a kit with {name} its builder compiles", line[:4], want)
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
