#!/usr/bin/env python3
"""reFrozen's first-run setup (app/setup), through its command-line mode:

  /opt/homebrew/bin/python3 -I tests/test_first_run_setup.py

Compiles this tree's app/setup with Apple's Swift compiler, then checks:
CD-key and owner rules (scripts/native_install.py's own: 26 characters of
its alphabet; 1-62 Windows-1252 bytes); input verification (the right
installers, swapped installers, a folder for the patch, a folder without a
tome, a fake tome of the real size that only the hash catches); the status
transitions (no install, an install without its marker, no module, a module
from another build, ready); the map checks (header, extension, the 8 MB
limit); and the install: bad keys refused before anything is written, a
cancelled install leaving no game and no temporary folder, and a full install
byte-identical to a reference install, with no key in its output or logs.

Needs, from the real tree (REFROZEN_ROOT): a kit (build/poc-kit), the player's
installers (REFROZEN_DOTA, default ../DOTA: ICC Game client install/) and a reference install
(game/native-install). The keys and owner name come from the reference's own
key files and are never printed. About a minute. Prints a FAIL line per
failing check.
"""
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.environ.get("REFROZEN_ROOT", ROOT)
KIT = os.environ.get("REFROZEN_POC_KIT", os.path.join(REAL, "build", "poc-kit"))
REF = os.path.join(REAL, "game", "native-install")
DOTA = os.environ.get("REFROZEN_DOTA", os.path.join(os.path.dirname(REAL), "DOTA"))
SRC = os.path.join(DOTA, "ICC Game client install")
ROC = os.path.join(SRC, "Warcraft III 1.21b ROC Installer enGB")
TFT = os.path.join(SRC, "Warcraft III 1.21b TFT Installer enGB")
PATCH = os.path.join(SRC, "War3TFT_126a_English.exe")
MAP = os.path.join(DOTA, "DotA v6.83dAI PMV 1.42 EN.w3x")
sys.path.insert(0, os.path.join(REAL, "scripts"))

failures = 0


def check(name, ok, detail=""):
    global failures
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f" ({detail})"))
    failures += not ok


class Setup:
    def __init__(self, binary, data):
        self.binary, self.data = binary, data

    def env(self):
        return dict(os.environ, REFROZEN_KIT=KIT, REFROZEN_DATA=self.data)

    def __call__(self, *args, stdin=None):
        r = subprocess.run([self.binary, "--setup", *args], input=stdin, capture_output=True, text=True,
                           env=self.env(), timeout=600)
        return r.returncode, (r.stdout + r.stderr).strip()


def secrets():
    """The reference install's RoC key, TFT key and owner, from its key files."""
    import font_keydata as fk
    import native_install as ni

    def read(mpq, name):
        return fk.decode(ni.Mpq(os.path.join(REF, mpq)).read(name)).rstrip(b"\0").decode("latin-1")

    return read("war3.mpq", "font\\font.gid"), read("War3x.mpq", "font\\font.exp"), read("war3.mpq", "font\\font.clh")


def tree(root):
    return {os.path.relpath(os.path.join(d, f), root): hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest()
            for d, _, files in os.walk(root) for f in files}


def main():
    for path in (KIT, ROC, TFT, PATCH, REF, MAP):
        if not os.path.exists(path):
            print(f"FAIL prerequisite missing: {path}")
            return 1
    with tempfile.TemporaryDirectory() as tmp:
        binary = os.path.join(tmp, "reFrozen")
        sources = sorted(os.path.join(ROOT, "app", "setup", f) for f in os.listdir(os.path.join(ROOT, "app", "setup"))
                         if f.endswith(".swift"))
        cc = subprocess.run(["/usr/bin/xcrun", "swiftc", "-O", "-swift-version", "5", "-target", "arm64-apple-macos14.0",
                             "-parse-as-library", "-module-name", "reFrozenSetup", *sources, "-o", binary],
                            capture_output=True, text=True)
        if cc.returncode:
            print("FAIL the setup compiles\n" + cc.stderr[-3000:])
            return 1
        data = os.path.join(tmp, "data")
        setup = Setup(binary, data)

        # CD keys (stdin) and the owner's name.
        for key, want, why in (("246789BCDEFGHJKMNPRTVWXYZ2", 0, "26 characters of the alphabet"),
                               ("2467-89BC DEFG-HJKM NPRT-VWXY-Z2", 0, "dashes and spaces ignored"),
                               ("246789bcdefghjkmnprtvwxyz2", 0, "lower case accepted"),
                               ("246789BCDEFGHJKMNPRTVWXYZ", 1, "25 characters"),
                               ("A46789BCDEFGHJKMNPRTVWXYZ2", 1, "A is not in the key alphabet"),
                               ("046789BCDEFGHJKMNPRTVWXYZ2", 1, "0 is not in the key alphabet")):
            rc, out = setup("key", stdin=key + "\n")
            check(f"key: {why}", rc == want and (key not in out), out)
        for name, want, why in (("Player", 0, "a plain name"), ("Zoë", 0, "Windows-1252 accented letters"),
                                ("x" * 62, 0, "62 characters"), ("x" * 63, 1, "63 characters"), ("", 1, "empty"),
                                ("名前", 1, "outside Windows-1252")):
            check(f"owner: {why}", setup("owner", name)[0] == want)

        # Input verification.
        rc, out = setup("verify", "roc", ROC)
        check("verify: the Reign of Chaos installer", rc == 0 and "Reign of Chaos 1.21b" in out, out)
        rc, out = setup("verify", "tft", TFT)
        check("verify: the Frozen Throne installer", rc == 0 and "Frozen Throne 1.21b" in out, out)
        rc, out = setup("verify", "patch", PATCH)
        check("verify: the 1.26a patch", rc == 0 and "1.26a" in out, out)
        rc, out = setup("verify", "roc", TFT)
        check("verify: swapped installers are named", rc == 1 and "this is Warcraft III: The Frozen Throne" in out, out)
        rc, out = setup("verify", "patch", ROC)
        check("verify: a folder for the patch is refused", rc == 1 and "patch file itself" in out, out)
        empty = os.path.join(tmp, "empty")
        os.mkdir(empty)
        rc, out = setup("verify", "roc", empty)
        check("verify: a folder without a tome is refused", rc == 1 and "no Installer Tome.mpq" in out, out)
        fake = os.path.join(tmp, "fake")
        os.mkdir(fake)
        with open(os.path.join(fake, "Installer Tome.mpq"), "wb") as f:
            f.truncate(os.path.getsize(os.path.join(ROC, "Installer Tome.mpq")))  # same size, other content
        rc, out = setup("verify", "roc", fake)
        check("verify: a tome of the right size but other content is refused", rc == 1 and "not Warcraft III" in out,
              out)

        # Status.
        def status():
            return setup("status")[1]

        check("status: nothing installed", status() == "needs-install")
        os.makedirs(os.path.join(data, "game"))
        check("status: a game folder without the install marker", status() == "needs-install")
        open(os.path.join(data, "game", "reFrozen-install.json"), "w").write("{}")
        check("status: installed, no module", status() == "needs-build")
        current = os.path.join(data, "build", "current")
        os.makedirs(current)
        open(os.path.join(current, "war3.dylib"), "w").write("")
        open(os.path.join(current, "stamp.txt"), "w").write("0000-other\n")
        check("status: a module from another build", status() == "needs-build")
        open(os.path.join(current, "stamp.txt"), "w").write(open(os.path.join(KIT, "stamp.txt")).read())
        check("status: a module of this build", status() == "ready")

        # Maps.
        rc, out = setup("add-map", MAP)
        check("map: a Warcraft III map is added", rc == 0 and os.path.exists(
            os.path.join(data, "game", "Maps", "Download", os.path.basename(MAP))), out)
        for name, content, why in (("notes.w3x", b"not a map", "no map header"), ("map.txt", b"HM3W....", "extension"),
                                   ("big.w3x", b"HM3W" + b"\0" * (9 << 20), "over 8 MB")):
            p = os.path.join(tmp, name)
            open(p, "wb").write(content)
            check(f"map: refused, {why}", setup("add-map", p)[0] == 1)

        # Install: refused before anything is written, cancelled, then complete.
        import shutil
        shutil.rmtree(data)
        roc, tft, owner = secrets()
        rc, out = setup("install", ROC, TFT, PATCH, owner, stdin="NOTAKEY\n" + tft + "\n")
        check("install: a bad key is refused before anything is written",
              rc == 1 and "CD keys" in out and not os.path.exists(os.path.join(data, "game")), out)
        rc, out = setup("install", TFT, ROC, PATCH, owner, stdin=f"{roc}\n{tft}\n")
        check("install: swapped installers are refused", rc == 1 and not os.path.exists(os.path.join(data, "game")))
        p = subprocess.Popen([binary, "--setup", "install", ROC, TFT, PATCH, owner], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=setup.env())
        p.stdin.write(f"{roc}\n{tft}\n")
        p.stdin.close()
        def listing():
            return os.listdir(data) if os.path.isdir(data) else []

        deadline = time.time() + 60
        while time.time() < deadline and not any(n.startswith(".installing-") for n in listing()):
            time.sleep(0.1)
        time.sleep(0.5)  # the installer is writing (it takes about 10 s)
        p.send_signal(signal.SIGTERM)
        sent = time.time()
        out = p.stdout.read()
        p.wait(timeout=120)
        check("install: a cancel stops the installer at once (setup exits within 3 s)", time.time() - sent < 3,
              f"{time.time() - sent:.1f} s")
        left = [n for n in listing() if n.startswith(".installing-") or n == "game"]
        check("install: cancelled, nothing installed and no temporary folder",
              p.returncode == 1 and "cancelled" in out and not left, f"rc {p.returncode}, left {left}")
        rc, out = setup("install", ROC, TFT, PATCH, owner, stdin=f"{roc}\n{tft}\n")
        logs = os.path.join(data, "logs")
        logged = "".join(open(os.path.join(logs, f), errors="replace").read() for f in os.listdir(logs))
        check("install: no CD key in the output or the setup logs",
              not any(s in out or s in logged for s in (roc, tft)))
        check("install: completes", rc == 0, out[-300:].replace(owner, "<owner>"))
        if rc == 0:
            got = tree(os.path.join(data, "game"))
            check("install: writes its marker", got.pop("reFrozen-install.json", None) is not None)
            want = tree(REF)
            diff = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
            check(f"install: byte-identical to the reference install ({len(want)} files)", not diff, diff[:5])
            check("status: installed by the setup, no module", status() == "needs-build")

    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
