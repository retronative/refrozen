# reFrozen v0.1.0 — release plan (public alpha, offline only)

**Published 2026-10-27, with the user's approval (R8):** tag `v0.1.0` on `57a0db5` (release
candidate 3), GitHub pre-release with `reFrozen-0.1.0.dmg` (SHA-256
`0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`) and `SHA256SUMS`, verified by
downloading them back; the website updated and deployed. Gate outcomes are in the release
checklist below. Release candidates 1 and 2 were not published: release candidate 3 fixed an
intermittent launch failure found in R6 (x86recomp patch 0022) and added the installer UX.

**Approved framework, 2026-10-26.** The user accepted the R1–R8 gates and the revised M6 acceptance
below. Nothing is implemented, tagged, published or pushed by this plan: each implementation step
(the first-run builder prototype included) and the publication itself need the user's separate
approval.

**Changes from the proposal of 2026-10-26:** R1–R8 accepted; M6 acceptance revised in ROADMAP (one
clean 65-minute run, after the crash fix, its regression tests and 3–5 clean 25–30-minute AI
stress runs); ad hoc signing made conditional on a tested browser-download experience on a clean
account; the first-run builder starts with a feasibility proof-of-concept (planning only);
licensing reframed as proportionate checks of what is shipped; public and private documentation
separated (unresolved legal analysis and reverse-engineering detail are kept out of this file).

## What v0.1.0 is
A native Apple silicon build of Warcraft III: The Frozen Throne 1.26a for offline play, produced on
the player's Mac from the player's own game files:
- offline custom games (single player, the Custom Game screen), including DotA maps the player
  supplies and DotA AI maps with computer players (M5, M6);
- audio, mouse and keyboard, native fullscreen and Retina/HiDPI (M5);
- replays written (in-game playback not yet verified).

**Not in v0.1.0:** LAN and private multiplayer (M7), iCCup (M8), Battle.net. Network-facing menus
stay as the game has them and are not supported or tested.

## What is distributed, and what never is
- **Shipped:** the reFrozen application (launcher and runtime, the recompiler and the native
  installer with their helpers, the build inputs from `config/` that hold no game bytes), its
  licences and notices, documentation.
- **Never shipped:** Blizzard binaries or installers, lifted or recompiled game code (source,
  objects or linked, in any form), game assets or MPQs, maps, CD keys, iCCup components, Wine.
- **Consequence:** the game module is lifted and compiled on the player's Mac from the player's own
  installers. reFrozen does not follow a distribution model in which compiled game code is part of
  the download.
- The distribution checks (R4, R7b) are about what the download actually contains.

## Release gates (final)

| Gate | What must be shown | Class |
|---|---|---|
| **R1 Crash correctness** | The intermittent `GetAttacker()` crash: root cause VERIFIED (FEASIBILITY), fix committed, targeted regression test(s) and mutants in the registry, all KILLED. **For the v0.1.0 alpha (approved 2026-10-26):** instead, a documented known limitation with the conditions below; it reopens as a mandatory blocker on any reopening trigger | Mandatory blocker (alpha risk accepted, see below) |
| **R2 Regression** | All suites and ctest pass; the full mutation registry (earlier mutants re-run, AGENTS.md) plus focused new mutants for every changed critical path (R1's fix, local build, first-run setup, packaging checks); two lifts byte-identical; `validate_lift.py` HARD PASS; patches reapply; M4 and M5 acceptance on the release-candidate build | Mandatory |
| **R3 M6** | M6 passed and signed off under the revised acceptance in ROADMAP (R1 met; 3–5 clean 25–30-minute AI stress runs; one clean 65-minute run with every existing pass condition), on the release-candidate build | Mandatory blocker |
| **R4 Release candidate** | One commit built from a clean checkout, packaged, bundle checks, content gate (no PE image, MPQ, map, key-shaped string or lifted-function symbol in any shipped file), dmg round trip, checksums, manifest. The game module the gates use is produced by the packaged app's own first-run builder | Mandatory, automated |
| **R5 Clean install** | A fresh macOS account; the dmg downloaded through a browser (quarantine attribute present); first run from the player's installers to the main menu; scripted negative cases (wrong installer or patch, cancel, low disk); uninstall; disk use and build time recorded | Mandatory blocker |
| **R6 Human session** | 30–60 minutes on the packaged app (checklist below); defects triaged, none open at "blocks play" | Mandatory |
| **R7a Signing** | Ad hoc signing, verified with `codesign --verify --deep --strict`, **only if** R5's browser-download Gatekeeper experience works and the required steps are documented accurately; otherwise Developer ID signing and notarization become mandatory | Mandatory (conditional) |
| **R7b Distribution and notices** | reFrozen's licence chosen and added; third-party redistribution obligations met for everything shipped; notices and attribution in the app; history audit before any public push; unresolved material restrictions recorded as decisions for the user, never as clearance | Mandatory blocker |
| **R8 Publication** | The user's explicit approval, then tag, GitHub pre-release, artifacts verified, website updated | Mandatory |

### Mandatory blockers versus deferred improvements
- **Blockers for v0.1.0:** R1, R3, R5 and R7b, plus R2, R4, R6, R7a and R8 as gates every release
  passes.
- **Deferred (not v0.1.0):** Developer ID signing and notarization (unless R7a's condition fails);
  the hardened runtime; an install test on a second Mac; replay determinism against the original
  client; an update checker; an `--uninstall` command; a bundled compiler toolchain; an
  external-display check; full reproducible-build evidence; tavern hero pick by mouse and replay
  playback as gates (tried in R6, recorded, not blocking unless they block play).

### Current versus final gates

| Earlier plan (G1–G8) | Final |
|---|---|
| G1 manual gameplay QA + G4 Game Mode verification | R6: one 30–60-minute session; Game Mode indicator observed (the system-log check dropped) |
| G2 clean installation | R5, with a browser download and negative cases |
| G3 `.app` packaging + G8 release artifacts | R4: one automated release-candidate run |
| G5 signing and notarization | R7a: ad hoc, conditional on R5; notarization deferred |
| G6 regression and mutation, incl. M4/M5/M6 re-runs | R2 (M4/M5 on the RC build); M6 is R3's own run on the RC build |
| G7 distribution and licensing review | R7b, proportionate to what is shipped |
| G8 tagging and publishing | R8 |
| Prerequisite "M6 passed" (three 65-minute runs, the script's default) | R3 under the revised M6 acceptance |
| — | R1 (new) |

### Approved revisions (the user's decision, 2026-10-26)

Both revisions are in force. Every other gate and every other M6 pass condition is unchanged.
M6 stays NOT PASSED until its revised acceptance (ROADMAP) is actually met.

**1. R1: the intermittent `GetAttacker()` crash as a known alpha limitation.**

*Evidence.*
- Development Mac (Apple M5, 24 GB): 6 crashes in 12 AI runs, about 14–30 minutes into the
  match, the same fault in every recorded case: a null object reached through the game's
  attacker lookup in its trigger code. Three other projects were running on that Mac at the
  same time. Whether the contention contributed is not established.
- Dedicated test Mac (Apple M1, 8 GB, nothing else running): 3 consecutive 30-minute AI runs with
  the crash diagnostics armed, no crash. Shorter runs there (map loading checks, under 5 minutes)
  are not counted.
- Not established: the root cause; whether the crash is a port divergence or happens in the
  original game too; whether it depends on timing or load. It is not fixed and its cause is not
  verified.

*R1 for the alpha (approved).* The crash is accepted as a known limitation of the v0.1.0 alpha, recorded in the
release notes and `docs/status.md`. That text says it was seen on one machine under heavy
concurrent load and not reproduced on a dedicated machine. It says the cause is unknown and asks
players to report it. The diagnostics stay in the runtime, opt-in: the fault report with guest
state, configurable guest-memory dumps and the stall recorder. The private records of the
investigation are kept. Nothing may claim the crash is fixed or its cause verified. R1 reopens
as a mandatory blocker, with its original conditions (root cause VERIFIED, fix, regression tests
and mutants), if any of these happens:
- the crash occurs on the dedicated test machine;
- the crash occurs in human playtesting (R6 or later);
- a reproducible runtime divergence is identified.

*Consequences for M6 and R3.* ROADMAP M6 step 1 reads "the crash fixed, or accepted under the
revised R1". Steps 2 and 3 keep every pass condition. Any crash during an M6 stress or acceptance
run fails that run and reopens R1.

**2. M6: a watchdog policy for map loading.**

*Evidence.* The DotA AI map's load includes one frame of game code (the C runtime's allocator,
about 22 million calls into the runtime) that does not pump window events. With diagnostics off,
it took 5.7 s on the M1 and about 3.4 s on the M5. With the import path optimised (patch 0020),
the M1 took 4.67–4.92 s in five runs. That is under the 5-second watchdog, but by only 0.08 s
at worst, so it is not reliable. Every other condition passed in those runs.

*Policy (approved, implemented in `scripts/m6_accept.sh` with `scripts/m6_watchdog.py`).* The
runtime's watchdog stays at 5 s everywhere, so hang detection in menus and gameplay is unchanged.
An acceptance run may have one watchdog report, and only during the map load: after the frame
that follows the Start Game click (the `start` shot) and before the loading screen's wait for a
key (the `loaded` shot), which precedes the first frame of the match. That load frame must be
verified at most 10 s: the game's own frame-interval report that follows the watchdog report
shows the longest frame. 10 s is twice the M1's measured time, so a load that hangs still fails.
A run fails on any of these:
- a report in the menus or the match;
- a second report (another hang, or the watchdog's repeated dump of the same one);
- a crash;
- phase shots missing or duplicated, so the load can't be identified;
- a load frame that is over 10 s or can't be verified.

Tests: `tests/test_m6_watchdog.py`, mutants M6-W1–M6-W12.

## reCarbon release workflow: what is reused

reCarbon's v0.1.0 release (`../reCarbon`, read-only; tag v0.1.0, a GitHub pre-release) is the
reference for the release mechanics. "Verified" means a script, commit or record in reCarbon shows
it was done; the reFrozen column is a proposal until implemented.

| Practice | Evidence (in `../reCarbon`) | Verified? | reFrozen adaptation |
|---|---|---|---|
| Release-candidate build of one commit from a clean clone, stopping at the first failure; manifest and checksums | `scripts/release_candidate.sh`, `reference/RELEASE_CANDIDATE.md`, commit 5b1b463 | Verified | `scripts/release_candidate.sh`: clone, tools, lift twice and compare, validation, suites, package, checks, content gate, dmg round trip, manifest |
| `.app` assembly (frameworks under `@rpath`, licences in Resources, `Info.plist` with category and version, ad hoc signing of each library then the app) | `scripts/macos/make_app.py` | Verified | Port the structure; bundle id and category chosen at implementation |
| Bundle checks (arm64 only, deployment floor, nothing loaded from outside the app, no build-machine paths, signature, LGPL code not static) | `scripts/macos/check_app.py` | Verified | Port; add "no lifted-function symbol" and "no PE image" |
| Content-safety gate (forbidden names and folders, allowlisted layout with size bounds) | `scripts/macos/rc_manifest.py`, `tests/release_candidate_test.py` | Verified | An allowlist with hashes (reFrozen must ship some headers and tables for the local build) |
| Release dependencies built from checksum-pinned sources, never Homebrew's | `scripts/macos/build_deps.sh` | Verified | Same for SDL3, StormLib and an LGPL-only FFmpeg if linked |
| LGPL libraries as replaceable dylibs, written offer, third-party source archive with checksum | `reference/ALPHA_RELEASE_GATES.md` G2, `THIRD_PARTY_NOTICES.md` | Verified | Same |
| First run: accepted inputs checked by hash, refusal with the reason, cancel leaves nothing partial, data in Application Support | `runtime/install/`, `docs/installation-advanced.md` | Verified | Same, for three installers plus the player's keys, followed by the local build |
| Installer end-to-end check with must-fail cases in a scratch HOME | `scripts/install_check.sh` | Verified | Same shape, with the build as its own cases |
| Clean-account install test | `reference/M8_ACCEPTANCE.md` | Verified (one Mac; test copies had no quarantine attribute) | R5, with a real browser download |
| Ad hoc signing with "Open Anyway" documented, never "turn Gatekeeper off" | `docs/installation.md`, `docs/troubleshooting.md` | Verified (documentation); the browser-download prompt was not exercised | R7a, conditional on R5 |
| No release CI; GitHub pre-release made by hand after approval; release checked with `gh release view` | `.github/workflows/website.yml` (only workflow), `reference/M8_ACCEPTANCE.md` | Verified | Same; the release tests need the player's game files |
| History audit before publishing (counts and paths only) | `../game-port-knowledge/general/process.md` | Verified | Same |
| Human test plan sized to be run | `reference/HUMAN_TEST_PLAN.md` (not run as written) | Lesson | R6 kept short, on the exact release build |
| **Not reused:** a download that contains compiled game code | — | — | reFrozen builds the game module on the player's Mac |

## First-run builder: feasibility proof-of-concept first (planning only)

**Proof of concept done (2026-10-26, on the M1 test Mac; experimental, on `main`):**
`scripts/poc/build_module.sh` lifts the player's installed game and compiles the module with
Apple's Command Line Tools only (clean environment, no Homebrew, no CMake). The launcher built
with `REFROZEN_DYNAMIC_MODULE` loads it at run time after two stamp checks.
- *Compiler:* every M4–M6 build already used Apple clang. The builder's 242 object files are
  byte-identical to the development build's. The generated sources differ only in comment lines,
  because the builder doesn't demangle names, so `llvm-undname` isn't needed.
- *Loading:* M4 acceptance passed 3/3 with the module loaded at run time, and a short AI match
  ran normally. The kit's own launcher, in a clean environment, reaches the game's main loop.
- *Cost on the M1 (8 GB):*
  - about 5.5 minutes (lift 63 s, compile about 4.5 min with 8 jobs);
  - a 105 MB module;
  - 591 MB of disk at peak;
  - 2.3 GB of compiler memory at peak, with no swapping;
  - a 15 MB kit of reFrozen's own files.
- *Errors:* `tests/test_builder_poc.py`, mutants R-B1–R-B6, R-L1 and R-L2. Covered: no
  Command Line Tools, a missing installed file, low disk, a compile failure and a cancel, each
  leaving nothing partial and the previous module in place. Also covered: the launcher refusing
  a module from another build, a missing one and a swapped library.
- *Open:* the kit still links Homebrew's SDL3, glslang and SPIRV-Tools, which packaging must
  bundle. `refrozen` does not link FFmpeg (to confirm at packaging). The first-run setup and
  packaging are not implemented.

The central new work is building the game module on the player's Mac. Before the full builder, a
proof-of-concept answers, with measurements; it is not started without the user's approval:
1. **Compiler:** do Apple's Command Line Tools (free, `xcode-select --install`) compile the
   generated code, and does the result behave identically (M4 and M5 acceptance, a short AI match)?
   Today's builds use Homebrew LLVM.
2. **Loading:** can the shipped runtime load a locally built game module (a dylib from Application
   Support) in one process, ad hoc signed, without library-validation problems? The alternative, a
   locally linked executable, gives two app identities and an unresolved Game Mode question.
3. **Cost:** build time and disk use on the slowest supported Mac; peak memory.
4. **Dependencies:** what the builder needs besides the CLT (lifter, extraction and patch helpers,
   StormLib, headers, the scripts on the CLT's Python instead of Homebrew paths).
5. **Compatibility:** the module and the packaged runtime from the same commit, checked by a stamp
   (reFrozen commit and input hashes); a mismatch rebuilds.
6. **UX and recovery:** progress and an estimate; cancel; failure keeps a log (never the game
   folder or keys); a rebuild into a new folder keeps the previous one until it succeeds.

If the CLT cannot be used, the fallback is a bundled toolchain (LLVM and Python, hundreds of MB and
more licences), deferred unless needed.

## Packaging and installation flow (target design, subject to the proof-of-concept)

**First-run setup implemented (2026-10-27, experimental, not yet packaged):** `app/setup` is a
native SwiftUI app. Its window walks through five steps, and the same core has a command-line mode
for tests (`reFrozen --setup …`):
1. Prerequisites: Apple silicon, macOS 14, free disk, and the Command Line Tools (with Apple's
   installer offered).
2. The player's installers and the 1.26a patch, each checked by SHA-256. Swapped or wrong files
   are refused with the reason.
3. CD keys and the owner's name, validated as the installer validates them. The keys go to the
   installer on standard input only; they never appear in an argument, the output or the logs.
4. Install into a temporary folder, then rename it into place. Then build the game module with
   progress and Cancel.
5. Add a map, then play.

Once setup is complete, later launches go straight to the game (the setup process replaces itself
with the launcher).

The installer step no longer needs Homebrew. The kit carries `native_install.py`, which runs on
Apple's Python 3.9, plus `bnupdate_patch` and StormLib (Homebrew's copy until the release
dependencies are built from pinned sources). An install by the setup is byte-identical to the
reference install: 209 files, 10 s on the M1. A full build through the setup took 5 min 16 s on
the M1.

`scripts/poc/make_setup_app.sh` makes a development `reFrozen.app` (ad hoc signed, no dmg). It is
not the release packaging (R4).

Accepted inputs: only the English (UK) 1.21b installers and the English 1.26a patch, the versions
reFrozen is verified with.

Tests: `tests/test_first_run_setup.py`, mutants R-S1–R-S10.

```
reFrozen.app/Contents/
  Info.plist           bundle id, version 0.1.0, commit, minimum macOS,
                       LSApplicationCategoryType (games), NSHighResolutionCapable
  MacOS/reFrozen       launcher + runtime (SDL3, SDL_GPU on Metal, audio, Win32 HLE)
  MacOS/<helpers>      lifter, MPQ extraction, patcher
  Frameworks/          SDL3, StormLib, LGPL FFmpeg dylibs if linked, runtime libraries
  Resources/builder/   what the local build needs (headers, archives, command list, config, scripts)
  Resources/licenses/  reFrozen's licence, THIRD_PARTY_NOTICES.md, licence texts
```

Player data: `~/Library/Application Support/reFrozen/` (`game/` the installed 1.26a game, maps,
replays; `build/<stamp>/` the built module; `logs/`).

First run on a clean machine:
1. Open the dmg, drag reFrozen to Applications; on first launch follow the steps R5 confirmed (for
   an ad hoc signed app, "Open Anyway" in System Settings, documented with screenshots).
2. Check prerequisites: Apple silicon, the macOS floor, free disk, Command Line Tools (offer Apple's
   installer, then continue).
3. Choose the installers (Reign of Chaos, The Frozen Throne, the 1.26a patch); each checked by hash;
   a mismatch is refused with the reason.
4. The player enters the CD keys and owner name (stored only as the official installer stores them;
   never transmitted or logged).
5. Install and patch into a temporary folder, verify, rename into place.
6. Build the game module with progress; on success rename into place.
7. Optionally copy a player-supplied map into the game's maps folder after a compatibility check.
8. Launch to the main menu. Later launches start here while the stamp matches.

**Fullscreen, Retina, Game Mode:** fullscreen and Retina are done and verified (M5): borderless
fullscreen by default, Ctrl+Cmd+F, the 4:3 picture kept with bars. Game Mode via the app category,
observed in R6 (on in fullscreen, off in a window).

**Uninstall (documented):** quit reFrozen; move `reFrozen.app` to the Bin; delete
`~/Library/Application Support/reFrozen`. That folder holds the player's installed game, including
the encoded CD keys: never attach it or its files to a bug report. The player's original installers
and maps are never modified.

**Versioning, artifacts, rollback:** version 0.1.0 in the build, the commit in `Info.plist`, a
CHANGELOG entry. Artifacts on a GitHub pre-release: the dmg and its SHA-256, `SHA256SUMS`, and the
third-party source archive if LGPL parts ship; checksums verified against the downloaded files.
Tag `v0.1.0` on the final RC commit after approval. Rollback: earlier releases stay available; a
withdrawn release says so and `docs/status.md` is reverted; tags are never moved or deleted.

## Licensing and distribution (proportionate)

Static recompilation and interoperability work sits in a legally complex area; complete certainty
may not be achievable. For an experimental public alpha the checks are practical and focused on
what is shipped:
- **No protected material in the download:** no game code (original or recompiled), assets, maps,
  CD keys or other protected material; enforced by R4's content gate, re-checked in R7b.
- **reFrozen's own licence:** chosen by the user and added before release (none exists yet).
- **Third-party obligations, each verified against what is actually linked and shipped:**

| Component | Expected licence | To verify |
|---|---|---|
| SDL3 | zlib | notice |
| x86recomp (with reFrozen's patches) | MIT (per upstream) | upstream licence file; notice |
| SoftFloat | BSD-3-Clause | licence file; notice |
| StormLib | MIT | licence file; notice |
| FFmpeg (if linked) | LGPL-2.1 from an LGPL-only build | Homebrew's build is GPL and must not ship; replaceable dylibs, source archive, written offer |
| glslang / SPIRV-Cross (if linked at run time) | permissive | notices |
| LLVM, Python (only if bundled) | Apache-2.0 with LLVM exception, PSF | deferred with the bundled toolchain |

- **Notices:** `THIRD_PARTY_NOTICES.md` and licence texts inside the app and in the repository.
- **Trademarks:** no Blizzard or iCCup marks as branding; non-affiliation and the need for the
  player's own copy stated in the app and docs.
- **Claims:** release notes and docs never claim legal clearance. Any material unresolved
  redistribution question is recorded and put to the user as a decision before R8.

## Documentation boundaries

- **Public** (repository docs, website, release notes): verified technical information,
  installation steps and the player-owned game requirements, supported features and known
  limitations, required notices, accurate release and compatibility information.
- **Private** (kept outside the public repository, never pushed): detailed reverse-engineering
  findings beyond what the public docs need, unresolved legal analysis, sensitive implementation
  details, proprietary interface research, anything derived from non-public third-party material.
  Private findings are kept accurately; nothing material is concealed, falsified or destroyed.
- **Before every commit to the public repository:** review the change for accidental disclosure
  (keys, game bytes, private research, legal analysis); committed files stay visible in Git history.
- **Already public:** `reference/` (including FEASIBILITY and `reference/research/`) is tracked and
  has been pushed to the public repository. Whether any of it should be reduced going forward, and
  whether to leave the history as it is, is the user's decision; rewriting public history is not
  part of this plan.

## Website integration
`docs/status.md` stays the single source: the release headline and Releases section switch to the
release, with new front-matter fields for the version, release URL and SHA-256 shown on the
Releases page. `docs/getting-started.md` gets the measured steps, requirements, disk use, build
time, "Open Anyway" (if R7a applies) and uninstall. The site deploys with the approved push.

## Technical blockers, risks and dependencies

| # | Item | Kind |
|---|---|---|
| 1 | `GetAttacker()` crash (6 of 12 AI runs on the development Mac, about 14–30 minutes in; none in 3 runs on the dedicated test Mac; root cause unknown) | Known alpha limitation (R1 as revised); reopens as a blocker on a trigger |
| 2 | The game module built with Apple's Command Line Tools, or a bundled toolchain | Proof of concept passed with the CLT (above); the builder is experimental |
| 3 | The lifted code built and loaded as a separate local module (today linked into one executable) | Proof of concept passed (`REFROZEN_DYNAMIC_MODULE`); first-run setup and packaging still to implement |
| 4 | reFrozen's licence | Blocker (user decision) |
| 5 | Ad hoc signing's browser-download experience on a clean account | Blocker for R7a's ad hoc option |
| 6 | An LGPL-only FFmpeg and source-built, pinned release dependencies | Dependency |
| 7 | Scripts that assume Homebrew paths (Python, StormLib, LLVM tools) | Dependency |
| 8 | Build time and disk use on the slowest supported Mac | Risk |
| 9 | Behaviour differences between compilers | Risk (covered by R2/R3 on the RC build) |
| 10 | Strict stubs reached in new situations | Risk (R6) |
| 11 | Frame stalls during map loading and play (diagnosis in progress, stall recorder) | Known issue unless it blocks play |
| 12 | Scoreboard shown expanded mid-match; replay playback and tavern pick by mouse unverified | Known issues (release notes) |
| 13 | Logs exposing keys or game data | Risk (checked in R4/R5) |

## Effort and critical path
Estimates for one developer with an agent, not measurements:

| Work | Days |
|---|---|
| Proof-of-concept: Apple CLT build and load, cost, dependencies | 1–2 |
| Local game module, default data folder, builder | 5–8 |
| First-run setup (prerequisites, input checks, keys, atomic install, progress, map copy) | 3–5 |
| Pinned release dependencies (SDL3, StormLib, LGPL FFmpeg) | 2–3 |
| Packaging, bundle checks, content gate, RC script (ported from reCarbon), with tests and mutants | 3–5 |
| Notices, source archive, history audit (plus the user's licence decision) | 1–2 |
| R5, R6, documentation and website | 2–3 |
| **Total, excluding R1** | **17–28** |
| R1 root cause, fix and regression tests; R3's stress and acceptance runs | open; in parallel |

**Critical path:** proof-of-concept → local module and builder → first-run setup → packaging and
RC tooling → R4 → R3 and R5 on that RC → R6 → R7a/R7b → R8. R1 is met for the alpha by the
approved risk acceptance, unless a reopening trigger occurs; then its fix must land before R4.

## Recommended minimum requirements
- An Apple silicon Mac; Intel is not supported.
- macOS 14 or later if the release dependencies build for it and the bundle checks pass; otherwise
  the floor found in the proof-of-concept.
- Apple's Command Line Tools (installed from the first run's prompt), unless the proof-of-concept
  leads to a bundled toolchain.
- The player's own Reign of Chaos and The Frozen Throne installers with their CD keys, and the
  official 1.26a English patch; maps supplied by the player.
- Free disk and memory as measured in the proof-of-concept and R5.

## Release checklist
Outcomes for v0.1.0 (release candidate 3, `57a0db5`), recorded 2026-10-27:
- [x] Approvals by the owner, recorded with the gates: R3, R5 (as partial), R6, R7a and R8.
- [x] R1 (alpha, as revised): the intermittent crash in long AI matches is a known limitation in the
      release notes and `docs/status.md`; the opt-in diagnostics are kept; no reopening trigger occurred.
- [x] R3 (2026-10-27, signed off by the owner): 3–5 clean 25–30-minute AI stress runs, then one clean 65-minute run with every pass
      condition (ROADMAP M6), on the RC build; M6 signed off.
- [x] R2: suites, ctest, the full mutation registry on release candidate 1 (239 mutants: 238 killed,
      1 equivalent) and every new mutant of release candidate 3 killed, identical lifts, HARD PASS,
      patches reapply, M4 3/3 and M5 3/3 on release candidate 3; TEST_COVERAGE.md updated.
- [x] R4: release candidate from a clean checkout, offline, against source-built dependencies; all
      release checks pass; the dmg read back; checksums and manifest.
- [x] R5 (accepted as partial by the owner): the packaged setup's install identical to the
      reference, no CD key in logs, cancel and retry, maps, disk and build time recorded; the
      browser download and the Gatekeeper steps on the owner's Mac. Tested in a fresh data folder,
      not a fresh macOS account; uninstall documented, not run on a fresh account.
- [x] R7a (approved by the owner): ad hoc signing, with the Gatekeeper experience tested and the
      exact "Open Anyway" steps documented (macOS 27.0.1).
- [x] R6 (signed off by the owner): the human session; no "blocks play" defect open. A launch
      failure found on release candidate 2 was fixed in release candidate 3 and verified. Saved
      games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded: a known limitation,
      not a gate (saves load on Booty Bay and on DotA v6.78c AI 1.4e; the owner, 2026-10-27).
- [x] R7b: licence file, notices, no LGPL component shipped, history audit, trademarks.
- [x] Disclosure review of the published changes and the release notes (no addresses, keys or private files).
- [x] Release notes: scope, requirements, known issues, non-goals (M7, M8), no legal-clearance claim.
- [x] R8 (approved by the owner): push, tag, GitHub pre-release, artifacts verified, `docs/status.md`
      and the site.

**R6 session (30–60 minutes, packaged app):** launch from Applications; menus; Custom Game with a
player-supplied DotA map; an AI match on the DotA AI map for at least 30 minutes; a hero picked by
mouse if the map allows; audio; hotkeys and chat; Ctrl+Cmd+F both ways with the Game Mode indicator;
minimise and restore; quit and relaunch without a rebuild; replay written.
