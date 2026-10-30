# Release readiness: reFrozen v0.2.1 (maintenance)

Status of the v0.2.1 release, with the evidence behind each item. Prepared 2026-10-30; release
candidate 2 (`23c28ec`) verified the same day, below.

Labels: **VERIFIED** (tested, evidence kept), **REUSED** (earlier evidence still valid, the reason
given), **OPEN** (not yet done), **OWNER** (the owner's decision or session).

## Scope (the owner, 2026-10-30)

- A focused maintenance release of 0.2.0: the guard for R1, the intermittent crash in long AI
  matches (`src/replaced.cpp`, `config/game.manifest`, the builder's file list), and nothing else
  that changes the shipped app or the game module.
- The related secondary defect (a lookup after a wait that may refer to a different object) stays
  **unresolved** and documented; no change to handle lifetimes or handle allocation. Nothing may
  claim that every R1-related issue is fixed.
- Official verification with the native Windows 1.26a client is deferred to **v0.2.2**. The Wine
  interoperability check of 0.2.0 stays preliminary evidence only.

## Evidence for the R1 guard (before the release candidate)

| Item | Result |
|---|---|
| Regression test | `tests/test_event_data.py`, ALL PASS |
| Mutants | R-E1–R-E10 KILLED; the affected gate after merging main: 63 mutants, all KILLED in the end (61 at once; R-B7 re-expressed, then KILLED; R-G15's timing-dependent check made deterministic, then KILLED); the gate's 21 re-run on the branch tip: KILLED |
| Forced fault (a test map, a test-only build that clears the event's data during the wait) | original code: the fatal fault of R1's reports; with the guard: the trigger gets "no unit" and the game continues |
| Real DotA AI matches (a test-only build: the guard plus logging) | 3 runs on m1-air: two complete 65-minute matches (the guard not needed, no crash), and in the third the guard took effect six times in one frame at about 21.5 minutes, on the attacker lookup of R1's reports; the game went on (two further frame reports at 62.5 and 62.3 frames a second, memory flat, no fatal error). One activation: the guard is exercised, not an endurance result |
| Not exercised in a real match | the damage-event path of the guard (unit test and builds only) |

## Release requirements

| Gate | Status |
|---|---|
| R1 | The known crash: guarded, regression test and mutants KILLED, exercised in a real match. The secondary defect: **unresolved** (Known issues) |
| R2 Regression | **VERIFIED** on release candidate 2: suites, ctest, two identical lifts, `validate_lift.py` HARD PASS (with the corrected audit, below), M4 3/3, M5 3/3, the release mutation gate 362 mutants: 360 KILLED, 2 EQUIVALENT |
| R3 M6 | One 30-minute AI run on release candidate 2: **VERIFIED** clean (no fatal error, no watchdog report). Endurance runs: **OWNER** (to be verified separately) |
| R4 Release candidate | **VERIFIED**: release candidate 2, `23c28ec` |
| R5 Clean install and upgrade | **VERIFIED** in a fresh data folder (the dmg as downloaded) and over a 0.2.0 data folder. The fresh macOS account test: deferred, as for 0.2.0 |
| R6 Human verification | **OWNER** |
| R7a Signing | **VERIFIED**: ad hoc signature valid; Gatekeeper rejects (not notarized), as for 0.2.0 |
| R7b Distribution and notices | **REUSED**: nothing shipped is added or changed except reFrozen's own code |
| R8 Publication | **OWNER** |

## Release candidate 1 (2026-10-30, `580077e`): stopped

Built by the release pipeline on m1-air (`reFrozen-0.2.1.dmg`, SHA-256
`75b8a14b4a99970b9915b3d2916dca14054929eb81e74ec484eb03b662a8da37`). The release checks passed
(24), the dmg read back, its signature verified and the setup installed, but the packaged app's
first-run build failed: a file did not compile. Cause: the release app's kit lacked
`src/replaced.cpp` (`scripts/release/make_release_app.sh` keeps its own list of the kit's files;
only the development kit's script had been changed, and the earlier build checks used that kit).
Fixed in the next commit, with a release check that the kit has every source its builder compiles,
a test that both kit scripts copy every such source, and mutants R-E11 and R-R4 (KILLED). The
remaining gates were not run on release candidate 1; it is not a release candidate for publication.

## Release candidate 2 (2026-10-30, `23c28ec`)

`release/v0.2.1-rc1` at `23c28ec`: main `8fda4e4`, the R1 guard (`fix/r1-event-data`), the version
setting and these documents, and the release kit fix. Built by the release pipeline on m1-air:
`reFrozen-0.2.1.dmg` (12,455,657 bytes), SHA-256
`576a1e5836251c23b9751c7dded8922faf280c81de4f56b0fae820990a47a3cc`, kit stamp
`23c28ec87ebc-b76ce7bf87e6`, x86recomp tree `b76ce7b`. No diagnostic probes. Evidence:
`~/rf-release/evidence-v021-rc2/` (m1-air), run attached (a first attempt lost its ssh session
during the clean install and was restarted on the same build; its evidence is kept as
`evidence-v021-rc2-attempt1`).

| Gate | Result |
|---|---|
| R4 release checks (`check_release.py`) | ALL PASS (25 checks, including the new one: the kit has every source its builder compiles) |
| R4/R5/R7a: the dmg as downloaded, signature, Gatekeeper, clean install in a fresh data folder | read-back identical to the manifest, quarantine present, signature valid; Gatekeeper rejects (expected: not notarized); install, cancel and complete build (375 s, progress monotonic) PASS; no CD key in any output or log; map import and re-import |
| The guard in the shipped kit and in the module the packaged app built | the kit has `src/replaced.cpp` and two `replace` lines; the module has both replacements and both translated bodies |
| Upgrade over a 0.2.0 data folder (a copy of 0.2.0 release candidate 2's) | the 0.2.0 module is detected as needing a build; built (406 s); module stamp `23c28ec87ebc-b76ce7bf87e6`, ready; maps kept; no temporary folder left |
| Suites and ctest | 19 suites PASS; ctest 20/20 |
| Lifts, patches | two lifts identical (`d3424b8985b85b2f`), both replaced helpers kept as translated bodies; patch tree identical to main's (`b76ce7b`) |
| `validate_lift.py` | the pipeline's run reported 2 functions not lifted: the two replaced helpers, whose translated bodies it did not recognise (a defect of the audit, fixed in `5ba97fe`); the corrected audit on the same lift: **HARD PASS**, no function missing (94,560 functions, the 94,558 counted before plus the two translated bodies) |
| M4 | 3/3 PASS |
| M5 | 3/3 PASS |
| M6, one 30-minute run | clean: no fatal error, no watchdog report, pacing median 14.95 ms (drift ×1.03), memory growth ×1.01; marked FAIL only for "no victory announcement" (30 minutes does not reach the end of a match, as for every 30-minute run) |
| Release mutation gate (`--focused --jobs 3`, cold), on `5ba97fe` | **362 mutants: 360 KILLED, 2 EQUIVALENT** (M3-F9, M7-B6); measured **1583 s (26.4 min)**, the first complete measured run after the builder tripwire (estimated about 27 minutes before) |

**After the build commit.** `5ba97fe` changes only `scripts/validate_lift.py` (the audit's function
pattern), `tests/test_event_data.py`, `tests/mutants.py` and `TEST_COVERAGE.md`; none is in the dmg
or the kit, so the artifacts of `23c28ec` stand. The mutation gate ran on `5ba97fe` (it includes
R-E12, the corrected audit's mutant); `test_event_data` passes there.

## Known limitations of v0.2.1

- The secondary defect (a lookup after a wait that may refer to a different object): unresolved,
  rare, does not stop the game. The checks used so far cannot see its likely form (an id reused by
  an event of the same kind), so no observation of it is evidence that it is gone.
- The guard's damage-event path has not been exercised in a real match (unit test and builds only).
- One real-match activation of the guard; endurance is verified separately.
- Whether the original Windows client stops on the same input: not verified.
- Native Windows 1.26a LAN play: not verified (v0.2.2); the Wine check stays preliminary.
- The fresh macOS account test: deferred, as for 0.2.0.
- As in 0.2.0: Terror of the Tides, the DotA v6.83d AI saves, the main display, the load pauses, no
  notarization.

## Reused evidence, and why it is still valid

| Evidence (0.2.0 release candidate 2, `M7_READINESS.md`) | Still valid because |
|---|---|
| Two-Mac LAN sessions (33.7 minutes, Wi-Fi disconnect and recovery, both host directions) | No network, runtime or launcher code changed. The guard changes the game only where it stopped before, identically on every Mac running 0.2.1 |
| x86recomp patches reapply identically | The x86recomp tree (`b76ce7b`) is unchanged |
| The preliminary Wine check with the original client | Kept as preliminary evidence only; official Windows testing in v0.2.2 |
