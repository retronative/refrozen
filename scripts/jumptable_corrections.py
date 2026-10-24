#!/usr/bin/env python3
"""Print a module's pinned jumptables.tsv with the case targets that
config/jumptable_corrections.tsv removes (each with the evidence that its
index cannot occur). A correction that names a jump or target the table
does not have is an error.

  jumptable_corrections.py <jumptables.tsv> <corrections.tsv> <module>
"""
import sys


def main():
    tables, fixes, module = sys.argv[1:]
    drop = {}
    for line in open(fixes).read().splitlines()[1:]:
        m, jmp, target = line.split("\t")[:3]
        if m == module:
            drop.setdefault(jmp, set()).add(target)
    lines = open(tables).read().splitlines()
    print(lines[0])
    for line in lines[1:]:
        jmp, targets = line.split("\t")
        targets = targets.split(",")
        gone = drop.pop(jmp, set())
        if not gone <= set(targets):
            sys.exit(f"{module}: jump {jmp} has no case {sorted(gone - set(targets))}")
        print(jmp + "\t" + ",".join(t for t in targets if t not in gone))
    if drop:
        sys.exit(f"{module}: no jump table at {sorted(drop)}")


if __name__ == "__main__":
    main()
