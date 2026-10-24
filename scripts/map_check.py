#!/usr/bin/env python3
"""Static compatibility check of a Warcraft III map against an install.

  /opt/homebrew/bin/python3 -I scripts/map_check.py <map.w3x> <install dir> [--out dir]

Reports the map's MPQ header (protected maps use odd sector sizes, tables
and listfiles), its HM3W and war3map.w3i headers, and checks its JASS script
with pjass (tools/pjass) against the install's own Scripts\\common.j and
Scripts\\Blizzard.j, read through the game's MPQ order (War3Patch, War3xLocal,
War3x, war3). Prints facts only, never map or game contents beyond names.
"""
import argparse
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from native_install import Mpq, ROOT, disk_path  # noqa: E402

PJASS = os.path.join(ROOT, "tools", "pjass", "pjass")
# Checked in this order (HYPOTHESIS: the game's own lookup order; see FEASIBILITY).
SCRIPT_NAMES = ("Scripts\\war3map.j", "war3map.j")
GAME_MPQS = ("War3Patch.mpq", "War3xLocal.mpq", "War3x.mpq", "war3.mpq")


def mpq_header(raw):
    off = raw.find(b"MPQ\x1a")
    while off >= 0 and off % 512:
        off = raw.find(b"MPQ\x1a", off + 1)
    if off < 0:
        return None
    hsize, asize, ver, shift, hpos, bpos, hcount, bcount = struct.unpack_from("<IIHHIIII", raw, off + 4)
    return {"offset": off, "header_size": hsize, "archive_size": asize, "format": ver,
            "sector_size": 512 << shift, "hash_entries": hcount, "block_entries": bcount}


def hm3w(raw):
    if raw[:4] != b"HM3W":
        return None
    end = raw.index(b"\0", 8)
    flags, players = struct.unpack_from("<II", raw, end + 1)
    return {"name": raw[8:end].decode("utf-8", "replace"), "flags": hex(flags), "max_players": players}


def w3i(data):
    fmt, saves, editor = struct.unpack_from("<iii", data, 0)
    pos = 12
    fields = []
    for _ in range(4):  # name, author, description, recommended players
        end = data.index(b"\0", pos)
        fields.append(data[pos:end].decode("utf-8", "replace"))
        pos = end + 1
    return {"format": fmt, "saves": saves, "editor_version": editor, "name": fields[0],
            "author": fields[1], "players_text": fields[3]}


def read_game_file(install, name):
    for mpq in GAME_MPQS:
        path = disk_path(install, mpq)
        if os.path.isfile(path):
            m = Mpq(path)
            data = m.read(name)
            m.close()
            if data is not None:
                return data, mpq
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("install")
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "mapcheck"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    with open(args.map, "rb") as f:
        raw = f.read()
    print("HM3W:", hm3w(raw))
    print("MPQ header:", mpq_header(raw))

    m = Mpq(args.map)
    names = m.names()
    listfile = m.read("(listfile)")
    print(f"listed files: {len(names)}; (listfile) present: {listfile is not None}")
    info = m.read("war3map.w3i")
    print("war3map.w3i:", w3i(info) if info else "missing")
    strings = m.read("war3map.wts")
    print("war3map.wts:", f"{len(strings)} bytes" if strings else "missing")
    script, script_name = None, None
    for n in SCRIPT_NAMES:
        data = m.read(n)
        if data is None:
            print(f"{n}: absent")
            continue
        head = data[:24].split(b":")[0].decode("latin-1", "replace")
        jass = b"function " in data and b"endfunction" in data
        print(f"{n}: {len(data)} bytes, {'JASS' if jass else 'not JASS (starts ' + repr(head) + ')'}")
        if script is None and jass:
            script, script_name = data, n
    m.close()
    if script is None:
        print("script: not found under", SCRIPT_NAMES)
        return 1
    print(f"script: {script_name}, {len(script)} bytes, {script.count(b'function ')} 'function' tokens")

    paths = {}
    for name, data in (("war3map.j", script),):
        paths[name] = os.path.join(args.out, name)
        with open(paths[name], "wb") as f:
            f.write(data)
    for name in ("Scripts\\common.j", "Scripts\\Blizzard.j"):
        data, src = read_game_file(args.install, name)
        if data is None:
            print(f"{name}: not found in the install")
            return 1
        base = name.split("\\")[1]
        paths[base] = os.path.join(args.out, base)
        with open(paths[base], "wb") as f:
            f.write(data)
        print(f"{name}: {len(data)} bytes from {src}")

    r = subprocess.run([PJASS, paths["common.j"], paths["Blizzard.j"], paths["war3map.j"]],
                       capture_output=True, text=True, errors="replace")
    out = (r.stdout + r.stderr).strip().splitlines()
    errors = [l for l in out if "Parse successful" not in l and "Parse failed" not in l and l.strip()]
    for l in out:
        if "Parse successful" in l or "Parse failed" in l:
            print("pjass:", l)
    print(f"pjass: exit {r.returncode}, {len(errors)} error lines")
    for l in errors[:40]:
        print("  " + l)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
