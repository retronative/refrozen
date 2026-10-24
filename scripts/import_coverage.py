#!/usr/bin/env python3
"""How every import of the recompiled modules is bound.

    scripts/import_coverage.py [--install DIR] [--generated DIR] [--tsv OUT]

For war3.exe and each lifted DLL (src/main.cpp lifted_dlls), every PE import is
classified the way the runtime loader binds it (process.cpp BindImport):

  lifted   imported from another lifted module, by name or #ordinal; the export
           must exist (else the loader stops) and be a lifted function entry
           (generated table.cpp), else the first call stops in Dispatch;
           an export in a data section (_acmdln, _HUGE, ...) binds as data
  hle      a Win32 export with an HLE handler (HLE/HLE_NAMED) in a library the
           refrozen executable links (recomp_runtime and the recomp_* HLE modules
           named in CMakeLists.txt); handlers in unlinked modules do not count
  stub     a Win32 export with no handler: a strict stub that stops the process
           with "unimplemented import" when called

Exit 1 if any lifted import is unresolved; stubs are reported, not errors.
"""
import argparse
import collections
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.path.join(ROOT, "tools/x86recomp")
# Handler names: an export name, or "#N" for an export by ordinal (wsock32).
HLE_RE = re.compile(r'^HLE(?:_NAMED)?\("([^"]+)",\s*"?(#?[A-Za-z0-9_@?$]+)"?,', re.M)
TABLE_RE = re.compile(r"^void f_([0-9A-F]{8})\(", re.M)


def normalise_dll(name):
    name = name.lower().replace("/", "\\").rsplit("\\", 1)[-1]
    return name if "." in name else name + ".dll"


def linked_hle_sources():
    """Sources of recomp_runtime and of each recomp_* library refrozen links."""
    with open(os.path.join(ROOT, "CMakeLists.txt")) as f:
        ours = f.read()
    link = re.search(r"target_link_libraries\(refrozen\s+PRIVATE([^)]*)\)", ours).group(1).split()
    with open(os.path.join(X86, "CMakeLists.txt")) as f:
        theirs = f.read()
    srcs = []
    for lib in set(link) | {"recomp_runtime"}:
        m = re.search(r"add_library\(" + lib + r"\s+SHARED([^)]*)\)", theirs)
        if m:
            srcs += [x for x in m.group(1).split() if x.startswith("src/runtime/hle/") and x.endswith(".cpp")]
    return srcs


def lifted_dlls():
    with open(os.path.join(ROOT, "src/main.cpp")) as f:
        src = f.read()
    block = re.search(r"lifted_dlls = \{(.*?)\n  \};", src, re.S).group(1)
    return [s.replace("\\\\", "\\") for s in re.findall(r'\{"([^"]+)"\}', block)]


class Pe:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.d = d = f.read()
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        nsec, optsize = struct.unpack_from("<H", d, pe + 6)[0], struct.unpack_from("<H", d, pe + 20)[0]
        opt = pe + 24
        self.base = struct.unpack_from("<I", d, opt + 28)[0]
        self.dirs = [struct.unpack_from("<II", d, opt + 96 + 8 * i) for i in range(16)]
        self.sections = []
        for i in range(nsec):
            o = opt + optsize + 40 * i
            vsize, rva, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
            chars = struct.unpack_from("<I", d, o + 36)[0]
            self.sections.append((rva, max(vsize, rsize), rptr, rsize, bool(chars & 0x20000000)))

    def off(self, rva):
        for start, size, rptr, rsize, _ in self.sections:
            if start <= rva < start + size and rva - start < rsize:
                return rptr + rva - start
        raise ValueError(f"rva {rva:X} not in file")

    def executable(self, va):
        return any(s <= va - self.base < s + size for s, size, _, _, x in self.sections if x)

    def u32(self, rva):
        return struct.unpack_from("<I", self.d, self.off(rva))[0]

    def cstr(self, rva):
        o = self.off(rva)
        return self.d[o:self.d.index(b"\0", o)].decode("latin-1")

    def imports(self):
        rva, size = self.dirs[1]
        out = []
        while size:
            ilt, name_rva, iat = self.u32(rva), self.u32(rva + 12), self.u32(rva + 16)
            if not name_rva:
                break
            dll = self.cstr(name_rva)
            look = ilt or iat
            while v := self.u32(look):
                out.append((dll, f"#{v & 0xFFFF}" if v & 0x80000000 else self.cstr(v + 2)))
                look += 4
            rva += 20
        return out

    def exports(self):
        """{name or #ordinal: va}; forwarders are left out, as the loader does."""
        rva, size = self.dirs[0]
        if not size:
            return {}
        base, nfuncs, nnames = self.u32(rva + 16), self.u32(rva + 20), self.u32(rva + 24)
        funcs, names, ords = self.u32(rva + 28), self.u32(rva + 32), self.u32(rva + 36)
        named = {}
        for i in range(nnames):
            idx = struct.unpack_from("<H", self.d, self.off(ords + 2 * i))[0]
            named[idx] = self.cstr(self.u32(names + 4 * i))
        out = {}
        for i in range(nfuncs):
            f = self.u32(funcs + 4 * i)
            if not f or rva <= f < rva + size:
                continue
            out[f"#{base + i}"] = self.base + f
            if i in named:
                out[named[i]] = self.base + f
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--install", default=os.path.join(ROOT, "game/native-install"))
    ap.add_argument("--generated", default=os.path.join(ROOT, "game/generated/war3"))
    ap.add_argument("--tsv", help="write every import with its binding here")
    a = ap.parse_args()

    handlers = set()
    for src in linked_hle_sources():
        with open(os.path.join(X86, src)) as f:
            handlers.update((dll, sym) for dll, sym in HLE_RE.findall(f.read()))
    with open(os.path.join(a.generated, "table.cpp")) as f:
        entries = {int(x, 16) for x in TABLE_RE.findall(f.read())}

    files = ["war3.exe"] + lifted_dlls()
    pes = {normalise_dll(p): Pe(os.path.join(a.install, p.replace("\\", "/"))) for p in files}
    exports = {n: pe.exports() for n, pe in pes.items()}

    rows, bad = [], 0
    counts = collections.defaultdict(collections.Counter)
    for importer, pe in pes.items():
        for dll, sym in pe.imports():
            n = normalise_dll(dll)
            if n in pes:
                va = exports[n].get(sym)
                if va is None:
                    kind, note = "UNRESOLVED", "no such export"
                elif not pes[n].executable(va):
                    kind, note = "lifted", f"{va:08X} data"
                elif va not in entries:
                    kind, note = "UNRESOLVED", f"export {va:08X} is not a lifted entry"
                else:
                    kind, note = "lifted", f"{va:08X}"
                bad += kind == "UNRESOLVED"
            elif (n, sym) in handlers:
                kind, note = "hle", ""
            else:
                kind, note = "stub", "stops if called"
            counts[importer][kind] += 1
            rows.append((importer, n, sym, kind, note))

    kinds = ["lifted", "hle", "stub", "UNRESOLVED"]
    print(f"{'module':16}" + "".join(f"{k:>11}" for k in kinds))
    for importer in pes:
        print(f"{importer:16}" + "".join(f"{counts[importer][k]:>11}" for k in kinds))
    total = collections.Counter()
    for c in counts.values():
        total.update(c)
    print(f"{'total':16}" + "".join(f"{total[k]:>11}" for k in kinds))
    for r in rows:
        if r[3] == "UNRESOLVED":
            print("UNRESOLVED: %s imports %s!%s: %s" % (r[0], r[1], r[2], r[4]))
    if a.tsv:
        with open(a.tsv, "w") as f:
            f.write("importer\tdll\tsymbol\tbinding\tnote\n")
            f.writelines("\t".join(r) + "\n" for r in rows)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
