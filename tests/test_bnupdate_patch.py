#!/usr/bin/env python3
"""Hand-computed cases for build/bnupdate_patch (no game data).

  /opt/homebrew/bin/python3 -I tests/test_bnupdate_patch.py [path/to/bnupdate_patch]

The delta case applies three control entries to old = "ABCDEFGH":
  1. add 4 (data 01 00 FF 00), extra "xy", seek +2:
     "A"+1="B", "B", "C"+0xFF wraps to "B", "D"; then "xy"; old offset 4+2 = 6
  2. add 2 (data 00 01), extra "", seek -6 (sign-magnitude 0x80000006):
     old[6]="G", old[7]+1="I"; old offset 8-6 = 2
  3. add 2 (data 10 00), extra "z", seek 0:
     old[2]+0x10="S", old[3]="D"; then "z"
  => "BBBDxyGISDz"
"""
import os
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "bnupdate_patch")
failures = 0


def rle(blob):
    """Literal runs (0x80 | n-1) and zero runs (n-1), at most 128 bytes each."""
    out, i = bytearray(), 0
    while i < len(blob):
        if blob[i] == 0:
            n = 1
            while i + n < len(blob) and blob[i + n] == 0 and n < 128:
                n += 1
            out.append(n - 1)
        else:
            n = 1
            while i + n < len(blob) and blob[i + n] != 0 and n < 128:
                n += 1
            out.append(0x80 | (n - 1))
            out += blob[i:i + n]
        i += n
    return bytes(out)


def record(rec_type, payload, new_size, base_size=0):
    return struct.pack("<HBBIIIQ", 0x18, 4, rec_type, 0, base_size, new_size, 0) + payload


def delta_record(ctrl, data, extra, new_size, base_size, declared_new_size=None):
    blob = b"BSDIFF40" + struct.pack("<QQQ", len(ctrl), len(data),
                                     new_size if declared_new_size is None else declared_new_size)
    blob += ctrl + data + extra
    return record(4, struct.pack("<I", len(blob)) + rle(blob), new_size, base_size)


def run(rec, old, tmp):
    rec_path, old_path, new_path = (os.path.join(tmp, n) for n in ("rec", "old", "new"))
    with open(rec_path, "wb") as f:
        f.write(rec)
    if old is not None:
        with open(old_path, "wb") as f:
            f.write(old)
    if os.path.exists(new_path):
        os.remove(new_path)
    r = subprocess.run([TOOL, rec_path, old_path if old is not None else "-", new_path],
                       capture_output=True)
    if r.returncode:
        return None
    with open(new_path, "rb") as f:
        return f.read()


def check(name, got, want):
    global failures
    if got != want:
        failures += 1
        print(f"FAIL {name}: got {got!r}, want {want!r}")


def main():
    old = b"ABCDEFGH"
    ctrl = struct.pack("<9I", 4, 2, 2, 2, 0, 0x80000006, 2, 1, 0)
    data = bytes([0x01, 0x00, 0xFF, 0x00, 0x00, 0x01, 0x10, 0x00])
    extra = b"xyz"
    with tempfile.TemporaryDirectory() as tmp:
        check("delta", run(delta_record(ctrl, data, extra, 11, len(old)), old, tmp), b"BBBDxyGISDz")
        check("whole file", run(record(1, b"hello", 5), None, tmp), b"hello")
        check("whole file, wrong size", run(record(1, b"hello", 6), None, tmp), None)
        check("BSDIFF40 size differs from header",
              run(delta_record(ctrl, data, extra, 11, len(old), declared_new_size=12), old, tmp), None)
        truncated = delta_record(ctrl, data, extra, 11, len(old))[:-2]
        check("truncated RLE literal run", run(truncated, old, tmp), None)
        check("control block ends early",
              run(delta_record(ctrl[:12], data[:4], extra[:2], 11, len(old)), old, tmp), None)
        check("delta without old file", run(delta_record(ctrl, data, extra, 11, len(old)), None, tmp), None)
    print("bnupdate_patch:", "FAILED" if failures else "ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
