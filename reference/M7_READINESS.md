# M7 readiness: reFrozen v0.2.0 Alpha — LAN Multiplayer

Status of the v0.2.0 release requirements (`M7_PLAN.md`, "v0.2.0 release target"), with the
evidence behind each. Updated 2026-10-29; main at the merge of patch 0028 (d3291ea).

Labels: **VERIFIED** (tested, evidence kept), **OPEN** (not yet tested), **ISSUE** (found, not
yet resolved).

## Release requirements

| # | Requirement | Status |
|---|---|---|
| 1 | LAN between the M1 and the M5 Mac, both host directions | **VERIFIED** (below), including the host behind a VPN |
| 2 | A 30+ minute DotA multiplayer session without desync | **OPEN**: separate session, needs the owner's approval |
| 3 | Map transfer and disconnect recovery | Map transfer **VERIFIED** both directions; disconnect (Wi-Fi off) **OPEN** |
| 4 | M4–M6 regression protection | Unit tests and the mutation gate pass on main; M4 3/3 and one M5 match PASS on the patch 0024 runtime; on release candidate 2: see "Release candidate 2" |
| 5 | Clean install, packaging, signing, human verification | Manual playtest **PASSED** on the patch 0028 build (the owner, 2026-10-29, below); R6 on the final v0.2.0 build, clean install, packaging and signing **OPEN**; see "Local Network permission" |
| 6 | Website, compatibility docs, release notes | Known issues, changelog, status and compatibility pages and the release-notes draft updated (2026-10-29); the site and the published notes at publication (R8): **OPEN** |

**Windows 1.26a interoperability (the owner, 2026-10-29):** outside v0.2.0's verification; the
release notes present it as experimental, invite community reports, and plan official
cross-platform LAN testing for v0.2.1.

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
- **Not yet tested:** Wi-Fi-off disconnect recovery; the 30+ minute DotA session; Windows
  interoperability (outside v0.2.0).

## Remaining acceptance plan (prepared 2026-10-28)

**Status 2026-10-29:** item 1 done (the version setting, `release/v0.2.0-rc1`, merged into
`release/v0.2.0-rc2`). Release candidate 2 (main with patches 0026–0028, the version setting and
these documents) is built and verified on m1-air: items 2 and 5's R4, R5 and R7a, see "Release
candidate 2". Sessions A and B need the owner and darkBook. Under the R1 decision above, an R1
crash during session A is recorded as the known issue; whether the session is then repeated is
the owner's call.

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
