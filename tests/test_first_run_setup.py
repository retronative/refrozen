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
        data = os.path.join(tmp, "Application Support")  # a space, as in the real default data folder
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
        dl = os.path.join(data, "game", "Maps", "Download")
        rc, out = setup("add-map", MAP)
        check("map: the same map again is already installed, not copied twice",
              rc == 0 and "already installed" in out and len(os.listdir(dl)) == 1, out)
        other = os.path.join(tmp, "other", os.path.basename(MAP))
        os.makedirs(os.path.dirname(other))
        open(other, "wb").write(open(MAP, "rb").read() + b"\0")  # a different map, same name
        rc, out = setup("add-map", other)
        kept = open(os.path.join(dl, os.path.basename(MAP)), "rb").read() == open(MAP, "rb").read()
        stem, ext = os.path.splitext(os.path.basename(MAP))
        check("map: a different map with the same name is added as (2), the installed one kept",
              rc == 0 and kept and os.path.exists(os.path.join(dl, f"{stem} (2){ext}")), out)
        check("map: no partial import file is left", not [n for n in os.listdir(dl) if n.startswith(".importing-")])
        for name, content, why in (("notes.w3x", b"not a map", "no map header"), ("map.txt", b"HM3W....", "extension"),
                                   ("big.w3x", b"HM3W" + b"\0" * (9 << 20), "over 8 MB")):
            p = os.path.join(tmp, name)
            open(p, "wb").write(content)
            check(f"map: refused, {why}", setup("add-map", p)[0] == 1)

        # One overall progress (SetupProgress, through replay-progress, with timed lines): Install,
        # Compile and Finish follow completed work; the Lift shows estimated progress from 3 % toward
        # 19 % at a fifth of the measured Lift's speed, 20 % only when it is done.
        def replay(timed, *args):
            text = "\n".join(f"{t} {l}" for t, l in timed) + "\n"
            out = subprocess.run([binary, "--setup", "replay-progress", *args], input=text, capture_output=True,
                                 text=True, env=setup.env()).stdout.splitlines()
            return [(float(l.split()[0]), l.split()[1], l.split()[2] == "1", " ".join(l.split()[3:])) for l in out]

        lift = [(10, "reFrozen game module 1234-abcd: 8 jobs")] + [(10 + i, f"prepared m{i} ({i}/11)") for i in range(1, 12)] \
            + [(22, "lifting the game code"), (70, "?"), (310, "?"), (1000, "?")]
        rest = [(1001, "compiling 244 files")] + [(1002 + i, f"compiled gen_{i:03d}.cpp") for i in range(244)] \
            + [(1250, "linking"), (1251, "signing"), (1252, "installing the module"), (1253, "built: /x/war3.dylib")]
        install = [(1, "install RoC: {'file': 77}"), (4, "install TFT: {'file': 194}"), (8, "patch 1.26a: {'disk': 147}")]
        seq = install + lift + rest + [(1254, "#verified")]
        r = replay(seq, "estimate=60")
        at = {t: x for (t, l), x in zip(seq, r) if l == "?"}
        check("progress: one Lift estimate (60 s) in, the bar shows 6.2 %", abs(at[70][0] - 0.062) < 0.0005, at[70])
        check("progress: at five times the estimate the Lift's estimate reaches 19 %", abs(at[310][0] - 0.19) < 0.0005,
              at[310])
        check("progress: a long Lift holds at 19 % with the shimmer", at[1000][0] == 0.19 and at[1000][2], at[1000])
        lift_values = [x[0] for (t, l), x in zip(seq, r) if x[1] == "lift"]
        check("progress: never 20 % before the Lift completes", max(lift_values) <= 0.19, max(lift_values))
        done_lift = seq.index((1001, "compiling 244 files"))
        check("progress: 20 % when the Lift completes", r[done_lift][0] == 0.20, r[done_lift])
        check("progress: the Lift says Recompiling game code", r[seq.index((22, "lifting the game code"))][3]
              == "Recompiling game code…")
        fr = [x[0] for x in r]
        check("progress: one bar that never moves back across install, lift, compile and finish",
              all(b >= a for a, b in zip(fr, fr[1:])), fr[:20])
        order = ["install", "lift", "compile", "finish", "done"]
        stages = [order.index(x[1]) for x in r]
        check("progress: the stages only move forward", all(b >= a for a, b in zip(stages, stages[1:])))
        check("progress: the install follows its completed products", [round(x[0], 4) for x in r[:3]] == [0.01, 0.02, 0.03],
              r[:3])
        mid = seq.index((1002 + 121, "compiled gen_121.cpp"))
        check("progress: halfway through compiling is halfway through the compile stage",
              abs(r[mid][0] - (0.20 + 0.78 * 122 / 244)) < 0.002, r[mid])
        check("progress: the status names the stage and the count", "122 of 244" in r[mid][3], r[mid][3])
        check("progress: never 100 % before the module is verified", max(fr[:-1]) < 1.0, max(fr[:-1]))
        check("progress: 100 % once verified", r[-1][0] == 1.0 and r[-1][1] == "done")
        rb = replay([(0, "?")] + [(t - 10, l) for t, l in lift[:1]], "build", "estimate=60")
        check("progress: a build after an install starts where the install ended", rb[0][0] == 0.03, rb)
        stop = replay(lift[:13] + [(40, "#stop"), (200, "?")], "build", "estimate=60")
        check("progress: a cancel freezes the bar where it stood, without the shimmer",
              stop[-1][0] == stop[-2][0] and not stop[-1][2], stop[-2:])
        retry = replay([(0, "?"), (1, "reFrozen game module 1234-abcd: 8 jobs"), (30, "?"), (2000, "?")],
                       "build", "estimate=60", f"floor={stop[-1][0]}")
        check("progress: a retry starts where the stopped attempt stood and never shows less",
              all(x[0] >= stop[-1][0] for x in retry) and retry[1][2], retry)
        odd = replay(install + lift[:12] + rest[:30] + [(1100, "prepared m1 (1/11)"), (1101, "compiling 244 files"),
                                                        (1102, "warning: x"), (1103, "build failed: y")], "estimate=60")
        of = [x[0] for x in odd]
        check("progress: stray, repeated or unknown lines never move it back",
              all(b >= a for a, b in zip(of, of[1:])), of[-6:])

        # The progress light (FrostSweep, through sweep): it sweeps from the bar's start to the fill
        # edge and never shows past it; none on a fill too short; constant speed, so a longer fill
        # takes longer. The Show/Hide Details control (through details): words and what VoiceOver says.
        def sweep(fill):
            out = subprocess.run([binary, "--setup", "sweep", str(fill)], capture_output=True, text=True,
                                 env=setup.env()).stdout.splitlines()
            return [tuple(float(x) for x in l.split()[1:]) if l.split()[1] != "-" else None for l in out]
        for fill in (24, 100, 480, 900):
            s = sweep(fill)
            shown = [x for x in s if x]
            check(f"sweep: never past the fill and never before the start ({fill} pt)",
                  shown and all(0 <= a < b <= fill for _, a, b in shown), shown[:3])
            check(f"sweep: runs from the start to the fill edge ({fill} pt)",
                  min(a for _, a, _ in shown) == 0 and max(b for _, _, b in shown) >= fill - 4,
                  (min(a for _, a, _ in shown), max(b for _, _, b in shown)))
            leads = [x[0] for x in shown]
            check(f"sweep: one steady pass, start to end ({fill} pt)", all(b >= a for a, b in zip(leads, leads[1:])))
        check("sweep: none on a fill too short to show it", all(x is None for x in sweep(10)))
        check("sweep: constant speed, so a longer fill takes longer", len(sweep(900)) > len(sweep(480)) > len(sweep(100)),
              (len(sweep(100)), len(sweep(480)), len(sweep(900))))
        det = dict(l.split(" ", 1) for l in subprocess.run([binary, "--setup", "details"], capture_output=True,
                                                            text=True, env=setup.env()).stdout.splitlines())
        check("details: collapsed says Show Details, and VoiceOver hears Details, collapsed",
              det.get("0") == "Show Details|Details|collapsed", det)
        check("details: expanded says Hide Details, and VoiceOver hears Details, expanded",
              det.get("1") == "Hide Details|Details|expanded", det)

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
