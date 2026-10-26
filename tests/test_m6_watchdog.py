#!/usr/bin/env python3
"""M6 acceptance's watchdog rule (scripts/m6_watchdog.py) and the match
script's phase shots (scripts/m6_accept.sh), no game data:

  /opt/homebrew/bin/python3 -I tests/test_m6_watchdog.py

The rule is the user's approved policy (2026-10-26): the runtime watchdog
stays at 5 s; one map-loading frame of at most 10 s between Start Game and
the first frame of the match is allowed; menus and gameplay never; repeated
reports, crashes, phase shots missing or misplaced, loads over 10 s or
unverified fail. The log lines are copied in the runtime's formats from
real launches (m1air-loadwd-nodiag-1-20261026-181415, poc-ai-1-20261026-194535).
Prints a FAIL line per failing check.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m6_watchdog as mw  # noqa: E402

failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))
    failures += not ok


def shot(name, frame):
    return f"warning: shot: {name} (frame {frame})"


def fps(t, mx):
    return f"warning: fps: 128.04 at t={t:.1f} s (interval ms: min 0.205 p1 1.389 median 5.384 p99 19.433 max {mx})"


DOG = ("warning: watchdog: main thread has not pumped window events for 5.1 s; stacks of all guest "
       "threads written to /tmp/xdg/refrozen/hangs/hang-1793013342-43235.txt")
FATAL = "FATAL: SIGBUS: guest memory fault at guest 0000003C (not handled by the guest's exception handlers)"
MENUS = [shot("dota", 8027), fps(60.0, "1313.054"), shot("slots", 12728)]
START = shot("start", 12731)
LOADED = shot("loaded", 13502)
MATCH = [fps(120.0, "{}"), shot("match_start", 14120), shot("camera", 14800), fps(180.0, "160.114"), shot("m0000", 16000)]


def log(*parts, load_max="5697.856"):
    out = []
    for p in parts:
        out += [line.format(load_max) for line in p] if isinstance(p, list) else [p]
    return "\n".join(out) + "\n"


def judge(text):
    return mw.judge(text)[0]


def main():
    # The rule.
    check("no report: passes", judge(log(MENUS, START, LOADED, MATCH)), True)
    check("one report in the map load, frame 5698 ms: passes",
          judge(log(MENUS, START, DOG, LOADED, MATCH)), True)
    check("limit: a 10000 ms load frame passes", judge(log(MENUS, START, DOG, LOADED, MATCH, load_max="10000.000")), True)
    check("limit: a 10000.5 ms load frame fails",
          judge(log(MENUS, START, DOG, LOADED, MATCH, load_max="10000.500")), False)
    check("limit: a 15 s load frame fails", judge(log(MENUS, START, DOG, LOADED, MATCH, load_max="15012.004")), False)
    check("phase: a report in the lobby before Start Game fails",
          judge(log(MENUS[:2], DOG, MENUS[2:], START, LOADED, MATCH)), False)
    check("phase: a report between the slots shot and the start shot fails",
          judge(log(MENUS, DOG, START, LOADED, MATCH)), False)
    check("phase: a report after the loaded shot (key wait, match) fails",
          judge(log(MENUS, START, LOADED, DOG, MATCH)), False)
    check("phase: a report in the match fails", judge(log(MENUS, START, LOADED, MATCH[:3], DOG, MATCH[3:])), False)
    check("repeat: two reports in the map load fail", judge(log(MENUS, START, DOG, DOG, LOADED, MATCH)), False)
    check("repeat: one in the map load and one in the match fail",
          judge(log(MENUS, START, DOG, LOADED, MATCH[:3], DOG, MATCH[3:])), False)
    check("classification: no start shot fails", judge(log(MENUS, DOG, LOADED, MATCH)), False)
    check("classification: no loaded shot fails", judge(log(MENUS, START, DOG, MATCH)), False)
    check("classification: shots out of order fail", judge(log(MENUS, LOADED, DOG, START, MATCH)), False)
    check("classification: a start shot twice fails", judge(log(MENUS, START, START, DOG, LOADED, MATCH)), False)
    check("verification: no frame report after the report fails",
          judge(log(MENUS, START, DOG, LOADED, shot("match_start", 14120))), False)
    check("verification: the report after the watchdog decides, not the one before",
          judge(log(MENUS[:1], fps(60.0, "900.000"), MENUS[2:], START, DOG, LOADED, MATCH, load_max="12000.000")),
          False)
    check("crash: a FATAL never gets the exception", judge(log(MENUS, START, DOG, LOADED, MATCH, FATAL)), False)
    check("crash: a FATAL without a watchdog report is left to the FATAL rule",
          judge(log(MENUS, START, LOADED, MATCH, FATAL)), True)
    ok, note = mw.judge(log(MENUS, START, DOG, LOADED, MATCH))
    check("note: says the load frame was allowed and its length", note,
          "one map-load frame of 5698 ms (allowed up to 10000 ms)")

    # The match script: "start" is the frame after the Start Game click, and
    # "loaded" comes before the first key of the match (Space).
    src = open(os.path.join(ROOT, "scripts", "m6_accept.sh")).read()
    gen = src[src.index("<<'EOF'\nimport sys\nm0") + len("<<'EOF'\n"):]
    gen = gen[:gen.index("\nEOF\n")]
    out = subprocess.run([sys.executable, "-I", "-", "112", "172"], input=gen, capture_output=True,
                         text=True).stdout.splitlines()
    timed = [(float(line.split()[0]), " ".join(line.split()[1:])) for line in out]
    cmds = [c for _, c in timed]
    click = cmds.index("goto 688 492") + 1
    check("match script: the Start Game click is followed by the start shot, at the same time",
          (cmds[click], cmds[click + 1], timed[click][0] == timed[click + 1][0]), ("click", "shot start", True))
    check("match script: one start shot and one loaded shot", (cmds.count("shot start"), cmds.count("shot loaded")),
          (1, 1))
    check("match script: the loaded shot comes before the first key of the match",
          cmds.index("shot loaded") < cmds.index("key Space"), True)
    check("acceptance: the watchdog verdict comes from m6_watchdog.py",
          "scripts/m6_watchdog.py" in src and '[ "$watchdog" != 0 ]' not in src, True)

    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
