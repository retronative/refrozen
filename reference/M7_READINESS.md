# M7 readiness: reFrozen v0.2.0 Beta — LAN Multiplayer

Status of the v0.2.0 release requirements (`M7_PLAN.md`, "v0.2.0 release target"), with the
evidence behind each. Updated 2026-10-30; main at the merge of patch 0028 (d3291ea). **Published
2026-10-30** ("Published", below).

Labels: **VERIFIED** (tested, evidence kept), **OPEN** (not yet tested), **ISSUE** (found, not
yet resolved).

## Release requirements

| # | Requirement | Status |
|---|---|---|
| 1 | LAN between the M1 and the M5 Mac, both host directions | **VERIFIED** (below), including the host behind a VPN |
| 2 | A 30+ minute DotA multiplayer session without desync | **VERIFIED** on release candidate 2: session A, 33.7 minutes, 20029 of 20029 turns identical ("Release candidate 2") |
| 3 | Map transfer and disconnect recovery | Map transfer **VERIFIED** both directions; disconnect (Wi-Fi off) and recovery **VERIFIED** on release candidate 2: session B ("Release candidate 2") |
| 4 | M4–M6 regression protection | **VERIFIED** on release candidate 2: suites, ctest, M4 3/3, M5 3/3, the full mutation gate (349: 347 KILLED, 2 EQUIVALENT); the one 30-minute M6 run failed with R1's known crash ("Release candidate 2") |
| 5 | Clean install, packaging, signing, human verification | Manual playtest **PASSED** on the patch 0028 build (the owner, 2026-10-29, below); on release candidate 2 the release checks, dmg read-back, signature and clean install in a fresh data folder **VERIFIED** (Gatekeeper rejects: not notarized, as for v0.1.0), and the owner played sessions A and B on it; R6 on the final build: **APPROVED** by the owner on 2026-10-30, with R8, in reply to the release package that asked for both ("Published"); see "Local Network permission" |
| 6 | Website, compatibility docs, release notes | Known issues, changelog, status and compatibility pages and the release-notes draft updated (2026-10-29); the site and the published notes at publication (R8): **VERIFIED** (2026-10-30, "Published") |

**Windows 1.26a interoperability (the owner, 2026-10-29):** outside v0.2.0's verification; the
release notes present it as experimental, invite community reports, and plan official
cross-platform LAN testing for v0.2.1.

**Clean install for v0.2.0 (the owner, 2026-10-29): accepted as for v0.1.0, with a known
limitation.** R5 runs the packaged setup in a fresh data folder on m1-air (a fresh `REFROZEN_DATA`,
from a copy of the dmg carrying the browser-download quarantine attribute; the installers and keys
as a player supplies them, the keys on stdin and checked absent from every log). The test in a
fresh macOS account is **deferred, not run**: a first run that depends on account-level state
(for example an existing permission or a cached Command Line Tools prompt) is not covered.

**R1 for v0.2.0 (the owner's decision, 2026-10-29).** The intermittent crash in long AI matches
ships as a documented known issue and does not block v0.2.0. Its mechanism is identified (probe
8: a sleeping trigger's attacker handle is left without a counted reference and freed while the
trigger waits; `private/r1/NOTES.md`), but no fix is verified. No GetAttacker workaround and no
unverified R1 change goes into v0.2.0; nothing may claim the crash is fixed. The investigation
and the replay-based debugging continue separately for v0.2.1. A crash in a v0.2.0 run is
recorded with its report as this known issue; any other crash fails the run as before.

## Two-Mac sessions (2026-10-28)

All sessions on isolated test installations on both Macs (fresh data folders; the installed
v0.1.0, its data, saves and maps untouched, checked before and after), built from main by the
release pipeline; each Mac built its own game module, byte-identical on both. "No desync" means
the two Macs' replays of the game carry the same seed and identical per-turn sync checksums over
every turn both recorded.

### Smoke test, patch 0024 build

| | M1 hosts, M5 joins | M5 hosts, M1 joins |
|---|---|---|
| Map | Booty Bay | Booty Bay |
| Discovery, join | VERIFIED | VERIFIED after the M5's VPN was disconnected (see the VPN finding) |
| Lobby chat both ways | VERIFIED | VERIFIED |
| In-game chat | unconfirmed (a test-input fault, not the game) | VERIFIED both ways |
| No desync | 3286 of 3286 turns identical | 2433 of 2433 turns identical |
| Leaving | the joiner leaving ends the game for the host; no hang | the host leaving ends it for the joiner; no hang |
| Exit | both clean | both clean |

**VPN finding:** the game's LAN discovery broadcasts (UDP 6112) go to 255.255.255.255, which
macOS routes by the primary network service; with a VPN there, into its tunnel, which refuses
them, so a Mac with a VPN on could join but not host. Fixed by patch 0025.

### VPN-on acceptance with map transfer, patch 0025 build

The M5 had its VPN on throughout (set by the owner; its limited broadcast verifiably refused
before the session). The M1 had none.

| | M5 (VPN on) hosts, M1 joins | M1 hosts, M5 (VPN on) joins |
|---|---|---|
| Discovery | **VERIFIED**: the M1 listed the M5's game (failed before patch 0025) | VERIFIED |
| Map (missing on the joiner) | DotA v6.78c AI 1.4e, 7.3 MB | Castle Fight v1.14b, 0.8 MB |
| Download, join | VERIFIED | VERIFIED |
| SHA-256 of the downloaded map | identical to the host's original | identical to the host's original |
| Lobby chat both ways | VERIFIED | VERIFIED |
| In-game chat | VERIFIED both ways | VERIFIED from the M5; from the M1 not tested (the test input sent to allies only) |
| Play | about 2 minutes | about 2 minutes |
| No desync | 2973 of 2973 turns identical | 2664 of 2664 turns identical |
| Exit | both clean | both clean |
| Network errors | none from the VPN; one failed first join while the permission prompt was open | the same |

## Manual playtest (2026-10-29, patch 0028 build)

The owner's manual session on the M5 Mac (darkBook), on the release-pipeline build of `63a6f33`
(patch 0028, the GetTickCount grid; main `d3291ea` differs from it by a documentation commit
only), kit stamp `63a6f3368d09-b76ce7bf87e6`, the game module built on that Mac
(`9f43945ef567…`, byte-identical to the M1's), no diagnostic probes. Before the launch: the app's
manifest (87 files) and code signature verified, the module stamps checked, and the game started
to the main menu. An isolated test installation (`~/rf-test/m7a-0028`, its own data folder); the
installed v0.1.0, its data, saves and maps untouched. The same build had passed the two-Mac replay
checksum test earlier that day (14:43–15:04; both host directions, 1499 of 1499 and 1588 of 1588
turns identical).

**Result (the owner, 2026-10-29): PASSED.** All 16 items of the owner's checklist passed:
gameplay, graphics, audio, controls, custom maps, save/load on the supported maps, fullscreen and
windowed behaviour, general stability. No crash, freeze or noticeable memory problem during the
session; the game felt playable throughout. Session 17:08–18:17 Bangkok, two launches; the second
(17:17–18:17) ended by a normal quit. Resolution changes (800 × 600, 1920 × 1200, 2940 × 1912,
1600 × 1200) and Ctrl+Cmd+F both ways worked.

Recorded alongside, not counted against the session:
- The first launch ended when the Terror of the Tides campaign was started: the documented
  DirectShow cinematic limitation (`docs/status.md`, the 0.2.0 known issues), unchanged by 0028;
  crash report kept in the test folder.
- Six hang reports were written while the macOS menu bar was open (the watchdog sees the main
  thread inside the menu's tracking loop): not hangs; a follow-up to silence them.
- **ISSUE (follow-up):** the game window cannot be moved to another display; it always opens
  on the primary display. Requirement: it opens on the display that holds the launcher window.
- R1 (the intermittent crash in long AI matches) stays **OPEN**: not seen in this session, but
  reproduced separately on the dedicated test Mac and under investigation (`private/r1/NOTES.md`).

## Release candidate 2 (2026-10-29, `64ef120`)

`release/v0.2.0-rc2` at `64ef120`: main `d3291ea` (patches 0026–0028) with the version setting
(release candidate 1) and these documents. Built by the branch's own release pipeline on m1-air:
`reFrozen-0.2.0.dmg`, SHA-256 `db1ff96c3e839bb7c2450db525f37ceca8ff08ba367fe200cb0a7af550685643`,
kit stamp `64ef1208a752-b76ce7bf87e6`; each Mac built its own game module from the packaged app,
byte-identical on both. No diagnostic probes. Evidence: `~/rf-release/evidence-rc2/` (m1-air) and
`~/rf-test/v020-rc2/evidence/` (darkBook).

### Automated gates (m1-air)

| Gate | Result |
|---|---|
| R4 release checks (`check_release.py`) | ALL PASS (24 checks) |
| R4/R5/R7a: the dmg as downloaded, signature, Gatekeeper, clean install in a fresh data folder | read-back identical, quarantine present, signature valid; Gatekeeper rejects (expected: not notarized); install, cancel and complete build (336 s, progress monotonic) PASS; no CD key in any output or log |
| Suites and ctest | 18 suites PASS; ctest 20/20 |
| Lifts, patches | two lifts identical (`dc7fa7f190d3d9ea`); `validate_lift.py` HARD PASS; patch tree identical to main's |
| M4 | 3/3 PASS |
| M5 | 3/3 PASS |
| M6, one 30-minute run | **FAIL: R1.** A fatal fault about 16 minutes in, with R1's signature (the attacker lookup after a trigger's wait); recorded as the known issue under the owner's R1 decision; crash report kept |
| Full mutation gate | **PASS**: 349 mutants, 347 KILLED, 2 EQUIVALENT (the release gate, below) |

### Mutation gate (2026-10-30, m1-air, run attached, nothing else running)

The release gate as revised by the owner (2026-10-30): `tests/mutate.py --focused --jobs 3`, every
registered mutant, from branch `perf/mutation-gate-release` (local, not merged). The full default
run was stopped after 5 minutes (C3) for this change; it took 2.8 h on release candidate 1.

| | Result |
|---|---|
| Mutants | **349: 347 KILLED, 2 EQUIVALENT** (M3-F9, M7-B6, documented); no survivor, timeout, INVALID or KILLED-OTHER |
| Runtime, measured | cold (no scratch trees, no caches) **2265 s (37.8 min)**; warm 2148 s (35.8 min); release candidate 1's default run 10071 s (2.8 h, 324 mutants) |
| Runtime, estimated | about **27 min cold, 25 min warm** after the change below (the measured runs less R-B1's and R-B3's 670 s; not measured as a whole) |
| Same results as the default runner | all 324 mutants of release candidate 1's default run: the same result; the 26 it did not have (patches 0026–0028's and the gate's own) by the default runner too: 26 KILLED; cold and warm: the same for all 349 |
| Parallel isolation | the parallel-safe tests unmutated in 3 concurrent loops: 207 runs, 0 failed |
| Change after the measured runs | R-B1 and R-B3 (330 s and 340 s: with their check removed the builder lifts and compiles everything) get a lifter that fails at once in their focused cases only. Verified: the unmutated cases pass; R-B1–R-B3 focused KILLED by their expected checks in 2–4 s; R-B1 and R-B3 by the whole test on the real kit (551 s, 563 s) KILLED by the same checks; the other six builder mutants (R-B4–R-B7, R-L1, R-L2) re-run focused with the changed script: KILLED. No other test changed, so no other result was re-run |

**What was tested, and the difference from the release candidate.** The gate ran on a worktree at
`64ef120` with its x86recomp tree `b76ce7b` (the release manifest's; no uncommitted or untracked
file there) and the kit cloned from release candidate 2 (stamp `64ef1208a752-b76ce7bf87e6`), plus
the gate branch's test files: `tests/mutate.py`, `mutants.py`, `test_mutate.py`,
`test_builder_poc.py`, `test_first_run_setup.py`, `scripts/poc/test_errors.sh` and the new
`scripts/poc/lift_fixture.sh`. None of them is in the dmg's manifest or the kit; the runtime, the
lifter and the shipped files are those of release candidate 2. The gate tooling itself is not in
commit `64ef120` and is not merged (the owner's approval).

### darkBook preparation

An isolated test installation (`~/rf-test/v020-rc2`) on each Mac, its own data folder; the
installed v0.1.0, its data, saves and maps untouched. On darkBook: the dmg's SHA-256 matched, the
app's manifest (87 files) and code signature verified, version 0.2.0. Both games ran with
`REFROZEN_STALL=1000`.

### Session A: 30+ minute DotA LAN session

| | darkBook hosts (the owner plays), m1-air joins (scripted, idle) |
|---|---|
| Map | DotA v6.83d AI 1.4e (the owner's choice), 8 Easy computer players |
| Discovery, join | VERIFIED (after the Local Network permission was allowed on m1-air, below) |
| Length | 33.7 minutes of game time on the host (2021163 ms); the joiner stayed to 36.7 minutes, then left |
| No desync | seed `006f62c5` on both; **20029 of 20029 turns identical** |
| Crashes, hang reports | none on either Mac (R1 not seen) |
| Exit | darkBook by the owner's normal quit; m1-air left by F10, End Game, Quit |

Long frames on darkBook during play (38.7 s, 17.4 s, 13.3 s, 6.5 s) were time spent waiting, not
in the game (frames the window did not present; the log shows the window switched to and
from fullscreen during the session); none on m1-air after the map load. Both games log an access
violation caught by the loader in `game.dll`'s detach during `ExitProcess`, as in the earlier
two-Mac sessions' logs: the exit completes (code 0).

### Session B: Wi-Fi disconnect and recovery

Booty Bay, darkBook hosts (the owner plays), m1-air joins (scripted, idle; its game detached from
ssh so that m1-air's outage could not end it). As planned, the owner turned each Mac's Wi-Fi off
for about 30 s and on again during the match; the owner's account below is darkBook's view, not
reported separately per outage.

| | Result |
|---|---|
| During the outage (the owner, on darkBook) | "Waiting for players" with a countdown; when it ran out, the game offered to drop the disconnected player; the owner chose not to and kept waiting |
| Recovery | with Wi-Fi back, the player reconnected and the game resumed normally; nobody was dropped |
| No desync | seed `0002c133` on both; **3460 of 3460 turns identical** (5.8 minutes on the host) |
| Crashes, hang reports | none on either Mac; m1-air's game survived its own outage |
| Afterwards, both host and join | darkBook hosts, m1-air joins: VERIFIED; m1-air hosts, darkBook joins: VERIFIED |

**Result: PASSED** as a disconnect and reconnect recovery test (the owner, 2026-10-29). The
plan's variant (the other Mac drops the player and plays on) was offered by the game and
declined; dropping was not exercised.

### Local Network permission (the new launcher identity)

On each Mac the prompt appeared at the first outgoing connection (the first join), not when
hosting. Until it is allowed a join fails silently: the game list shows the game, Join does
nothing, no message (m1-air: 16 failed connection attempts; darkBook: `connect: errno 65 (No
route to host)`). The prompt's wording on darkBook: *Allow "refrozen" to find devices on local
networks? This will allow the app to discover, connect to, and collect data from devices on your
networks.* [Don't Allow] [Allow]. It names the game process `refrozen` (lower case), not
reFrozen. The wording on m1-air was not captured.

### Preliminary Wine compatibility (smoke test; not Windows verification)

The original Warcraft III 1.26a client under Wine (Wine Devel, an isolated copy of the
installation and prefix) on m1-air; reFrozen release candidate 2 on darkBook, hosting Booty Bay.
About 3 minutes of play.

| | Result |
|---|---|
| Discovery, join, play | worked (the owner: the game was playable) |
| Chat | tested manually by the owner, successfully; both directions of lobby chat not separately confirmed: **unverified** |
| No desync | seed `0007c978` on both; **1582 of 1582 turns identical** (2.7 minutes on the host) |
| Crashes, disconnects | none; no errors in the Wine log |

Preliminary only: one short game, one map, the Wine client joining. Official cross-platform LAN
testing with the Windows client stays planned for v0.2.1; the release notes' experimental wording
is unchanged.

## Published (2026-10-30)

The owner approved v0.2.0 on 2026-10-30, in reply to the release package that asked for the R6 and R8
approvals, chose to publish it that day, and chose "passed, signed off" for M7 on the status page: tag `v0.2.0` on `64ef120` (release
candidate 2), GitHub pre-release "reFrozen 0.2.0 Beta (LAN multiplayer)" with `reFrozen-0.2.0.dmg`
(SHA-256 `db1ff96c3e839bb7c2450db525f37ceca8ff08ba367fe200cb0a7af550685643`) and `SHA256SUMS`,
verified by downloading them back; the website updated and deployed, showing v0.2.0, its checksum
and download. R1 ships as a documented known issue; its fix is planned for v0.2.1.

## Open issues

- **Local Network permission across builds (ISSUE, non-blocking for v0.2.0).** macOS asks the
  game launcher (the app replaces itself with it to start the game), named "refrozen", and
  recorded the answer for its signing identifier and path. The launcher was signed ad hoc, so each
  build had a new identifier: the patch 0025 build asked again on both Macs, and until the prompt
  was answered the first join failed ("Unable to join the specified game"). The launcher now
  carries an embedded Info.plist (reFrozen, the usage description) and a stable signing
  identifier, `org.retronative.refrozen.game`; the app's Info.plist has the description too.
  **Persistence is not verified.** A/B experiment on m1-air (2026-10-28), **inconclusive**: the
  first launch of a build with the new identity showed no prompt, failed no network call and
  hosted a game, and macOS added no permission record for it (the earlier builds each got their
  own); that a second Mac could see its game was not checked, and the update and moved-app cases
  were not run (time-boxed). The ad hoc signature's designated requirement is still the build's
  code hash. The second-Mac check (prompt, discovery) is part of the next planned LAN session;
  the experiment's build and evidence are kept until then.
- **Hang reports during a custom map's load (observed; the M6 watchdog behaviour kept).** When
  Castle Fight loaded in the two-Mac session, both Macs wrote one hang report each (the main
  thread had not pumped window events for 5.3 and 5.5 s), at the same moment; the game then
  continued normally (play, chat, matching replays). Measured on m1-air alone (single player,
  the stall recorder): the first frame drawn after the stall is the map's loading screen, so the
  stall is the map load; the main thread is busy in the game's own loading code (about 4.5 s of
  guest code, 30 ms of waits, negligible file reads), not waiting, and each run wrote at most one
  report. In 12 runs the longest frame took 4.57–4.63 s, under the watchdog's 5 s, with no
  report; the multiplayer load is somewhat longer and crossed it. One earlier run's load frame
  took **17.3 s, unexplained**: a prior visit to the campaign screen and a launch detached from
  the ssh session were ruled out (both 4.6 s). The M6 rule stands: one report during the map
  load, with that frame verified at most 10 s; no fix is proposed.
- **The Frozen Throne campaigns (known issue, non-blocking for v0.2.0).** Reproduced on m1-air
  with RC1 (2026-10-28, a fresh profile, file opens traced): starting Terror of the Tides creates a
  full-screen window whose paint handler calls `FillRect`, a GDI drawing call the runtime stops on
  by design ("GDI drawing is not implemented"); no game file was missing (the movies and campaign
  folders are identical to the reference install). The Founding of Durotar loaded and played its
  opening sequence with no error; the rest of it, and the other campaigns, were not tested. Listed
  in the release notes' known issues and on the compatibility page. Not a v0.2.0 regression: the
  stop dates from M4 (v0.1.0 was not re-run to confirm). **Update (2026-10-29, branch
  `feat/gdi-fill`, merged into main the same day):** with GDI fills implemented (patch 0026) and GetConsoleMode failing
  properly (0027), the campaign gets past its backdrop: the game then creates a DirectShow filter
  graph for the cinematic, which fails here (no DirectShow), prints its own `[FAIL]
  CoCreateInstance(CLSID_FilterGraph ...)` line (now visible in the log) and uses the failed graph
  anyway, so it still stops (a null dereference in its movie player, the same path FEASIBILITY §6
  records for the startup intro). The campaign blocker is cinematic playback, not GDI; the known
  issue's wording is updated accordingly.
- **Map checker tool (tooling).** `scripts/map_check.py` stops with an exception on Castle Fight's
  MPQ header; the game itself lists and plays the map. Not a player-facing issue.
- **Not yet tested:** Windows interoperability (outside v0.2.0; a preliminary Wine smoke test
  on release candidate 2); dropping a disconnected player (offered by the game, declined in
  session B).

## Remaining acceptance plan (prepared 2026-10-28)

**Status 2026-10-29:** item 1 done (the version setting, `release/v0.2.0-rc1`, merged into
`release/v0.2.0-rc2`). Release candidate 2 (main with patches 0026–0028, the version setting and
these documents) is built and verified on m1-air: items 2 and 5's R4, R5 and R7a, see "Release
candidate 2". Sessions A and B need the owner and darkBook. Under the R1 decision above, an R1
crash during session A is recorded as the known issue; whether the session is then repeated is
the owner's call. Sessions A and B PASSED on release candidate 2, with a preliminary Wine smoke
test ("Release candidate 2"); the full mutation gate PASSED (2026-10-30, the release gate).
Left: R6 on the final build, the release notes' verification, the site and the published notes
(requirement 6), and R8 with the owner's approval.

Order: the release candidate first, so the long sessions run on the build that ships.

1. **Version 0.2.0 in the release scripts (needs approval).** `make_release_app.sh`,
   `release_candidate.sh` and `check_release.py` name 0.1.0 (Info.plist, dmg name, manifest,
   check): one version setting for all three, then release candidate 1 of v0.2.0 from a clean
   checkout (R4: release checks, content gate, dmg round trip, checksums, manifest).
2. **Automated regression on that build, on m1-air (no GUI from the owner; CPU-heavy, nothing
   else on m1-air meanwhile; network tests attached):** suites and ctest; the full mutation gate
   (the default runner, the release-level verification; about 2.5 h for 321 mutants); patches
   reapply; two lifts identical; `validate_lift.py` HARD PASS; M4 3/3 and M5 3/3 on the RC's own
   module. M6 on the RC: the owner's choice between v0.1.0's R3 (3–5 runs of 25–30 minutes, then
   one of 65 minutes, about 4 h) and one 30-minute run, the runtime changes since v0.1.0 being the
   network layer.
3. **Session A, two Macs (GUI; needs the owner's approval and darkBook): the 30+ minute DotA
   LAN session**, on the RC build in fresh isolated test folders, combined with checks that do not
   disturb it:
   - the first launch of the new launcher identity on each Mac: whether a Local Network prompt
     appears, its exact wording (name, description), and that each Mac sees the other's game
     (the deferred second-Mac permission and discovery check; the experiment's build A is kept);
   - the multiplayer load frame measured (`REFROZEN_STALL=1000`, low overhead), against the
     watchdog observation above;
   - DotA v6.83d AI (PMV 1.42 EN), on both test installs; the M5 hosts (VPN as the owner chooses),
     the M1 joins; the owner plays a hero; computer players fill the other slots so the match stays
     active while the scripted M1 player idles; at least 30 minutes, then a normal exit;
   - pass: no desync dialog, both replays identical turn for turn over the whole match, both exit
     cleanly, no crash; hang reports only as the M6 rule allows (one, during the map load).
   Known risk: the intermittent crash in long AI matches (v0.1.0's known limitation R1) may occur;
   a crash is recorded with its report and fails the session.
4. **Session B, two Macs: Wi-Fi disconnect and recovery (separate approval; disruptive).** A short
   game (Booty Bay); the owner turns Wi-Fi off on one Mac for about 30 s, then on: the other Mac
   drops the player and plays on, no hang or crash; the disconnected Mac leaves the game cleanly
   and, with Wi-Fi back, both host and join again. Each Mac disconnects once. Turning Wi-Fi off
   on m1-air also cuts its ssh: its scripted input runs on, and the results are read afterwards.
5. **Release verification:** R5 (clean install from a browser download), R6 (the human session),
   R7a/R7b, then the release notes, compatibility pages and site (requirement 6), and R8 with the
   owner's approval.
