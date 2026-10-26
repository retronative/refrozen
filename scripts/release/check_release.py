#!/usr/bin/env python3
"""Release checks of reFrozen.app (RELEASE_PLAN R4/R7b): what the download
actually contains.

  /usr/bin/python3 -I scripts/release/check_release.py <reFrozen.app>

- the signature verifies (codesign --verify --deep --strict);
- every Mach-O is arm64 only, built for macOS 14, and loads only system
  libraries or libraries inside the bundle; no rpath or string names a
  build-machine or Homebrew path;
- the content gate: no Windows executable (MZ), MPQ archive, Warcraft III map
  (HM3W, .w3x/.w3m), game data name, CD-key-shaped string or lifted-function
  symbol (f_<8 hex digits>) anywhere in the bundle;
- reFrozen's licence, the third-party notices and licence texts, and the fonts'
  licences are in the bundle; Info.plist names version 0.1.0, macOS 14 and
  the games category.
Prints one ok/FAIL line per check; exit 1 if any fails.
"""
import os
import plistlib
import re
import subprocess
import sys

APP = sys.argv[1]
fails = 0
KEY = re.compile(rb"(?<![0-9A-Z])[246789BCDEFGHJKMNPRTVWXYZ]{26}(?![0-9A-Z])")
SYMBOL = re.compile(r"\bf_[0-9A-F]{8}\b")
BUILD_PATHS = (b"/opt/homebrew", b"/Users/", b"/private/var/folders", b"/usr/local/Cellar")


def check(name, ok, detail=""):
    global fails
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": {detail}"))
    fails += not ok


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


files = [os.path.join(d, f) for d, _, fs in os.walk(APP) for f in fs]
macho = [f for f in files if not os.path.islink(f) and open(f, "rb").read(4) in
         (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca")]

r = run("codesign", "--verify", "--deep", "--strict", APP)
check("signature verifies (codesign --verify --deep --strict)", r.returncode == 0, r.stderr.strip()[:300])

bad_arch, bad_min, bad_dep, bad_rpath = [], [], [], []
libs_in_bundle = {os.path.basename(f) for f in macho}
for f in macho:
    rel = os.path.relpath(f, APP)
    if run("lipo", "-archs", f).stdout.split() != ["arm64"]:
        bad_arch.append(rel)
    lc = run("otool", "-l", f).stdout
    m = re.search(r"cmd LC_BUILD_VERSION.*?minos (\S+)", lc, re.S)
    if not m or tuple(int(x) for x in m.group(1).split(".")[:2]) > (14, 0):
        bad_min.append(f"{rel} ({m.group(1) if m else 'none'})")
    for rp in re.findall(r"cmd LC_RPATH.*?path (\S+)", lc, re.S):
        if not rp.startswith(("@executable_path", "@loader_path", "/usr/lib/")):
            bad_rpath.append(f"{rel}: {rp}")
    for dep in run("otool", "-L", f).stdout.splitlines()[1:]:
        dep = dep.strip().split(" (")[0]
        if dep.startswith(("/usr/lib/", "/System/Library/")):
            continue
        if dep.startswith(("@rpath/", "@executable_path/", "@loader_path/")) and os.path.basename(dep) in libs_in_bundle:
            continue
        bad_dep.append(f"{rel} -> {dep}")
check(f"every Mach-O is arm64 only ({len(macho)} files)", not bad_arch, ", ".join(bad_arch[:5]))
check("every Mach-O targets macOS 14 or earlier", not bad_min, ", ".join(bad_min[:5]))
check("rpaths are bundle-relative or system (/usr/lib: the Swift runtime) only", not bad_rpath, ", ".join(bad_rpath[:5]))
check("every library loaded is a system library or inside the bundle", not bad_dep, ", ".join(bad_dep[:8]))

paths_found = []
for f in macho:
    data = open(f, "rb").read()
    for p in BUILD_PATHS:
        if p in data:
            paths_found.append(f"{os.path.relpath(f, APP)}: {p.decode()}")
check("no build-machine or Homebrew path inside a binary", not paths_found, ", ".join(paths_found[:8]))

# The content gate.
mz, mpq, maps, names, keys, syms = [], [], [], [], [], []
for f in files:
    if os.path.islink(f):
        continue
    rel = os.path.relpath(f, APP)
    with open(f, "rb") as h:
        head = h.read(4)
        h.seek(0)
        data = h.read()
    if head[:2] == b"MZ":
        mz.append(rel)
    if head == b"MPQ\x1a":
        mpq.append(rel)
    if head == b"HM3W" or rel.lower().endswith((".w3x", ".w3m", ".w3g")):
        maps.append(rel)
    if rel.lower().endswith((".mpq", ".exe", ".dll", ".asi", ".m3d", ".flt")):
        names.append(rel)
    for k in KEY.findall(data):
        keys.append(f"{rel}: {k[:6].decode()}…")
for f in macho:
    syms += [f"{os.path.relpath(f, APP)}: {s}" for s in SYMBOL.findall(run("nm", "-U", f).stdout)][:3]
check("no Windows executable or DLL (MZ header)", not mz, ", ".join(mz[:5]))
check("no MPQ archive", not mpq, ", ".join(mpq[:5]))
check("no Warcraft III map or replay", not maps, ", ".join(maps[:5]))
check("no game file names (.mpq .exe .dll .asi .m3d .flt)", not names, ", ".join(names[:5]))
check("no CD-key-shaped string (26 characters of the key alphabet)", not keys, ", ".join(keys[:5]))
check("no lifted game function symbol in a binary", not syms, ", ".join(syms[:5]))

res = os.path.join(APP, "Contents", "Resources")
need = ["licenses/COPYING", "licenses/NOTICE", "licenses/THIRD_PARTY_NOTICES.md", "licenses/LICENSES/GPL-3.0.txt",
        "licenses/LICENSES/x86recomp-MIT.txt", "kit/resources/OFL-Cinzel.txt", "kit/resources/OFL-Inter.txt",
        "kit/resources/OFL-Cormorant-Garamond.txt"]
missing = [n for n in need if not os.path.exists(os.path.join(res, n))]
check("licences and notices are in the bundle", not missing, ", ".join(missing))
dep_licences = [n for n in ("SDL3", "StormLib", "glslang", "SPIRV-Tools", "SPIRV-Cross", "SoftFloat", "Zydis", "LLVM")
                if not os.path.exists(os.path.join(res, "licenses", "third-party", n))]
check("each shipped or linked dependency's licence is in the bundle", not dep_licences, ", ".join(dep_licences))

info = plistlib.load(open(os.path.join(APP, "Contents", "Info.plist"), "rb"))
check("Info.plist: version 0.1.0", info.get("CFBundleShortVersionString") == "0.1.0", str(info.get("CFBundleShortVersionString")))
check("Info.plist: macOS 14 minimum", info.get("LSMinimumSystemVersion") == "14.0")
check("Info.plist: games category (Game Mode)", info.get("LSApplicationCategoryType") == "public.app-category.games")

print("ALL PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
