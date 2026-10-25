# reFrozen v0.1.0 — release plan (public alpha, offline only)

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
| **R1 Crash correctness** | The intermittent `GetAttacker()` crash: root cause VERIFIED (FEASIBILITY), fix committed, targeted regression test(s) and mutants in the registry, all KILLED | Mandatory blocker |
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
| 1 | `GetAttacker()` crash (5 of 10 AI runs, 14–23 minutes in; root cause unknown, diagnosis in progress) | Blocker (R1) |
| 2 | The game module built with Apple's Command Line Tools, or a bundled toolchain | Blocker (proof-of-concept) |
| 3 | The lifted code built and loaded as a separate local module (today linked into one executable) | Blocker (implementation) |
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
RC tooling → R4 → R3 and R5 on that RC → R6 → R7a/R7b → R8. R1 runs in parallel and must land
before R4; it becomes the critical path if the root cause takes longer than the packaging work.

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
- [ ] Approvals: proof-of-concept start; builder design; signing outcome (R7a); reFrozen's licence;
      any unresolved redistribution question; publication.
- [ ] R1: root cause VERIFIED in FEASIBILITY; fix, regression tests and mutants (KILLED).
- [ ] R3: 3–5 clean 25–30-minute AI stress runs, then one clean 65-minute run with every pass
      condition (ROADMAP M6), on the RC build; M6 signed off.
- [ ] R2: suites, ctest, full mutation registry with focused new mutants, identical lifts, HARD
      PASS, patches reapply, M4 and M5 on the RC build; TEST_COVERAGE.md updated.
- [ ] R4: RC from a clean checkout; every step PASS; content gate; dmg round trip; checksums.
- [ ] R5: fresh account, browser download, first run to the main menu, negative cases, uninstall,
      disk and time recorded; Gatekeeper steps captured exactly.
- [ ] R7a: ad hoc only if R5's Gatekeeper experience worked and is documented; else Developer ID.
- [ ] R6: the human session on the R4 build; no "blocks play" defect open.
- [ ] R7b: licence file, notices, LGPL obligations if any, history audit, trademarks; open
      questions put to the user.
- [ ] Disclosure review of every public document and of the release notes.
- [ ] Release notes: scope, requirements, known issues, non-goals (M7, M8), no legal-clearance claim.
- [ ] R8 on approval: push, tag, GitHub pre-release, artifacts verified, `docs/status.md` and site.

**R6 session (30–60 minutes, packaged app):** launch from Applications; menus; Custom Game with a
player-supplied DotA map; an AI match on the DotA AI map for at least 30 minutes; a hero picked by
mouse if the map allows; audio; hotkeys and chat; Ctrl+Cmd+F both ways with the Game Mode indicator;
minimise and restore; quit and relaunch without a rebuild; replay written.
