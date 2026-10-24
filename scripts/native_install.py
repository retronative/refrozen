#!/usr/bin/env python3
"""Install Warcraft III RoC + TFT 1.21b from the player's installers and patch
it to 1.26a, natively (no Wine, no Windows tools), then optionally verify the
result against a reference install.

  /opt/homebrew/bin/python3 -I scripts/native_install.py \
      --roc "<RoC installer dir>" --tft "<TFT installer dir>" \
      --patch "<War3TFT_126a_English.exe>" --out game/native-install \
      [--verify "<reference install dir>"]

Install: each installer's tome ("Installer Tome.mpq") carries the installer's
own manifest, InstallCD/InstallerFileList/InstallerFileList.xml. Its Win32
branch is interpreted: <repack_into type="file"> copies a tome file into the
install folder, <repack_into type="mpq" container="X"> adds it to archive X.
CD keys, as the installer stores them: <encrypt object="cdkey26"> writes the
product's key (26 characters, upper case, no dashes) and <encrypt
object="user"> the owner's name, each with its NUL, into font\\font.gid / font.exp /
font.clh inside the MPQs, in the cipher game.dll reads them with
(scripts/font_keydata.py; checked byte for byte against the official
installer's output). The keys are asked for as the installer asks (or read
from stdin when it is not a terminal), the name comes from --owner; neither is
stored anywhere else. The game validates the keys itself when it starts.
<repack type="cdkey1encode"> (font\\font.ccd) is not reproduced: the shipped
file is kept (game.dll's decoder rejects both it and the official one).

Patch: the 1.26a patch EXE embeds an MPQ holding Patch_War3x.mpq, BNUpdate's
input. Each patch.lst line is "target;record[;flags]"; a record is applied by
build/bnupdate_patch (whole file, or an RLE-packed BSDIFF40 delta). A delta's
base is the revert.lst name of the target, read from the installed MPQs
(War3xLocal, War3x, war3), the one whose size equals the record's base-size
field. 3-field targets go into a new War3Patch.mpq (delete.lst removes the old
one), except plain names that exist as loose files; 2-field targets are loose
files. These rules reproduce the official patcher's output for 1.26a.

Needs StormLib (brew install stormlib) and build/bnupdate_patch
(scripts/setup_tools.sh).
"""
import argparse
import ctypes
import getpass
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_keydata  # noqa: E402
PATCHER = os.path.join(ROOT, "build", "bnupdate_patch")

# ---- StormLib --------------------------------------------------------------

storm = ctypes.CDLL("/opt/homebrew/opt/stormlib/lib/libstorm.dylib")
HANDLE = ctypes.c_void_p
DWORD = ctypes.c_uint32
MPQ_OPEN_READ_ONLY = 0x100
MPQ_FILE_COMPRESS = 0x200
MPQ_FILE_REPLACEEXISTING = 0x80000000
MPQ_COMPRESSION_ZLIB = 0x02
MPQ_CREATE_LISTFILE = 0x00100000
MPQ_CREATE_ATTRIBUTES = 0x00200000


class FindData(ctypes.Structure):
    _fields_ = [("cFileName", ctypes.c_char * 1024), ("szPlainName", ctypes.c_char_p),
                ("dwHashIndex", DWORD), ("dwBlockIndex", DWORD), ("dwFileSize", DWORD),
                ("dwFileFlags", DWORD), ("dwCompSize", DWORD), ("dwFileTimeLo", DWORD),
                ("dwFileTimeHi", DWORD), ("lcLocale", DWORD)]


storm.SFileOpenArchive.argtypes = [ctypes.c_char_p, DWORD, DWORD, ctypes.POINTER(HANDLE)]
storm.SFileOpenArchive.restype = ctypes.c_bool
storm.SFileCreateArchive.argtypes = [ctypes.c_char_p, DWORD, DWORD, ctypes.POINTER(HANDLE)]
storm.SFileCreateArchive.restype = ctypes.c_bool
storm.SFileCloseArchive.argtypes = [HANDLE]
storm.SFileCloseArchive.restype = ctypes.c_bool
storm.SFileAddListFile.argtypes = [HANDLE, ctypes.c_char_p]
storm.SFileAddListFile.restype = DWORD
storm.SFileOpenFileEx.argtypes = [HANDLE, ctypes.c_char_p, DWORD, ctypes.POINTER(HANDLE)]
storm.SFileOpenFileEx.restype = ctypes.c_bool
storm.SFileGetFileSize.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
storm.SFileGetFileSize.restype = DWORD
storm.SFileReadFile.argtypes = [HANDLE, ctypes.c_void_p, DWORD, ctypes.POINTER(DWORD), ctypes.c_void_p]
storm.SFileReadFile.restype = ctypes.c_bool
storm.SFileCloseFile.argtypes = [HANDLE]
storm.SFileCloseFile.restype = ctypes.c_bool
storm.SFileFindFirstFile.argtypes = [HANDLE, ctypes.c_char_p, ctypes.POINTER(FindData), ctypes.c_char_p]
storm.SFileFindFirstFile.restype = HANDLE
storm.SFileFindNextFile.argtypes = [HANDLE, ctypes.POINTER(FindData)]
storm.SFileFindNextFile.restype = ctypes.c_bool
storm.SFileFindClose.argtypes = [HANDLE]
storm.SFileFindClose.restype = ctypes.c_bool
storm.SFileAddFileEx.argtypes = [HANDLE, ctypes.c_char_p, ctypes.c_char_p, DWORD, DWORD, DWORD]
storm.SFileAddFileEx.restype = ctypes.c_bool
storm.SFileGetMaxFileCount.argtypes = [HANDLE]
storm.SFileGetMaxFileCount.restype = DWORD
storm.SFileSetMaxFileCount.argtypes = [HANDLE, DWORD]
storm.SFileSetMaxFileCount.restype = ctypes.c_bool
storm.SFileGetLastError = storm.SErrGetLastError
storm.SFileGetLastError.restype = DWORD


def enc(s):
    return s.encode("latin-1")


class Mpq:
    def __init__(self, path, write=False, listfile=None):
        self.h = HANDLE()
        if not storm.SFileOpenArchive(enc(path), 0, 0 if write else MPQ_OPEN_READ_ONLY,
                                      ctypes.byref(self.h)):
            raise RuntimeError(f"cannot open MPQ {path}: error {storm.SFileGetLastError()}")
        if listfile:
            storm.SFileAddListFile(self.h, enc(listfile))

    @classmethod
    def create(cls, path, max_files):
        self = cls.__new__(cls)
        self.h = HANDLE()
        if not storm.SFileCreateArchive(enc(path), MPQ_CREATE_LISTFILE | MPQ_CREATE_ATTRIBUTES,
                                        max_files, ctypes.byref(self.h)):
            raise RuntimeError(f"cannot create MPQ {path}: error {storm.SFileGetLastError()}")
        return self

    def close(self):
        storm.SFileCloseArchive(self.h)

    def names(self):
        fd = FindData()
        find = storm.SFileFindFirstFile(self.h, b"*", ctypes.byref(fd), None)
        out = []
        more = bool(find)
        while more:
            out.append(fd.cFileName.decode("latin-1"))
            more = storm.SFileFindNextFile(find, ctypes.byref(fd))
        if find:
            storm.SFileFindClose(find)
        return out

    def read(self, name):
        f = HANDLE()
        if not storm.SFileOpenFileEx(self.h, enc(name), 0, ctypes.byref(f)):
            return None
        size = storm.SFileGetFileSize(f, None)
        buf = ctypes.create_string_buffer(size)
        got = DWORD()
        ok = storm.SFileReadFile(f, buf, size, ctypes.byref(got), None)
        storm.SFileCloseFile(f)
        if not ok or got.value != size:
            raise RuntimeError(f"cannot read {name}")
        return buf.raw

    def add(self, src_path, name):
        if not storm.SFileAddFileEx(self.h, enc(src_path), enc(name),
                                    MPQ_FILE_COMPRESS | MPQ_FILE_REPLACEEXISTING,
                                    MPQ_COMPRESSION_ZLIB, MPQ_COMPRESSION_ZLIB):
            err = storm.SFileGetLastError()
            if err == 1006:  # ERROR_DISK_FULL: the hash table is full
                cur = storm.SFileGetMaxFileCount(self.h)
                if storm.SFileSetMaxFileCount(self.h, max(cur * 2, 16)):
                    return self.add(src_path, name)
            raise RuntimeError(f"cannot add {name}: error {err}")


# ---- helpers ---------------------------------------------------------------

def norm(p):
    return p.replace("\\", "/").lower()


def disk_path(root, rel):
    """Install path for a Windows-style relative path; reuses existing folder
    and file names case-insensitively, as on the Windows install."""
    cur = root
    parts = [p for p in rel.replace("\\", "/").split("/") if p]
    for i, part in enumerate(parts):
        match = None
        if os.path.isdir(cur):
            for e in os.listdir(cur):
                if e.lower() == part.lower():
                    match = e
                    break
        cur = os.path.join(cur, match or part)
    return cur


FILETIME_UNIX_EPOCH = 116444736000000000


def stamp(path, filetime=FILETIME_UNIX_EPOCH):
    """StormLib stores the local file's mtime in (attributes); a fixed stamp
    keeps the archives reproducible run to run."""
    t = max(filetime - FILETIME_UNIX_EPOCH, 0) // 10_000_000
    os.utime(path, (t, t))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def list_lines(data):
    """BNUpdate list files: CRLF lines, terminated by a "*" line."""
    out = []
    for line in data.decode("latin-1").splitlines():
        s = line.strip()
        if s == "*":
            break
        if s:
            out.append(s)
    return out


# ---- install ---------------------------------------------------------------

def evaluate(elem, actions):
    """Walk the manifest for Win32; collect (kind, container, from, to)."""
    for child in elem:
        tag = child.tag
        if tag == "if":
            cond = child.get("true_condition")
            taken = cond == "Win32"  # English: every language test is false
            then = child.find("then")
            other = child.find("else")
            if then is None and other is None:
                if taken:
                    evaluate(child, actions)
            elif taken and then is not None:
                evaluate(then, actions)
            elif not taken and other is not None:
                evaluate(other, actions)
        elif tag == "target":
            if child.get("location") == "user":
                evaluate(child, actions)
        elif tag == "repack_into":
            kind = child.get("type")
            for r in child:
                if r.tag == "repack":
                    src = r.get("from") or r.get("input0")
                    if r.get("type") == "cdkey1encode":
                        actions.append(("cdkey", child.get("container"), src, r.get("to")))
                    else:
                        actions.append((kind, child.get("container"), src, r.get("to")))
                elif r.tag == "encrypt":
                    actions.append(("cdkey", child.get("container"), r.get("object"), r.get("into")))
        elif tag in ("disc", "archive"):
            evaluate(child, actions)


KEY_ALPHABET = set("246789BCDEFGHJKMNPRTVWXYZ")


def normalise_key(text):
    """A 26-character Warcraft III key as the installer stores it, or None."""
    k = "".join(text.split()).replace("-", "").upper()
    return k if len(k) == 26 and set(k) <= KEY_ALPHABET else None


def ask_key(product):
    prompt = f"{product} CD key: "
    text = getpass.getpass(prompt) if sys.stdin.isatty() else sys.stdin.readline()
    key = normalise_key(text)
    if key is None:
        raise SystemExit(f"{product}: not a 26-character CD key")
    return key


def keyfile(plain):
    return font_keydata.encode(plain, b"\0" * (64 - len(plain)))


def install_product(installer_dir, out, work, log, secrets):
    tome = Mpq(os.path.join(installer_dir, "Installer Tome.mpq"))
    xml = tome.read("InstallCD\\InstallerFileList\\InstallerFileList.xml")
    actions = []
    evaluate(ET.fromstring(xml), actions)
    counts = {"file": 0, "mpq": 0, "cdkey": 0}
    open_mpqs = {}
    tmp = os.path.join(work, "tome-file")
    for kind, container, src, to in actions:
        if kind == "cdkey":
            counts["cdkey"] += 1
            if src not in secrets:  # cdkey1encode of a tome file
                log.append(f"kept shipped file, cdkey1encode not reproduced: {container}:{to}")
                continue
            kind, data = "mpq", keyfile(secrets[src])
            log.append(f"encoded {src} into {container}:{to}")
        else:
            data = tome.read(src)
        if data is None:
            raise RuntimeError(f"tome file missing: {src}")
        if kind == "file":
            dst = disk_path(out, to)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
        elif kind == "mpq":
            key = norm(container)
            if key not in open_mpqs:
                open_mpqs[key] = Mpq(disk_path(out, container), write=True)
            with open(tmp, "wb") as f:
                f.write(data)
            stamp(tmp)
            open_mpqs[key].add(tmp, to)
        else:
            continue
        counts[kind] += 1
    for m in open_mpqs.values():
        m.close()
    tome.close()
    return counts


# ---- patch -----------------------------------------------------------------

def patch(patch_exe, out, work, log):
    outer = Mpq(patch_exe)
    inner_path = os.path.join(work, "Patch_War3x.mpq")
    with open(inner_path, "wb") as f:
        f.write(outer.read("Patch_War3x.mpq"))
    patch_txt = outer.read("patch.txt")
    outer.close()
    if patch_txt is not None:
        with open(disk_path(out, "Patch.txt"), "wb") as f:
            f.write(patch_txt)

    p = Mpq(inner_path)
    entries = [l.split(";") for l in list_lines(p.read("patch.lst"))]
    revert = {norm(a): b for a, b in (l.split(";")[:2] for l in list_lines(p.read("revert.lst")))}
    for name in list_lines(p.read("delete.lst")):
        victim = disk_path(out, name)
        if os.path.isfile(victim):
            os.remove(victim)

    bases = [Mpq(disk_path(out, n)) for n in ("War3xLocal.mpq", "War3x.mpq", "war3.mpq")]
    rec_path, base_path, new_path = (os.path.join(work, n) for n in ("rec", "base", "new"))
    staged = os.path.join(work, "war3patch")
    os.makedirs(staged, exist_ok=True)
    into_mpq = []
    counts = {"disk": 0, "War3Patch.mpq": 0}
    for f in entries:
        target, recname = f[0], f[1]
        rec = p.read(recname)
        if rec is None or rec[:3] != b"\x18\x00\x04":
            raise RuntimeError(f"bad record {recname}")
        with open(rec_path, "wb") as fh:
            fh.write(rec)
        base_arg = "-"
        if rec[3] == 4:
            base_size = struct.unpack_from("<I", rec, 8)[0]
            key = revert.get(norm(target), target)
            base = None
            for m in bases:
                data = m.read(key)
                if data is not None and len(data) == base_size:
                    base = data
                    break
            if base is None:
                raise RuntimeError(f"no base of {base_size} bytes for {target} ({key})")
            with open(base_path, "wb") as fh:
                fh.write(base)
            base_arg = base_path
        subprocess.run([PATCHER, rec_path, base_arg, new_path], check=True)

        loose = disk_path(out, target)
        to_disk = len(f) == 2 or ("\\" not in target and os.path.isfile(loose))
        if to_disk:
            os.makedirs(os.path.dirname(loose), exist_ok=True)
            shutil.copyfile(new_path, loose)
            counts["disk"] += 1
        else:
            stage = os.path.join(staged, str(len(into_mpq)))
            shutil.copyfile(new_path, stage)
            stamp(stage, struct.unpack_from("<Q", rec, 0x10)[0])
            into_mpq.append((stage, target))
            counts["War3Patch.mpq"] += 1
    for m in bases:
        m.close()
    p.close()

    w3p = Mpq.create(disk_path(out, "War3Patch.mpq"), max(len(into_mpq) * 2, 64))
    for stage, target in into_mpq:
        w3p.add(stage, target)
    w3p.close()
    return counts


# ---- verify ----------------------------------------------------------------

# Written by the Windows tools themselves, not game files.
NOT_COMPARED = ("errors/", "bnupdate.exe", "bnupdate.log", "warcraft iii install log.html",
                "warcraft iii - the frozen throne install log.html")
# Written by the game when it runs (the oracle has been played), not installed.
RUNTIME_WRITTEN = ("maps/download/", "save/", "tempreplay.w3g")
MPQ_BOOKKEEPING = ("(listfile)", "(attributes)", "(signature)")
CDKEY_FILES = ("font/font.gid", "font/font.clh", "font/font.ccd", "font/font.exp")


def walk(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            out[norm(os.path.relpath(p, root))] = p
    return out


def verify(out, ref, listfile):
    ours, theirs = walk(out), walk(ref)
    report = {"identical": 0, "differ": [], "missing": [], "extra": []}
    mpq_names = []
    for rel, path in sorted(theirs.items()):
        if rel.startswith(NOT_COMPARED[0]) or rel in NOT_COMPARED[1:] or rel.startswith(RUNTIME_WRITTEN):
            continue
        if rel not in ours:
            report["missing"].append(rel)
        elif rel.endswith(".mpq") and "/" not in rel:
            mpq_names.append(rel)
        elif sha256(path) == sha256(ours[rel]):
            report["identical"] += 1
        else:
            report["differ"].append(rel)
    for rel in ours:
        if rel not in theirs:
            report["extra"].append(rel)

    mpq_report = {}
    for rel in mpq_names:
        a, b = Mpq(theirs[rel], listfile=listfile), Mpq(ours[rel], listfile=listfile)
        names = {norm(n): n for n in a.names()}
        ours_names = {norm(n) for n in b.names()}
        r = {"identical": 0, "differ": [], "missing": [], "cdkey": [], "bytes_identical": False}
        r["bytes_identical"] = sha256(theirs[rel]) == sha256(ours[rel])
        for key, name in sorted(names.items()):
            if key in MPQ_BOOKKEEPING:
                continue
            if key in CDKEY_FILES:
                # Contents are key-derived: compared by equality only, never printed.
                if a.read(name) != b.read(name):
                    r["cdkey"].append(key)
                continue
            if key not in ours_names:
                r["missing"].append(key)
                continue
            if a.read(name) == b.read(name):
                r["identical"] += 1
            else:
                r["differ"].append(key)
        r["extra"] = sorted(k for k in ours_names - set(names) if k not in MPQ_BOOKKEEPING)
        a.close()
        b.close()
        mpq_report[rel] = r
    return report, mpq_report


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--roc", required=True)
    ap.add_argument("--tft", required=True)
    ap.add_argument("--patch", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--owner", required=True, help="the name the installer asks for (font.clh)")
    ap.add_argument("--verify")
    args = ap.parse_args()
    owner = args.owner.encode("cp1252")
    if not 0 < len(owner) < 63 or b"\0" in owner:
        sys.exit("--owner: 1 to 62 characters")
    keys = {"RoC": ask_key("Warcraft III"), "TFT": ask_key("The Frozen Throne")}
    if os.path.exists(args.out) and os.listdir(args.out):
        sys.exit(f"{args.out} is not empty")
    os.makedirs(args.out, exist_ok=True)
    log = []
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(args.out))) as work:
        for name, d in (("RoC", args.roc), ("TFT", args.tft)):
            secrets = {"cdkey26": keys[name].encode() + b"\0", "user": owner + b"\0"}
            print(f"install {name}: {install_product(d, args.out, work, log, secrets)}")
        print(f"patch 1.26a: {patch(args.patch, args.out, work, log)}")
        for line in log:
            print("  " + line)
        if not args.verify:
            return 0
        # War3Patch.mpq is written without the patch's names in a listfile on
        # the reference side, so name its files from patch.lst and revert.lst.
        p = Mpq(os.path.join(work, "Patch_War3x.mpq"))
        names = [l.split(";")[0] for l in list_lines(p.read("patch.lst"))]
        names += [l.split(";")[0] for l in list_lines(p.read("revert.lst"))]
        p.close()
        listfile = os.path.join(work, "listfile.txt")
        with open(listfile, "w", encoding="latin-1") as f:
            f.write("\n".join(names))
        report, mpqs = verify(args.out, args.verify, listfile)
    ok = not (report["differ"] or report["missing"])
    print(f"\nloose files: {report['identical']} byte-identical, "
          f"{len(report['differ'])} differ, {len(report['missing'])} missing, "
          f"{len(report['extra'])} extra")
    for k in ("differ", "missing", "extra"):
        for rel in report[k]:
            print(f"  {k}: {rel}")
    for rel, r in mpqs.items():
        print(f"{rel}: {r['identical']} files identical, {len(r['differ'])} differ, "
              f"{len(r['missing'])} missing, {len(r['extra'])} extra, "
              f"CD-key files differing: {len(r['cdkey'])}, archive bytes identical: {r['bytes_identical']}")
        for k in ("differ", "missing", "extra", "cdkey"):
            for name in r[k]:
                print(f"  {k}: {name}")
        ok = ok and not (r["differ"] or r["missing"])
    print("\nVERIFY:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
