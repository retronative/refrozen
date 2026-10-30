# Release readiness: reFrozen v0.2.1 (maintenance)

Status of the v0.2.1 release, with the evidence behind each item. Prepared 2026-10-30.

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
| R2 Regression | **OPEN** on the release candidate: suites, ctest, two lifts, `validate_lift.py`, M4, M5, the release mutation gate (`--focused --jobs 3`, every registered mutant) |
| R3 M6 | One 30-minute AI run on the release candidate (as for 0.2.0): **OPEN**. Endurance runs: **OWNER** (to be verified separately) |
| R4 Release candidate | **OPEN** |
| R5 Clean install and upgrade | **OPEN**: a clean install in a fresh data folder, and an upgrade over a 0.2.0 data folder |
| R6 Human verification | **OWNER** |
| R7a Signing | **OPEN** (ad hoc, as for 0.2.0) |
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

## Reused evidence, and why it is still valid

| Evidence (0.2.0 release candidate 2, `M7_READINESS.md`) | Still valid because |
|---|---|
| Two-Mac LAN sessions (33.7 minutes, Wi-Fi disconnect and recovery, both host directions) | No network, runtime or launcher code changed. The guard changes the game only where it stopped before, identically on every Mac running 0.2.1 |
| x86recomp patches reapply identically | The x86recomp tree (`b76ce7b`) is unchanged |
| The preliminary Wine check with the original client | Kept as preliminary evidence only; official Windows testing in v0.2.2 |
