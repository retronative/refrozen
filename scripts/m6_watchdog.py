#!/usr/bin/env python3
"""M6 acceptance: the watchdog rule and its one exception, the map load.

  /opt/homebrew/bin/python3 -I scripts/m6_watchdog.py <launch log>   # "ok|<note>" or "fail|<reason>"

The runtime's watchdog stays at 5 s everywhere; this only decides whether a
launch's reports fail it (RELEASE_PLAN, approved 2026-10-26). It passes with
no watchdog report, or with exactly one during the map load when that frame
is verified at most 10 s:
  - the map load: between the "start" shot (the frame after Start Game is
    clicked) and the "loaded" shot (the loading screen waiting for a key,
    before the first frame of the match), each in the log exactly once and
    in that order;
  - verified: the first frame-interval report after the watchdog report
    (REFROZEN_FPS_REPORT; its window holds that frame) has a longest
    interval of at most 10 000 ms;
  - no FATAL in the log.
Anything else fails: a report in the menus or the match, a second report
(another hang, or the watchdog's repeated dump of the same one), phase shots
missing or out of order, a load frame over 10 s or not verified, a crash.
"""
import re
import sys

LOAD_LIMIT_MS = 10000.0


def judge(text):
    lines = text.splitlines()
    reports = [i for i, line in enumerate(lines) if "watchdog" in line]
    if not reports:
        return True, "no watchdog report"
    if any("FATAL" in line for line in lines):
        return False, "a crash: the loading exception does not apply"
    if len(reports) > 1:
        return False, f"{len(reports)} watchdog reports"

    def shot(name):
        found = [i for i, line in enumerate(lines) if re.search(rf"\bshot: {name} \(frame \d+\)", line)]
        return found[0] if len(found) == 1 else None

    start, loaded = shot("start"), shot("loaded")
    if start is None or loaded is None:
        return False, "the map load is not identified (its start and loaded shots)"
    if not start < reports[0] < loaded:
        return False, "a watchdog report outside the map load (menus or match)"
    for line in lines[reports[0] + 1:]:
        m = re.search(r"fps: .*\bmax ([\d.]+)\)", line)
        if m:
            ms = float(m.group(1))
            if ms > LOAD_LIMIT_MS:
                return False, f"map-load frame {ms:.0f} ms, over {LOAD_LIMIT_MS:.0f} ms"
            return True, f"one map-load frame of {ms:.0f} ms (allowed up to {LOAD_LIMIT_MS:.0f} ms)"
    return False, "the map-load frame is not verified (no frame report after the watchdog report)"


def main():
    ok, note = judge(open(sys.argv[1], errors="replace").read())
    print(f"{'ok' if ok else 'fail'}|{note}")


if __name__ == "__main__":
    main()
