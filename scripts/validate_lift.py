#!/usr/bin/env python3
"""Structural audit of recomp_lift output against the original modules.

  /opt/homebrew/bin/python3 -I scripts/validate_lift.py --generated game/generated/war3 \
      --module game/native-install/war3.exe game/symbols/war3 \
      --module game/native-install/game.dll game/symbols/game ...

Each symbol dir holds Ghidra's functions.tsv, jumptables.tsv, instructions.tsv and
noncode.tsv (tools/x86recomp/tools/ghidra, scripts/ghidra/ExportInstructions.java)
and pe_symbols.py's exports.tsv / imports.tsv.

HARD checks (exit 1 if any fails), all of which would be fatal at run time:
  - no Unimplemented sites in the generated code;
  - every Ghidra function entry and every exported function is a lifted function;
  - every instruction Ghidra decoded in an executable section was lifted;
  - every relocated pointer into an executable section targets a lifted function,
    a label inside one (switch case, SEH continuation) or explained non-code data.
Reported (classified, not failing): indirect jumps Ghidra left unresolved, by
encoding and by how the lifter emitted them; executable bytes that are not code
(padding, relocated data, unexplained); instructions only the lifter found;
Unreachable / Trap / BadJump / Dispatch sites. Details go to <generated>/validate.txt.
"""
import argparse
import bisect
import collections
import os
import re
import struct
import sys

# A function reFrozen replaces (config/*.manifest, "replace") keeps its translated body as f_<address>_lifted.
FN_RE = re.compile(r"^void f_([0-9A-F]{8})(?:_lifted)?\(::recomp::Ctx& c\) \{")
INSN_RE = re.compile(r"^  \{ // ([0-9A-F]{8}) (\S+)")
LABEL_RE = re.compile(r"^L_([0-9A-F]{8}):")
MARKERS = {
    "unimplemented": re.compile(r"::recomp::Unimplemented\(c, 0x([0-9A-F]{8})u, \"([^\"]*)\"\)"),
    "badjump": re.compile(r"::recomp::BadJump\(c, 0x([0-9A-F]{8})u"),
    "unreachable": re.compile(r"::recomp::Unreachable\(c, 0x([0-9A-F]{8})u"),
    "trap": re.compile(r"::recomp::Trap\(c, 0x([0-9A-F]{8})u"),
}


def read_tsv(path):
    with open(path, encoding="latin-1") as f:
        rows = [l.rstrip("\n").split("\t") for l in f]
    return rows[1:]


class Pe:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        nsec = struct.unpack_from("<H", d, pe + 6)[0]
        opt = pe + 24
        self.base = struct.unpack_from("<I", d, opt + 28)[0]
        reloc_rva, reloc_size = struct.unpack_from("<II", d, opt + 96 + 5 * 8)
        self.sections = []
        for i in range(nsec):
            o = opt + struct.unpack_from("<H", d, pe + 20)[0] + 40 * i
            name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
            vsize, rva, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
            chars = struct.unpack_from("<I", d, o + 36)[0]
            self.sections.append((name, self.base + rva, max(vsize, rsize), rptr, rsize, bool(chars & 0x20000000)))
        self.relocs = []
        if reloc_size:
            pos, end = self.off(self.base + reloc_rva), self.off(self.base + reloc_rva) + reloc_size
            while pos + 8 <= end:
                page, size = struct.unpack_from("<II", d, pos)
                if size < 8:
                    break
                for k in range((size - 8) // 2):
                    e = struct.unpack_from("<H", d, pos + 8 + 2 * k)[0]
                    if e >> 12 == 3:
                        self.relocs.append(self.base + page + (e & 0xFFF))
                pos += size

    def off(self, va):
        for _, start, size, rptr, rsize, _ in self.sections:
            if start <= va < start + size and va - start < rsize:
                return rptr + va - start
        return None

    def u32(self, va):
        o = self.off(va)
        return None if o is None else struct.unpack_from("<I", self.data, o)[0]

    def bytes_at(self, va, n):
        o = self.off(va)
        return b"" if o is None else self.data[o:o + n]

    def exec_ranges(self):
        return [(s, s + size) for _, s, size, _, _, x in self.sections if x]

    def in_exec(self, va):
        return any(a <= va < b for a, b in self.exec_ranges())


def parse_generated(gen_dir):
    fns, insns, labels = set(), {}, set()
    marks = collections.defaultdict(list)
    dispatch = collections.Counter()
    switch_at = set()
    cur = None
    cur_fn = None
    site_fn = {}
    for name in sorted(os.listdir(gen_dir)):
        if not (name.startswith("gen_") and name.endswith(".cpp")):
            continue
        with open(os.path.join(gen_dir, name), encoding="latin-1") as f:
            for line in f:
                m = FN_RE.match(line)
                if m:
                    cur_fn = int(m.group(1), 16)
                    fns.add(cur_fn)
                    continue
                m = LABEL_RE.match(line)
                if m:
                    labels.add(int(m.group(1), 16))
                    continue
                m = INSN_RE.match(line)
                if m:
                    cur = int(m.group(1), 16)
                    insns[cur] = m.group(2)
                    continue
                if "::recomp::" not in line and "switch (" not in line:
                    continue
                if "switch (" in line and cur is not None:
                    switch_at.add(cur)
                if "::recomp::Dispatch(c, " in line and cur is not None:
                    dispatch[insns.get(cur, "?")] += 1
                for k, rx in MARKERS.items():
                    for mm in rx.finditer(line):
                        marks[k].append((int(mm.group(1), 16),) + mm.groups()[1:])
                        site_fn[int(mm.group(1), 16)] = cur_fn
    return fns, insns, labels, marks, dispatch, switch_at, site_fn


def classify_jump(pe, va, iat):
    b = pe.bytes_at(va, 7)
    if len(b) < 2 or b[0] != 0xFF:
        return "not an FF-form jmp"
    modrm = b[1]
    mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
    if reg != 4:
        return "not jmp"
    if mod == 3:
        return "jmp register"
    if mod == 0 and rm == 5:
        target = struct.unpack_from("<I", b, 2)[0]
        return "import thunk (jmp [IAT])" if target in iat else "jmp [absolute]"
    if rm == 4 and len(b) >= 3:
        sib = b[2]
        if (sib >> 6) == 2 and mod == 0 and (sib & 7) == 5:
            return "table jmp [reg*4+table]"
    return "jmp [memory]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", required=True)
    ap.add_argument("--module", nargs=2, action="append", metavar=("PE", "SYMDIR"), required=True)
    ap.add_argument("--unreachable", help="TSV of function entries whose Unimplemented sites are "
                    "documented as unreachable (config/unreachable.tsv); they stay fatal at run time")
    args = ap.parse_args()

    fns, insns, labels, marks, dispatch, switch_at, site_fn = parse_generated(args.generated)
    unreachable = {}
    if args.unreachable:
        unreachable = {int(r[0], 16): r[2] for r in read_tsv(args.unreachable)}
    out = []
    hard = []

    def say(s=""):
        print(s)
        out.append(s)

    say(f"generated: {len(fns)} functions, {len(insns)} instructions, {len(labels)} labels")
    say(f"markers: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(marks.items())))
    say(f"indirect Dispatch sites by mnemonic: {dict(dispatch)}; switch dispatches: {len(switch_at)}")
    documented = [m for m in marks["unimplemented"] if site_fn.get(m[0]) in unreachable]
    live = [m for m in marks["unimplemented"] if site_fn.get(m[0]) not in unreachable]
    say(f"unimplemented sites: {len(live)} reachable, {len(documented)} in "
        f"{len({site_fn[m[0]] for m in documented})} documented-unreachable functions "
        f"({dict(collections.Counter(m[1] for m in documented))})")
    if live:
        hard.append(f"{len(live)} unimplemented sites")
        for va, mn in live[:50]:
            out.append(f"  unimplemented {va:08X} {mn} in f_{site_fn.get(va) or 0:08X}")
    for va, *_ in marks["trap"]:
        out.append(f"  trap {va:08X} {insns.get(va, '?')}")

    for pe_path, sym in args.module:
        pe = Pe(pe_path)
        name = os.path.basename(pe_path)
        say(f"\n== {name} (base {pe.base:#x})")
        exec_r = pe.exec_ranges()

        def mine(va):
            return any(a <= va < b for a, b in exec_r)

        gfn = [r for r in read_tsv(os.path.join(sym, "functions.tsv")) if mine(int(r[0], 16))]
        missing = [r for r in gfn if int(r[0], 16) not in fns]
        say(f"Ghidra functions: {len(gfn)}, not lifted: {len(missing)}")
        if missing:
            hard.append(f"{name}: {len(missing)} Ghidra functions not lifted")
            out += [f"  missing function {r[0]} {r[7] if len(r) > 7 else ''}" for r in missing[:100]]

        exports = [r for r in read_tsv(os.path.join(sym, "exports.tsv")) if r[1] == "func"]
        missing_x = [r for r in exports if int(r[0], 16) not in fns]
        say(f"exported functions: {len(exports)}, not lifted: {len(missing_x)}")
        if missing_x:
            hard.append(f"{name}: {len(missing_x)} exports not lifted")
            out += [f"  missing export {r[0]} {r[2]}" for r in missing_x[:100]]

        gins = {int(r[0], 16): (int(r[1]), r[3]) for r in read_tsv(os.path.join(sym, "instructions.tsv"))}
        mod_insns = {va for va in insns if mine(va)}
        not_lifted = sorted(set(gins) - mod_insns)
        extra = sorted(mod_insns - set(gins))
        code_bytes = sum(n for n, _ in gins.values())
        lifted_bytes = sum(gins[v][0] for v in gins if v in mod_insns)
        say(f"Ghidra instructions: {len(gins)} ({code_bytes} B), lifted: {len(gins) - len(not_lifted)} "
            f"({100 * lifted_bytes / max(code_bytes, 1):.3f}% of code bytes); lifter-only instructions: {len(extra)}")
        out += [f"  lifter-only {va:08X} {insns[va]}" for va in extra[:50]]

        noncode = [(int(a, 16), int(b, 16)) for a, b in read_tsv(os.path.join(sym, "noncode.tsv"))]
        reloc_sites = sorted(pe.relocs)
        reloc_set = set(reloc_sites)
        cats = collections.Counter()
        unexplained = []
        for a, b in noncode:
            data = pe.bytes_at(a, b - a + 1)
            lo = bisect.bisect_left(reloc_sites, a)
            has_reloc = lo < len(reloc_sites) and reloc_sites[lo] <= b
            if data and all(x in (0xCC, 0x90, 0x00) for x in data):
                cats["padding"] += b - a + 1
            elif has_reloc:
                cats["relocated data (pointer/jump tables)"] += b - a + 1
            else:
                cats["unexplained"] += b - a + 1
                unexplained.append((a, b))
        say(f"non-code bytes in executable sections: {dict(cats)}")
        out += [f"  unexplained non-code {a:08X}-{b:08X} ({b - a + 1} B) {pe.bytes_at(a, min(16, b - a + 1)).hex(' ')}"
                for a, b in unexplained]

        def in_noncode(va):
            i = bisect.bisect_right(noncode, (va, 0xFFFFFFFF)) - 1
            return i >= 0 and noncode[i][0] <= va <= noncode[i][1]

        # Reachability evidence for code that was not lifted. Everything the
        # lifter reached is lifted (recursive descent from all entries), so a
        # block is referenced only by a direct branch decoded at a lifted
        # instruction or by a pointer to it. In a relocatable image every
        # stored code address has a base relocation (checked exactly here); in
        # one without, any 4-byte value anywhere in the image that equals an
        # instruction address in the block counts as a reference.
        exec_bytes = [(a, pe.bytes_at(a, b - a)) for a, b in exec_r]
        branch_targets = set()
        for va in mod_insns:
            b = pe.bytes_at(va, 6)
            while b and b[0] in (0x2E, 0x3E):  # branch-hint prefixes
                va, b = va + 1, b[1:]
            if len(b) >= 5 and b[0] in (0xE8, 0xE9):
                branch_targets.add((va + 5 + struct.unpack_from("<i", b, 1)[0]) & 0xFFFFFFFF)
            elif len(b) >= 6 and b[0] == 0x0F and 0x80 <= b[1] <= 0x8F:
                branch_targets.add((va + 6 + struct.unpack_from("<i", b, 2)[0]) & 0xFFFFFFFF)
            elif len(b) >= 2 and (b[0] == 0xEB or 0x70 <= b[0] <= 0x7F or 0xE0 <= b[0] <= 0xE3):
                branch_targets.add((va + 2 + struct.unpack_from("<b", b, 1)[0]) & 0xFFFFFFFF)
        branch_sorted = sorted(branch_targets)
        any_dword = collections.defaultdict(list)  # value -> VAs holding it (no relocations)
        if not pe.relocs:
            file_va = [(rptr, rptr + rsize, start) for _, start, _, rptr, rsize, _ in pe.sections]
            for i in range(len(pe.data) - 3):
                v = struct.unpack_from("<I", pe.data, i)[0]
                at = next((st + i - a for a, b, st in file_va if a <= i < b), None)
                any_dword[v].append(at)
        ginsn_sorted = sorted(gins)
        reloc_by_target = collections.defaultdict(list)
        for site in reloc_sites:
            v = pe.u32(site)
            if v is not None:
                reloc_by_target[v].append(site)
        target_sorted = sorted(reloc_by_target)
        lifted_sorted = sorted(mod_insns)
        def any_in(sorted_list, lo, hi):
            i = bisect.bisect_left(sorted_list, lo)
            return i < len(sorted_list) and sorted_list[i] <= hi

        def site_in_lifted(site):
            """True if site lies inside a lifted instruction (between two
            consecutive lifted instruction starts, at most 15 bytes in)."""
            i = bisect.bisect_right(lifted_sorted, site) - 1
            if i < 0:
                return False
            p = lifted_sorted[i]
            q = lifted_sorted[i + 1] if i + 1 < len(lifted_sorted) else p + 16
            return p <= site < min(q, p + 15)

        memo = {}

        def why_referenced(lo, hi, excluded_sites):
            """None if nothing live refers to [lo, hi], else the evidence. A
            relocated pointer stored in unlifted code counts only if that code
            is itself referenced (a cycle with no way in is dead)."""
            if any_in(lifted_sorted, lo, hi):
                return "contains lifted code"
            i = bisect.bisect_left(branch_sorted, lo)
            if i < len(branch_sorted) and branch_sorted[i] <= hi:
                return f"direct branch from lifted code to {branch_sorted[i]:08X}"
            if any_dword:
                i = bisect.bisect_left(ginsn_sorted, lo)
                values = [lo]
                while i < len(ginsn_sorted) and ginsn_sorted[i] <= hi:
                    values.append(ginsn_sorted[i])
                    i += 1
                for v in values:
                    for at in any_dword.get(v, ()):
                        if at in excluded_sites:
                            continue
                        if at is None or not mine(at) or site_in_lifted(at):
                            where = "a header" if at is None else f"{at:08X}"
                            return f"dword {v:08X} stored at {where} (no relocations)"
                        src = block_start(at)
                        key = (src, at)
                        if key not in memo:
                            memo[key] = None
                            memo[key] = why_referenced(src, at, excluded_sites)
                        if memo[key] is not None:
                            return f"dword {v:08X} at {at:08X} in referenced code ({memo[key]})"
            i = bisect.bisect_left(target_sorted, lo)
            while i < len(target_sorted) and target_sorted[i] <= hi:
                for site in reloc_by_target[target_sorted[i]]:
                    if site in excluded_sites:
                        continue
                    if not mine(site) or site_in_lifted(site):
                        return f"relocated pointer at {site:08X} to {target_sorted[i]:08X}"
                    src = block_start(site)
                    key = (src, site)
                    if key not in memo:
                        memo[key] = None  # in progress: a cycle alone is not a way in
                        memo[key] = why_referenced(src, site, excluded_sites)
                    if memo[key] is not None:
                        return f"relocated pointer at {site:08X} in referenced code ({memo[key]})"
                i += 1
            return None

        def unreferenced(lo, hi, excluded_sites):
            return why_referenced(lo, hi, excluded_sites) is None

        def padding(va):
            b = pe.bytes_at(va, 1)
            return not b or b[0] in (0xCC, 0x90)

        def block_start(va):
            """Start of the unlifted code ending at va: just past the nearest
            lifted instruction before it (or the padding before that), so a
            function that directly follows another without padding is its own
            block."""
            lo = min(a for a, b in exec_r if a <= va < b)
            i = bisect.bisect_left(lifted_sorted, va) - 1
            if i >= 0 and lifted_sorted[i] in gins:
                lo = max(lo, lifted_sorted[i] + gins[lifted_sorted[i]][0])
            start = va
            while start > lo and not padding(start - 1):
                start -= 1
            while start < va and padding(start):
                start += 1
            return start

        dead_tables = {}  # table base -> (slot sites, dispatch block) or None when live

        def table_of(site):
            base = site
            while base - 4 in reloc_set:
                base -= 4
            if base in dead_tables:
                return base, dead_tables[base]
            slots = set()
            x = base
            while x in reloc_set:
                slots.add(x)
                x += 4
            jmps = []
            pat = struct.pack("<I", base)
            for a, blob in exec_bytes:
                i = blob.find(pat)
                while i >= 0:
                    if i >= 3 and blob[i - 3] == 0xFF and blob[i - 2] == 0x24 and (blob[i - 1] & 7) == 5:
                        jmps.append(a + i - 3)
                    i = blob.find(pat, i + 1)
            info = None
            if jmps and all(j not in mod_insns for j in jmps):
                blocks = [(block_start(j), j) for j in jmps]
                if all(unreferenced(lo, j, slots) for lo, j in blocks):
                    info = (slots, blocks)
            dead_tables[base] = info
            return base, info

        rc = collections.Counter()
        bad = []
        dead_notes = set()
        for site in reloc_sites:
            v = pe.u32(site)
            if v is None or not mine(v):
                rc["to data / other"] += 1
            elif v in fns:
                rc["function entry"] += 1
            elif v in labels:
                rc["label in a function (case/continuation)"] += 1
            elif in_noncode(v):
                rc["into non-code data"] += 1
            elif pe.bytes_at(site - 3, 2) == b"\xFF\x24" and (pe.bytes_at(site - 1, 1)[0] & 7) == 5:
                rc["operand of a table jmp (table base, data)"] += 1
            else:
                base, info = table_of(site)
                if info:
                    rc["case target of an unreferenced switch (dead code)"] += 1
                    for lo, j in info[1]:
                        dead_notes.add(f"  dead switch: code {lo:08X}..{j:08X} dispatches through table {base:08X} "
                                       f"({len(info[0])} slots); nothing refers to the block")
                else:
                    rc["UNEXPLAINED code pointer"] += 1
                    bad.append((site, v))
        say(f"relocations: {len(reloc_sites)}: {dict(rc)}")
        out += sorted(dead_notes)
        if bad:
            hard.append(f"{name}: {len(bad)} relocated pointers into code that are neither entries nor labels")
            out += [f"  unexplained reloc at {s:08X} -> {v:08X} ({insns.get(v, 'not an instruction')})" for s, v in bad]

        # Ghidra instructions the lifter did not reach, as contiguous runs.
        dead_slots = set().union(*(info[0] for info in dead_tables.values() if info))
        runs, cur = [], None
        for va in not_lifted:
            if cur and va == cur[1]:
                cur[1] = va + gins[va][0]
                cur[2] += 1
            else:
                cur = [va, va + gins[va][0], 1]
                runs.append(cur)
        nc = collections.Counter()
        live_runs = []
        for lo, hi, count in runs:
            if any_in(reloc_sites, lo, hi - 1):
                nc["table data decoded as code"] += count
            elif site_in_lifted(lo):
                nc["Ghidra decode overlapping lifted instructions"] += count
            else:
                why = why_referenced(lo, hi - 1, dead_slots)
                if why is None:
                    nc["unreferenced code (dead)"] += count
                else:
                    nc["REACHABLE but not lifted"] += count
                    live_runs.append((lo, hi, count, why))
        say(f"Ghidra instructions not lifted: {len(not_lifted)}: {dict(nc)}")
        if live_runs:
            hard.append(f"{name}: {sum(c for _, _, c, _ in live_runs)} reachable Ghidra instructions not lifted")
            out += [f"  reachable, not lifted: {lo:08X}-{hi:08X} ({c} instructions, first {gins[lo][1]}): {why}"
                    for lo, hi, c, why in live_runs]

        iat = {int(r[0], 16) for r in read_tsv(os.path.join(sym, "imports.tsv"))}
        jt = read_tsv(os.path.join(sym, "jumptables.tsv"))
        unresolved = [int(r[0], 16) for r in jt if len(r) < 2 or not r[1]]
        jc = collections.Counter()
        for va in unresolved:
            how = "switch" if va in switch_at else ("Dispatch" if va in insns else "not lifted")
            kind = classify_jump(pe, va, iat)
            jc[f"{kind} -> {how}"] += 1
            if kind.startswith("table") and how != "switch":
                out.append(f"  unresolved table jump {va:08X} emitted as {how}")
        say(f"jump tables: {len(jt) - len(unresolved)} resolved by Ghidra; unresolved computed jumps: "
            f"{len(unresolved)}: {dict(jc)}")

        mod_marks = {k: [m for m in v if mine(m[0])] for k, v in marks.items()}
        say("markers here: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(mod_marks.items())))
        bj_switch = sum(1 for m in mod_marks["badjump"] if m[0] in switch_at)
        say(f"BadJump sites: {len(mod_marks['badjump'])} ({bj_switch} switch defaults, "
            f"{len(mod_marks['badjump']) - bj_switch} other)")
        out += [f"  BadJump (not a switch default) {m[0]:08X} {insns.get(m[0], '?')}"
                for m in mod_marks["badjump"] if m[0] not in switch_at][:100]

    say("\nHARD: " + ("PASS" if not hard else "FAIL"))
    for h in hard:
        say("  " + h)
    with open(os.path.join(args.generated, "validate.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
