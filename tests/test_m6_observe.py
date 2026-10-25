#!/usr/bin/env python3
"""M6 observation tooling (scripts/m6_observe.py), no game data:

  /opt/homebrew/bin/python3 -I tests/test_m6_observe.py

Expected values come from the game's own frames, not from the code:
  - the scoreboard's row labels as Vision OCR read them from an expanded
    board (run m6-accept-1-20261025-123841, shot m0126: "Current Cold",
    "Hero K/D/A", "Bonus Cold", "Creep Stats", "Tower Stats") and from a
    collapsed one (m0125: menu buttons, a tower message, the hero panel);
  - the board's minimize toggle at (787, 35) and the minimap's map area
    x 10-150, y 454-593 (centre (80, 524)), measured on 800x600 frames
    (M5's run m5-accept-1-20261025-054311 won.bmp; M6 probe match_start.bmp);
  - camera boxes drawn into synthetic 800x600 BMPs at known positions.
The observer's decisions (when to click, verify, retry, stop, recentre) are
checked as a sequence of shots. Prints a FAIL line per failing check.
"""
import os
import struct
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m6_observe as mo  # noqa: E402

failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))
    failures += not ok


EXPANDED = ["NFS]", "Menu (F1C]", "Lcg (F12)", "test", "Items", "Current Cold", "Hero K/D/A", "6036",
            "Bonus Cold", "Bonus XP", "Tower Stats", "Creep Stats"]
COLLAPSED = ["IFSI", "Menu (F1C]", "Leg (F12)", "Enemy: 38 | 20 |01", "vé.83d Al 1.4",
             "Na Vi.SoNNelkO has destroyed a tower.", "Inventar y", "701 / 701", "Barathrum"]
VICTORY = COLLAPSED + ["The Sentinel has won!"]
# The AI map's board expanded (probe m6-probe-cam-1-20261025-143721, m0005).
AI_BOARD = ["(FS]", "Menu (F1C]", "Leg (F12]", "881", "v6.83d AI 1.4", "The Sentinel", "F test", "Javilionaire",
            "The Scourge", "F M.ilLogic", "(0/0/0 - 0/0 - 0", "CD L", "KDAG"]


def bmp(path, box=None, size=(800, 600), blobs=()):
    """A dark 24-bit BMP; box = (x0, y0, x1, y1): a white 1-px outline;
    blobs: white filled squares (x, y, side), as pings and icons."""
    w, h = size
    stride = (w * 3 + 3) & ~3
    rows = bytearray(stride * h)
    for y in range(h):
        for x in range(w):
            i = (h - 1 - y) * stride + x * 3
            rows[i:i + 3] = bytes((20, 40, 20))
    if box:
        x0, y0, x1, y1 = box
        for x in range(x0, x1 + 1):
            for y in (y0, y1):
                i = (h - 1 - y) * stride + x * 3
                rows[i:i + 3] = b"\xff\xff\xff"
        for y in range(y0, y1 + 1):
            for x in (x0, x1):
                i = (h - 1 - y) * stride + x * 3
                rows[i:i + 3] = b"\xff\xff\xff"
    for bx, by, side in blobs:
        for y in range(by, by + side):
            for x in range(bx, bx + side):
                i = (h - 1 - y) * stride + x * 3
                rows[i:i + 3] = b"\xff\xff\xff"
    hdr = b"BM" + struct.pack("<IHHI", 54 + len(rows), 0, 0, 54)
    hdr += struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(rows), 2835, 2835, 0, 0)
    open(path, "wb").write(hdr + rows)


def replay(lines, start):
    """Follow-file lines -> (cursor end, largest step, cursor touched an edge,
    click after the last move, shot after the click, verification shot name)."""
    x, y = start
    big, edge, t_move, t_click, t_shot, shot = 0, False, 0.0, None, None, None
    for line in lines:
        t, cmd, *args = line.split()
        t = float(t.lstrip("+"))
        if cmd == "move":
            dx, dy = int(args[0]), int(args[1])
            big = max(big, abs(dx), abs(dy))
            x, y = x + dx, y + dy
            edge |= x <= 0 or y <= 0 or x >= 799 or y >= 599
            t_move = max(t_move, t)
        elif cmd == "click":
            t_click = t
        elif cmd == "shot":
            t_shot, shot = t, args[0]
    return ((x, y), big, edge, t_click is not None and t_click > t_move,
            t_shot is not None and t_click is not None and t_shot > t_click, shot)


def main():
    # Geometry measured on the game's frames.
    check("toggle: the board's minimize control", mo.BOARD_TOGGLE, (787, 35))
    check("minimap: map area", mo.MINIMAP, (10, 454, 150, 593))
    check("centre: the minimap's centre", mo.CENTRE,
          (round((10 + 150) / 2), round((454 + 593) / 2)))

    # Board detection on OCR text of real frames.
    check("board: expanded frame", mo.board_expanded(EXPANDED), True)
    check("board: collapsed frame", mo.board_expanded(COLLAPSED), False)
    check("board: a victory frame is collapsed", mo.board_expanded(VICTORY), False)
    check("board: one stray label is not a board", mo.board_expanded(COLLAPSED + ["Tower Stats"]), False)
    check("board: the AI map's board expanded", mo.board_expanded(AI_BOARD), True)
    check("board: one team line is not the AI board", mo.board_expanded(COLLAPSED + ["The Scourge"]), False)
    check("board: a victory line names a team inside a sentence",
          mo.board_expanded(VICTORY + ["The Scourge has won!"]), False)

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "f.bmp")
        bmp(p, (72, 518, 89, 529))
        check("camera: box centre", mo.camera_box(p), (80.5, 523.5))
        bmp(p, (9 + 1, 577, 26, 588))
        check("camera: box at the fountain", mo.camera_box(p), (18.0, 582.5))
        bmp(p, (72, 518, 89, 529), blobs=((22, 574, 6),))
        check("camera: a white mark at the fountain is not part of the box", mo.camera_box(p), (80.5, 523.5))
        bmp(p, (72, 518, 89, 529), blobs=((20, 572, 8),))
        check("camera: a mark with more white pixels than the box, but not box-shaped, is not the box",
              mo.camera_box(p), (80.5, 523.5))
        bmp(p, (72, 518, 89, 529), blobs=((120, 470, 3), (40, 500, 2)))
        check("camera: small pings are not the box", mo.camera_box(p), (80.5, 523.5))
        bmp(p, None, blobs=((60, 500, 14),))
        check("camera: a box-sized filled white square is taken as the box (known limitation)", mo.camera_box(p), (66.5, 506.5))
        bmp(p, None)
        check("camera: no box", mo.camera_box(p), None)
        bmp(p, (72, 18, 89, 29), size=(400, 300))
        check("camera: not an 800x600 frame", mo.camera_box(p), None)

    cam = (80.5, 523.5)
    centre, tog = mo.CENTRE, mo.BOARD_TOGGLE

    def acts(name, lines, start, target, shot):
        end, big, edge, click_after, shot_after, sname = replay(lines, start)
        check(f"{name}: cursor ends on the target", end, target)
        check(f"{name}: steps of at most 200 points", big <= 200, True)
        check(f"{name}: never at a screen edge (no edge scroll)", edge, False)
        check(f"{name}: click after the motion, verification shot after the click",
              (click_after, shot_after, sname), (True, True, shot))

    o = mo.Observer()
    check("seq: the first frame sets the camera reference, no input", o.shot("m0000", COLLAPSED, cam)[0], [])
    check("seq: collapsed, camera in place: no input", o.shot("m0001", COLLAPSED, cam)[0], [])
    acts("seq: expanded: toggle", o.shot("m0002", EXPANDED, cam)[0], centre, tog, "v0000")
    check("seq: a periodic shot before the verification: no input", o.shot("m0003", EXPANDED, cam)[0], [])
    add, log = o.shot("v0000", COLLAPSED, cam)
    check("seq: verified collapsed: no input", add, [])
    check("seq: ... counted", o.collapses, 1)
    acts("seq: board reopened: collapsed again", o.shot("m0004", EXPANDED, cam)[0], tog, tog, "v0001")
    check("seq: ... reopen counted", o.reopens, 1)
    o.shot("v0001", COLLAPSED, cam)
    check("seq: victory frame: no input", o.shot("m0005", VICTORY, cam)[0], [])
    check("seq: camera moved within tolerance: no input",
          o.shot("m0006", COLLAPSED, (cam[0] + mo.CAMERA_TOLERANCE, cam[1]))[0], [])
    acts("seq: camera moved past tolerance: recentre",
         o.shot("m0007", COLLAPSED, (cam[0] + mo.CAMERA_TOLERANCE + 1, cam[1]))[0], tog, centre, "v0002")
    add, log = o.shot("v0002", COLLAPSED, cam)
    check("seq: recentre verified", (add, any("verified" in m for m in log)), ([], True))

    o = mo.Observer()
    o.shot("m0000", COLLAPSED, cam)
    o.shot("m0001", EXPANDED, cam)
    acts("fail: still expanded after a click: one retry", o.shot("v0000", EXPANDED, cam)[0], tog, tog, "v0001")
    check("fail: still expanded after the retry: no more clicks", o.shot("v0001", EXPANDED, cam)[0], [])
    check("fail: expanded periodic frames: still no clicks (never blind)", o.shot("m0002", EXPANDED, cam)[0], [])
    check("fail: ... nor counted as collapses", o.collapses, 0)
    check("fail: a collapsed frame re-enables clicks", o.shot("m0003", COLLAPSED, cam)[0], [])
    acts("fail: ... then an expanded one is collapsed again", o.shot("m0004", EXPANDED, cam)[0], tog, tog,
         "v0002")

    o = mo.Observer()
    check("start: no camera box: no reference", (o.shot("m0000", COLLAPSED, None)[0], o.camera_ref), ([], None))
    acts("start: the board is handled without a camera reference", o.shot("m0001", EXPANDED, None)[0],
         centre, tog, "v0000")
    o.shot("v0000", COLLAPSED, None)
    check("start: no camera box: never a recentre", o.shot("m0002", COLLAPSED, None)[0], [])
    check("start: the first box found becomes the reference", (o.shot("m0003", COLLAPSED, cam)[0], o.camera_ref),
          ([], cam))

    # The match script never orders the hero (camera-only observation).
    src = open(os.path.join(ROOT, "scripts", "m6_accept.sh")).read()
    match = src[src.index("print(f\"{m0} shot match_start\")"):src.index("print(f\"{end} shot match_end")]
    for cmd in ("key F1", "key M", "key H", "key A", "key S", "click right", "pointer"):
        check(f"match script: no '{cmd}' during the match", cmd in match, False)
    check("match script: the cursor homed once, to the minimap's centre",
          (match.count("goto"), match.count(f"goto {mo.CENTRE[0]} {mo.CENTRE[1]}")), (1, 1))

    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
