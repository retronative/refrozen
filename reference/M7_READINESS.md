# M7 readiness: reFrozen v0.2.0 Alpha — LAN Multiplayer

Status of the v0.2.0 release requirements (`M7_PLAN.md`, "v0.2.0 release target"), with the
evidence behind each. Updated 2026-10-28; main at the merge of patch 0025.

Labels: **VERIFIED** (tested, evidence kept), **OPEN** (not yet tested), **ISSUE** (found, not
yet resolved).

## Release requirements

| # | Requirement | Status |
|---|---|---|
| 1 | LAN between the M1 and the M5 Mac, both host directions | **VERIFIED** (below), including the host behind a VPN |
| 2 | A 30+ minute DotA multiplayer session without desync | **OPEN**: separate session, needs the owner's approval |
| 3 | Map transfer and disconnect recovery | Map transfer **VERIFIED** both directions; disconnect (Wi-Fi off) **OPEN** |
| 4 | M4–M6 regression protection | Unit tests and the mutation gate pass on main; M4 3/3 and one M5 match PASS on the patch 0024 runtime; **OPEN** on the final v0.2.0 build |
| 5 | Clean install, packaging, signing, human verification | **OPEN**; see "Local Network permission" |
| 6 | Website, compatibility docs, release notes | **OPEN** |

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

## Open issues

- **Local Network permission asks again after every build (ISSUE).** macOS asks the game
  launcher (the app replaces itself with it to start the game), named "refrozen", and records the
  answer for its signing identifier and path. The launcher is signed ad hoc, so each build has a
  new identifier: the patch 0025 build asked again on both Macs, and until the prompt was
  answered the first join failed ("Unable to join the specified game"). Planned: a stable
  signing identifier and an Info.plist with a usage description embedded in the launcher, tested
  for persistence across rebuilds and moved paths before release.
- **Hang reports during a custom map's load (ISSUE).** When Castle Fight loaded, both Macs wrote
  a hang report (the main thread had not pumped window events for about 5.5 s), at the same
  moment; the game then continued normally (play, chat, matching replays). Under investigation:
  a long load or a real event-loop stall.
- **Map checker tool (tooling).** `scripts/map_check.py` stops with an exception on Castle Fight's
  MPQ header; the game itself lists and plays the map. Not a player-facing issue.
- **Not yet tested:** Wi-Fi-off disconnect recovery; the 30+ minute DotA session; Windows
  interoperability (outside v0.2.0).
