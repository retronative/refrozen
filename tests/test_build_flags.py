#!/usr/bin/env python3
"""The runtime's hot host paths are optimised in every build type (M6):

  /opt/homebrew/bin/python3 -I tests/test_build_flags.py

AGENTS.md configures the game as a Debug build. The lifted code is always
-O2; host code that runs per guest call, per draw, per vertex, per pixel or
per sample is too. At -O0 the AI map's load held the main thread 5 s and
7 s (a watchdog report), a third of it in Dispatch's image lookup and a
quarter in the GPU device's and GL context's per-draw buffers; with these
files at -O2, 1.1 s and 3.1 s, the same as a RelWithDebInfo runtime
(FEASIBILITY §13).

Configures REFROZEN_X86RECOMP (default tools/x86recomp) as Debug in a
temporary directory (no build) and checks, in compile_commands.json, that
each file's compile command for its runtime library ends with -O2 as its
last optimisation flag. Prints a FAIL line per failing check.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X86 = os.environ.get("REFROZEN_X86RECOMP", os.path.join(ROOT, "tools", "x86recomp"))

# (source under src/runtime, the library target that builds it, why)
HOT = [
    ("dispatch.cpp", "recomp_runtime", "every indirect call and return"),
    ("gfx/gpu_device.cpp", "recomp_gfx", "every draw, upload and uniform block"),
    ("gfx/format.cpp", "recomp_gfx", "every texel converted"),
    ("gl/context.cpp", "recomp_opengl", "every immediate-mode vertex and matrix"),
    ("x87.cpp", "recomp_x87", "every x87 instruction"),
    ("sse.cpp", "recomp_x87", "every SSE instruction"),
    ("audio/mixer.cpp", "recomp_audio", "every mixed sample"),
    ("audio/source.cpp", "recomp_audio", "every source sample"),
]


def main():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        cfg = subprocess.run(["cmake", "-S", X86, "-B", tmp, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug",
                              "-DRECOMP_LLVM_ROOT=/opt/homebrew/opt/llvm"],
                             capture_output=True, text=True)
        if cfg.returncode:
            print("FAIL x86recomp configures as Debug")
            print(cfg.stdout[-2000:], cfg.stderr[-2000:])
            return 1
        commands = json.load(open(os.path.join(tmp, "compile_commands.json")))
        for src, target, why in HOT:
            path = os.path.join("src", "runtime", src)
            entries = [e for e in commands if e["file"].endswith(path)
                       and f"/{target}.dir/" in e.get("output", e["command"])]
            opt = [a for a in entries[0]["command"].split() if a.startswith("-O")] if entries else []
            ok = bool(opt) and opt[-1] == "-O2"
            print(f"{'ok  ' if ok else 'FAIL'} optimised in a Debug build: {src} ({why}; flags {opt or 'none'})")
            failures += not ok
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
