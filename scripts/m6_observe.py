#!/usr/bin/env python3
"""M6 observation: keeps the view on the match without playing it.

  /opt/homebrew/bin/python3 -I scripts/m6_observe.py <run dir> <follow file> <game pid>

Run by scripts/m6_accept.sh beside the game. The camera is put on the map's
centre once by the match script (a plain minimap click; the player's hero
stays at the fountain and is never ordered). This watches <run dir>/shots
for the periodic shots (m<NNNN>.bmp) and its own verification shots
(v<NNNN>.bmp) as they are saved, reads each with macOS's Vision OCR
(build/oracle_keys/ocr_text) and acts only on what it detects, by appending
TEST_INPUT lines to the follow file (<ID>_TEST_INPUT_FOLLOW, "+<s>" times):

  - A multiboard expanded: DotA's scoreboard over the screen (its row labels
    in the OCR: "Hero K/D/A", "Current Gold", ...) or the AI map's board at
    the top right (its team rows: "The Sentinel" and "The Scourge" as lines
    of their own). Only the board shown has the toggle: one click on it,
    then a verification shot. Collapsed: done; still expanded: one retry,
    then no more clicks until a periodic shot shows it collapsed (never a
    blind toggle). A board that opens again later is counted and collapsed
    again the same way.
  - The camera moved off the observation view (the minimap's white camera
    box more than CAMERA_TOLERANCE points from where it was after the
    centring click): one minimap click on the centre, then a verification
    shot.

In a match the game's cursor follows relative motion only (TEST_INPUT's
"pointer" does not move it), and "goto" homes it through the top-left
corner, which scrolls the camera. So the match script homes it once (goto
to the minimap's centre, then the centring click, which sets the camera
anyway) and this tracks where it is and moves it with relative "move"
steps that never touch a screen edge. Every action
and verification goes to <run dir>/observe.log; OCR text to ocr.txt
("<shot>: <line>"). Periodic and verification BMPs are kept as 400-point
JPEGs once read (disk); named shots stay BMPs. Exits when the game does.
"""
import os
import re
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR = os.path.join(ROOT, "build", "oracle_keys", "ocr_text")

# 800x600 HUD: the minimap's map area and its centre (the observation view),
# the scoreboard's minimize toggle (top right of the board).
MINIMAP = (10, 454, 150, 593)  # x0, y0, x1, y1 inclusive
CENTRE = (80, 524)
BOARD_TOGGLE = (787, 35)
CAMERA_TOLERANCE = 6
STEP = 200  # largest relative motion per event (TEST_INPUT's goto uses the same)
# Row labels only the expanded board shows (OCR may read "Gold" as "Cold").
BOARD_ROWS = re.compile(r"Hero K/?D/?A|Current [GC]old|Creep Stats|Tower Stats|Bonus [GC]old")


def board_expanded(lines):
    """OCR lines of a frame -> True iff a multiboard is shown expanded."""
    if sum(1 for line in lines if BOARD_ROWS.search(line)) >= 2:
        return True
    return {"The Sentinel", "The Scourge"} <= {line.strip() for line in lines}


def read_bmp(path):
    """(width, height, pixel(x, y) -> (r, g, b)) of an uncompressed 24/32-bit BMP."""
    d = open(path, "rb").read()
    off, = struct.unpack_from("<I", d, 10)
    w, h = struct.unpack_from("<ii", d, 18)
    bp = struct.unpack_from("<H", d, 28)[0] // 8
    stride = (w * bp + 3) & ~3

    def px(x, y):
        i = off + ((abs(h) - 1 - y) if h > 0 else y) * stride + x * bp
        return d[i + 2], d[i + 1], d[i]
    return w, abs(h), px


# The camera box's outline on the minimap (measured: about 17 x 11 points).
BOX_W, BOX_H = (10, 30), (6, 20)


def camera_box(path):
    """Centre (x, y) of the minimap's white camera box, or None if not found.
    Other white marks (pings, icons) are separate components of another
    size: the box is the largest 8-connected white component whose bounds
    are a camera box's."""
    w, h, px = read_bmp(path)
    if (w, h) != (800, 600):
        return None
    x0, y0, x1, y1 = MINIMAP
    white = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
             if min(px(x, y)) > 225}
    best = None
    while white:
        stack = [white.pop()]
        comp = []
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for n in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if n in white:
                    white.remove(n)
                    stack.append(n)
        xs, ys = [p[0] for p in comp], [p[1] for p in comp]
        bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if BOX_W[0] <= bw <= BOX_W[1] and BOX_H[0] <= bh <= BOX_H[1] and (not best or len(comp) > best[0]):
            best = (len(comp), ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    return best[1] if best else None


def move_and_click(src, dst):
    """Relative motion from src to dst in steps of at most STEP points,
    0.1 s apart (one per game frame), then a click; -> (lines, end time)."""
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    n = max(1, -(-max(abs(dx), abs(dy)) // STEP))
    lines, t, done = [], 0.1, (0, 0)
    for k in range(1, n + 1):
        to = (round(dx * k / n), round(dy * k / n))
        lines.append(f"+{t:.1f} move {to[0] - done[0]} {to[1] - done[1]}")
        done, t = to, t + 0.1
    lines.append(f"+{t + 0.1:.1f} click")
    return lines, t + 0.1


class Observer:
    """Decides, from each shot, what input (if any) to append. Pure: no I/O."""

    def __init__(self):
        self.cursor = CENTRE  # where the match script's goto left it
        self.camera_ref = None  # camera box centre after the centring click
        self.pending = None  # ("board" | "camera", tries) awaiting a v-shot
        self.collapses = 0
        self.reopens = 0
        self.board_was_collapsed = False
        self.blocked = False  # a collapse failed twice: wait for a collapsed frame
        self.next_v = 0

    def _act(self, kind, tries, target):
        """Cursor to target, click, then a verification shot."""
        lines, end = move_and_click(self.cursor, target)
        self.cursor = target
        name = f"v{self.next_v:04d}"
        self.next_v += 1
        self.pending = (kind, tries)
        return lines + [f"+{end + 1.4:.1f} shot {name}"]

    def shot(self, name, ocr_lines, camera):
        """-> (input lines to append, log messages)."""
        log = []
        expanded = board_expanded(ocr_lines)
        if self.pending:
            kind, tries = self.pending
            if not name.startswith("v"):
                return [], log  # the verification shot comes first
            self.pending = None
            if kind == "board":
                if not expanded:
                    self.collapses += 1
                    self.board_was_collapsed = True
                    log.append(f"{name}: scoreboard collapsed (verified)")
                elif tries < 2:
                    log.append(f"{name}: scoreboard still expanded; retry")
                    return self._act("board", tries + 1, BOARD_TOGGLE), log
                else:
                    self.blocked = True
                    log.append(f"{name}: scoreboard still expanded after 2 clicks; no more clicks until a "
                               "collapsed frame")
            else:
                if camera and self.camera_ref and _dist(camera, self.camera_ref) <= CAMERA_TOLERANCE:
                    log.append(f"{name}: camera back on the observation view (verified)")
                else:
                    log.append(f"{name}: camera not back on the view ({camera}); next periodic shot decides")
            return [], log
        if name.startswith("v"):
            return [], log
        if self.camera_ref is None and camera:
            self.camera_ref = camera
            log.append(f"{name}: camera reference {camera}")
        if not expanded:
            if self.blocked:
                self.blocked = False
                log.append(f"{name}: scoreboard collapsed again; clicks re-enabled")
            self.board_was_collapsed = True
        elif not self.blocked:
            if self.board_was_collapsed and self.collapses:
                self.reopens += 1
                log.append(f"{name}: scoreboard reopened (reopen {self.reopens})")
            log.append(f"{name}: scoreboard expanded; collapsing")
            return self._act("board", 1, BOARD_TOGGLE), log
        if camera and self.camera_ref and _dist(camera, self.camera_ref) > CAMERA_TOLERANCE:
            log.append(f"{name}: camera moved to {camera} (reference {self.camera_ref}); recentring")
            return self._act("camera", 1, CENTRE), log
        return [], log


def _dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main():
    run, follow, pid = sys.argv[1], sys.argv[2], int(sys.argv[3])
    shots = os.path.join(run, "shots")
    obs = Observer()
    seen = set()
    with open(os.path.join(run, "observe.log"), "a") as logf, open(os.path.join(run, "ocr.txt"), "a") as ocrf:
        def alive():
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
        while True:
            running = alive()
            new = sorted(f for f in os.listdir(shots) if re.fullmatch(r"[mv]\d{4}\.bmp", f) and f not in seen)
            for f in new:
                path = os.path.join(shots, f)
                if running and time.time() - os.path.getmtime(path) < 1.0:
                    continue  # still being written
                seen.add(f)
                name = f[:-4]
                lines = subprocess.run([OCR, path], capture_output=True, text=True).stdout.splitlines()
                ocrf.writelines(f"{name}: {line}\n" for line in lines)
                ocrf.flush()
                cam = camera_box(path)
                add, msgs = obs.shot(name, lines, cam)
                for m in msgs:
                    logf.write(f"{time.strftime('%H:%M:%S')} {m}\n")
                logf.flush()
                if add:
                    with open(follow, "a") as ff:
                        ff.write("".join(line + "\n" for line in add))
                subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "400", path, "--out", path[:-4] + ".jpg"],
                               capture_output=True)
                if os.path.exists(path[:-4] + ".jpg"):
                    os.remove(path)
            if not running and not new:
                break
            time.sleep(0.5)
        logf.write(f"{time.strftime('%H:%M:%S')} summary: collapses {obs.collapses}, reopens {obs.reopens}\n")


if __name__ == "__main__":
    main()
