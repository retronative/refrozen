# M7 plan: LAN multiplayer (2026-10-27, updated 2026-10-28)

**Release target (the owner, 2026-10-28): M7a ships as its own release, reFrozen v0.2.0 Alpha —
LAN Multiplayer.** See "v0.2.0 release target" below. Work is on isolated branches; nothing is
merged, pushed, tagged or released without the owner's approval, and the published v0.1.0 stays
unchanged.

**Approved direction (the owner, 2026-10-27):**
1. **M7a targets Mac-to-Mac LAN multiplayer first.**
2. **M7b** (private servers, PvPGN-style) is a separate, deferred scope that needs its own approval.
3. **Windows 1.26a compatibility is a stretch goal**, not a blocker for the first M7a release.
4. **The replay cross-check comes first**, to investigate simulation determinism before any network
   code.
5. The Wine reference on m1-air is repaired if that can be done in a bounded time. Wine
   troubleshooting never blocks M7a.
6. The M7a acceptance requirements below stay: LAN discovery, hosting, joining, the lobby, map
   transfer, 30+ minute DotA play, desync detection, disconnect handling and the macOS permission
   checks.
7. M4–M6 stay protected against regressions.

Public online services, iCCup included, stay M8.

## What the game needs from the runtime

Warcraft III 1.26a's networking is in `game.dll` (and `war3.exe`), on **Winsock 1.1**, imported
by ordinal from `wsock32.dll` (`scripts/import_coverage.py`).

| Already provided (x86recomp `shell_net.cpp`) | Strict stubs today (stop the game when called) |
|---|---|
| `WSAStartup`, `WSACleanup`, `WSAGetLastError`, `gethostname`, `gethostbyname`, `htonl/htons/ntohl/ntohs`, `inet_addr`, `inet_ntoa` | `socket`, `bind`, `listen`, `accept`, `connect`, `closesocket`, `getsockname`, `getpeername`, `ioctlsocket`, `setsockopt`, `select`, `send`, `recv`, `sendto`, `recvfrom` |

- **FALSIFIED (2026-10-28): "no asynchronous Winsock".** Discovery and the lobby's
  connection set-up poll with `select` and non-blocking sockets, but **hosting and joining
  use I/O completion ports** (traced on m1-air, details in private notes):
  - `WSAStartup` reports Winsock 1.1, so the game loads `mswsock.dll` and takes `AcceptEx` and
    `GetAcceptExSockaddrs` from it (with Winsock 2 it would use `ws2_32.dll`'s `WSASend`,
    `WSARecv` and `WSAIoctl` instead; that branch is not used);
  - the listening socket and every connection are associated with one completion port; 16
    `AcceptEx` calls stay pending; each connection's input is an overlapped `ReadFile` on the
    socket, completed through the port; output is a plain `send`;
  - leaving a lobby closes the sockets with operations pending and **waits until every one of
    them has completed**: without cancellation the game hangs (observed).
  - Not used on these paths: `WriteFile` on sockets, `CancelIo`, `PostQueuedCompletionStatus`,
    `TransmitFile`, name lookups.

  This is patch 0024 (below). Patch 0023 (the Winsock 1.1 calls) is implemented and tested.
- The game calls `LoadLibrary("mswsock.dll")`; without it, hosting stops at a call through a
  missing `AcceptEx`.
- `wininet` (`InternetCanonicalizeUrlA`) is Battle.net only: not M7a.

**The LAN protocol (W3GS)**, as the 1.26a client uses it:
- **Discovery:** UDP on port 6112. A searching client broadcasts a search; hosts answer with game
  info and announce or withdraw games themselves.
- **Game:** TCP to the host's game port: the registry's `netgameport`, 6112 by default (present
  in `registry.txt`). Lobby, map transfer (a client lacking the map downloads it from the host)
  and the in-game lockstep actions, with periodic sync checksums. These detect a desync, which ends
  the game for the players out of sync.

## Runtime work (an x86recomp patch, with tests)

A `wsock32` socket layer in the runtime, mapping Winsock 1.1 onto macOS BSD sockets. Each item has
its own tests, written from the Winsock 1.1 specification and Wine's behaviour, not from our code.

1. **Handles.** A guest `SOCKET` is a 32-bit handle, mapped to a host file descriptor in a table;
   `INVALID_SOCKET`/`SOCKET_ERROR` returned as Winsock does.
2. **Structures.** `sockaddr_in` (same layout, guest memory); `timeval` (two 32-bit values);
   **`fd_set` translated both ways.** Winsock's is a count plus an array of up to 64 handles, not
   a bitmask, and `select` ignores its first argument.
3. **Errors.** errno to `WSAGetLastError` codes (`EWOULDBLOCK` to `WSAEWOULDBLOCK` 10035,
   `EINPROGRESS` to `WSAEWOULDBLOCK` on connect, `ECONNRESET` to `WSAECONNRESET`, …), in the
   thread's TEB slot as the existing `WSAGetLastError` reads it.
4. **Options.** `SO_BROADCAST`, `SO_REUSEADDR`, `TCP_NODELAY`, `SO_RCVBUF`/`SO_SNDBUF`, `SO_LINGER`,
   with Winsock's option numbers and value sizes; unknown options a strict error, never a silent
   success.
5. **Non-blocking and connect.** `ioctlsocket(FIONBIO)`, `FIONREAD`; a non-blocking connect
   completing through `select`'s write set, failure through the except set (Winsock's rule).
6. **Broadcast.** `sendto` to 255.255.255.255:6112 with `SO_BROADCAST`; receiving on a socket bound
   to `INADDR_ANY:6112`, from every local interface.
7. **Threads.** Calls can come from the game's network thread: the handle table is thread-safe, and
   blocking calls leave the runtime's import lock, as file I/O does.

8. **Patch 0024: sockets as kernel handles, completion ports and overlapped input.** Socket
   handles share the kernel handle table (0023's own numbering collided with kernel handles);
   sockets can be associated with a completion port; a minimal `mswsock.dll` provides `AcceptEx`
   and `GetAcceptExSockaddrs`; overlapped `ReadFile` on a socket completes through the port, from
   one background thread over all pending socket operations; failed completions carry their status
   (`GetQueuedCompletionStatus` returns FALSE with the operation, distinct from a timeout); closing
   a socket ends each of its pending operations exactly once with `ERROR_OPERATION_ABORTED`, and
   its buffer is never written after that. Expected values from Wine's conformance tests (run
   against Windows). Only the traced paths: no Winsock 2.

## Mac platform work

- **Local Network privacy.** Recent macOS asks the user before an app talks on the local network
  (broadcast and LAN connections). The app needs `NSLocalNetworkUsageDescription` in `Info.plist`.
  The prompt has to come from reFrozen.app, the game process being exec'd from it; to be confirmed
  on macOS 27 with an ad hoc signed app.
- **Firewall.** With the macOS firewall on, hosting a game (incoming TCP) needs the app allowed. To
  be documented, with the exact dialog, as for Gatekeeper.
- **Sleep and network changes.** Wi-Fi changes mid-game must end the game cleanly, as on Windows,
  never hang or crash.

## Compatibility with the original 1.26a LAN

- **Between reFrozen Macs:** the same recompiled code on both sides, so lockstep holds if the
  runtime is deterministic: no host timing or uninitialised memory reaching the simulation.
- **With Windows 1.26a clients (the real goal):** the simulation must be **bit-exact with the
  original x87/SSE code**. The runtime's x87 fast paths (`X87_RUNS`, `X87_DOUBLE`) and any HLE that
  returns a different value than Windows can desync. **This is the main risk, and it is testable
  before any networking exists:**
  - **Replay cross-check:** a replay recorded by the original client (Wine reference) and played in
    reFrozen, and the reverse, compared action by action and at the game's sync checksums. A
    divergence is a desync that LAN would show.
  - A fallback if the fast paths diverge: an exact mode for multiplayer, measured for speed.
- The game's own W3GS packets are produced by the original code, so the protocol is compatible by
  construction. Only the transport is ours.

## Test strategy (two Macs)

1. **Unit tests** of the socket layer (x86recomp tests, as `run_on_stack_test`): `fd_set`
   translation, error mapping, non-blocking connect, broadcast send/receive on loopback, handle
   reuse; with mutants in `tests/mutants.py`.
2. **One Mac, one instance (automated, m1-air).** Two instances on one Mac cannot both bind
   UDP 6112 (OBSERVED: the game does not ask for address reuse on it, so Windows rules refuse the
   second bind), so the automated runs pair one game with a small private test peer: a scripted
   join against a hosted game (join, lobby, leave, disconnect, host cancel), and the game joining a
   replayed host. Bounded runs; no network configuration changes.
3. **Two Macs (m1-air and the owner's darkBook), manual on darkBook:** discovery both ways on the
   same Wi-Fi and on Ethernet, join, a map download, a full DotA match with two players plus
   computer players, at least 30 minutes, then the replays compared. darkBook stays free of
   automated input: a checklist, as in R6.
4. **Against Windows 1.26a (stretch goal):** the Wine reference on m1-air, if its repair succeeds
   within its time box (at present it exits silently). Discovery and joining both ways, then a full
   match.
5. **Diagnostics:** an opt-in packet log (headers and sizes only, never chat text or names), and
   the game's sync checksums written to the log, so a desync is caught at its first turn.

## Acceptance (M7a, LAN)

1. A game hosted on one Mac appears in the other's LAN list within 5 s and disappears when closed;
   both directions.
2. Joining, lobby chat, slot changes and a map download (a map up to 8 MB the client lacks) work;
   the game starts for both.
3. A full DotA AI-map match between two reFrozen Macs, two players plus computer players, at least
   30 minutes, to the score screen on both: **no desync, no disconnect**, no fatal stop, frame
   pacing as in M6. Both replays written and their action streams identical.
4. **Desync detection:** a desync between the two Macs is detected and reported (the game's own
   sync checksums, logged by the runtime from the first turn), never a silent divergence.
5. **Disconnects:** a peer quitting, crashing or losing the network ends or continues the game as the
   original does, with no hang or crash on the other Mac.
6. **macOS permissions:** the Local Network and firewall prompts appear, are documented with their
   exact wording, and LAN works after allowing them.
7. The socket layer's tests and mutants pass; **M4, M5 and M6 do not regress** (their acceptance
   runs on the M7a build; single player untouched).

**Stretch goal (not a blocker for the first M7a release):** against a Windows 1.26a client,
discovery and joining both ways and a full match with no desync. Without it, the release notes say
LAN play is Mac to Mac.

## Risks

| Risk | Effect | Mitigation |
|---|---|---|
| x87/SSE results differ from Windows | Desync against Windows clients | Replay cross-check first; exact x87 mode for multiplayer |
| Non-deterministic runtime behaviour (timing, uninitialised memory) | Desync even between Macs | Sync checksums logged from the first turn; two-instance soak tests |
| Discovery on 6112 with two instances on one Mac | Automated tests cannot discover | Measure early; fall back to two Macs or the Wine reference |
| Local Network privacy with an exec'd, ad hoc signed process | LAN silently blocked | Check on macOS 27 first; `Info.plist` key; documented steps |
| Firewall blocks hosting | Others cannot join | Documented allow steps; joining (outgoing) unaffected |
| Untrusted packets and maps from peers | The original game's parsing bugs | Recompiled code cannot run injected x86 code (an indirect branch outside the lifted code stops the game); guest memory stays in its arena; only play with people you trust (documented) |
| Wine reference broken on m1-air | No automated Windows peer | Repair it (deferred from v0.1.0), or a real Windows PC |
| The intermittent crash in long AI matches | A crash ends a LAN game for everyone | Tracked as before; LAN soak runs add evidence |

## Replay cross-check: findings (2026-10-27, diagnostic only)

- **Replays carry a per-turn state checksum.** Every replay reFrozen records has one `0x22` block
  per time slot (a turn of about 100 ms of game time), holding a 4-byte value that changes every
  turn: 1,193 in M5's 110-second match, 18,098 in a 30-minute M6 match. These are the values a LAN
  game exchanges to detect a desync, so replays are an exact determinism record.
- **The replay viewer does not check them.** A reFrozen replay re-encoded with valid block and
  header checksums plays normally (`-loadfile`). The same replay with one turn's checksum altered
  (turn 200, about 20 s in) also plays on with no message. So watching a replay cannot by itself
  show a desync: the checksum the game computes during playback has to be read out and compared.
- **The game writes the replay only at the end.** `TempReplay.w3g` stays empty during play (the
  replay is kept in memory), so the checksum routine cannot be found from file writes; it needs
  reverse-engineering of the game's code (private notes, as the docs policy requires).
- **No replay recorded by the original client existed.** The Wine reference's `TempReplay.w3g` is
  empty.
- **The Wine reference is repaired.** Wine itself works; the game exited because, launched over
  ssh, Wine's Mac display driver cannot reach the window server ("the graphics driver is missing").
  Launched through LaunchServices (`open` on a small `.app`), the original client runs, so
  replays recorded by the original 1.26a client can now be made on m1-air.
- **Not yet known:** whether reFrozen's simulation is deterministic against itself (record versus
  playback) and against the original client. Both need the playback checksum.

**Checksum probe (2026-10-27, diagnostic only; details in private notes):**
- **The checksum is located.** Each turn the game computes it and sends it as an internal message,
  which the replay records. A diagnostic probe on that send reads exactly the recorded values:
  381 of 381 in a live game, in order.
- **During replay playback the game does not compute the checksum at all.** It is skipped by a
  session flag, and part of its input comes from session data that a playback does not have. So
  the full checksum cannot be compared in playback. The checksum combines a **simulation-state
  value** (one of its inputs, mixed with the game's build number) with session values that change
  during the game.
- **The simulation-state value can be read in both modes**, and it is the meaningful one for
  determinism:
  - **DotA 6.83d AI, about 38 s of game with computer heroes: 381 of 381 turns identical**, live
    against the playback of its own replay;
  - **the M5 match (DotA 6.85oz LoD: hero selection, attack-move, the enemy base destroyed,
    victory): 1,195 of 1,195 turns identical.**
- **Conclusion for M7a (Mac to Mac):** reFrozen's simulation is deterministic against itself on
  m1-air, in record versus playback, through player actions and combat. Nothing so far calls for
  an exact-x87 mode before LAN play between Macs.
- **Not yet measured:**
  - two different Macs (M1 and M5) on the same replay;
  - long matches (30 minutes and more);
  - against the original client. That needs the same value read inside the original client under
    Wine (for example a small logging DLL), since the full checksum cannot be compared from replays
    alone.

## v0.2.0 release target (the owner, 2026-10-28)

**reFrozen v0.2.0 Alpha — LAN Multiplayer**, a standalone release.

**Scope:**
- Native Mac-to-Mac LAN: hosting, discovery, joining and the lobby.
- Multiplayer chat and custom map transfer.
- Stable multiplayer gameplay with desync detection.
- Correct disconnect, cancellation and cleanup behaviour.
- The installer progress-bar refinements already on main (source only since v0.1.0).

**Release requirements:**
1. LAN testing between the M1 and the M5 Mac in both host/client directions.
2. A 30+ minute DotA multiplayer session without desync.
3. Map transfer and disconnect recovery tests.
4. M4–M6 regression protection.
5. Clean installation, packaging, signing and human verification (as R1–R8 for v0.1.0).
6. Website, compatibility documentation and release notes updated.

**Outside v0.2.0:** Windows 1.26a interoperability (the stretch goal above) and M7b private
servers.

**Status (2026-10-28):** the current release status, with the two-Mac results, is in
`M7_READINESS.md`; the notes below record how it was reached.
- Determinism: VERIFIED for reFrozen against itself (record vs playback, a 30-minute match), and
  across Macs (M1 and M5, the same replay).
- Patch 0023 (Winsock 1.1): implemented and tested on its branch, not merged.
- Patch 0024 (completion ports, `AcceptEx`, overlapped socket input): implemented and tested on
  its own branch (`feat/m7a-iocp`), not merged. VERIFIED on m1-air (2026-10-28):
  - `test_win32`: 540 checks pass; mode Q (completion ports) 40 of 40 repeated runs, which
    include 2,000 closes racing a completion; mode N 30 of 30;
  - the mutation gate: all 37 M7 mutants (0023's 14, 0024's 23) KILLED;
  - the patch series 0001–0024 applied to the pinned upstream commit reproduces the tree;
  - one game instance with a private test peer, twice: hosting, three joins (a leave, a
    reset, a player still connected when the host cancels the lobby), and joining a replayed
    host that then disconnects. No fatal stop, no hang, the lobby and LAN screens as expected;
  - M4 acceptance 3 of 3 and one M5 match PASS on the 0024 runtime.
- **Network tests must run attached.** OBSERVED: on m1-air a process left running after its ssh
  session ends gets "No route to host" for every LAN broadcast (loopback unaffected): this caused
  the intermittent broadcast failure seen with patch 0023. `test_win32` now checks this
  precondition first. The mechanism is presumably macOS's local network privacy (HYPOTHESIS),
  which also matters for players: see "Mac platform work".
- Not yet tested: two Macs, map transfer, a full multiplayer match, desync detection.
- Two-Mac session: checklist below; runs on darkBook only with the owner's approval per session.

### Two-Mac session checklist (M1 ↔ M5)

Both Macs on the same LAN, no network settings changed; the same patch 0024 build on both, a fresh
data folder each, `REFROZEN_NET_LOG=1`. If macOS asks for local network access, record the exact
wording, then allow it.
1. M1 hosts Booty Bay: M5 sees it in its LAN list within 5 s, joins; chat both ways; slot changes.
2. M5 leaves the lobby: M1 shows the departure and accepts a new join.
3. M1 cancels the lobby with M5 joined: both return to the LAN screen, no hang.
4. Map transfer: M1 hosts a custom map M5 lacks (under 8 MB); M5 downloads it and joins.
5. A short game (about 2 minutes), then exit normally: both write a replay; compare checksums.
6. Repeat 1–5 with M5 hosting.
7. Disconnect: during a game, turn Wi-Fi off on one Mac for about 30 s: the other drops the player
   and plays on, no hang or crash.
8. Afterwards on both: no `hangs/` dump, no FATAL in the logs; keep the logs and replays.
9. The release requirement's 30+ minute DotA session is a separate, later session.

### Two-Mac smoke test results (2026-10-28, patch 0024 build, main 98b2e48)

Booty Bay, isolated test installs on both Macs (the installed v0.1.0 and its data untouched).
- **M1 hosts, M5 joins: pass.** Discovery, lobby, chat both ways, about 2 minutes of play, clean
  exit; replays: same seed, 3286 of 3286 per-turn checksums identical.
- **M5 hosts, M1 joins: pass once the M5's VPN was disconnected.** Lobby and in-game chat both ways;
  replays 2433 of 2433 identical; the host leaving ends the game for the joiner without a hang.
- **VPN finding:** the game's LAN discovery broadcasts (UDP 6112) go to 255.255.255.255, which macOS
  routes by the primary service; with a VPN there, into its tunnel, which refuses them
  (`EADDRNOTAVAIL`), so a Mac with a VPN on can join but not host. Patch 0025 sends them to each
  local network's broadcast address instead.
- **Local Network permission:** macOS asks once per app identity ("Allow “refrozen” to find devices
  on local networks?"); until allowed, the first broadcast fails with `EHOSTUNREACH`. The prompt
  names the game launcher (the app replaces itself with it), not the app: see the launcher
  identity work.

### VPN-on acceptance with map transfer (patch 0025)

Runs only after patch 0025 passes its mutation gate and the test builds are verified, with the
owner's confirmation immediately before the session. Isolated 0025 test installs on both Macs
(fresh data folders, the existing maps, saves and v0.1.0 installations untouched); no network or
VPN setting is changed by the test.

Setup: the M5 (darkBook) with its VPN on, set by the owner; the M1 (m1-air) without a VPN.
1. The M5 hosts: the M1 sees the game in its LAN list while the M5's VPN is on.
2. The M5 hosts DotA v6.78c AI 1.4e (7.3 MB, in the M5's test install only).
3. The M1 downloads the map: progress shown, the join completes.
4. The downloaded map's SHA-256 equals the host's original.
5. A short game: play, chat both ways (lobby and in game), clean exit; replays compared per turn.
6. Reverse: the M1 hosts a small custom map (one shown as playable in its Create Game list) that
   the M5 lacks; the M5, its VPN still on, downloads it; steps 3–5 again.
7. Kept: both net logs (`REFROZEN_NET_LOG=1`), transfer progress screenshots, both replays and the
   map checksums.

Wi-Fi-off disconnect and the 30+ minute DotA session stay separate, each with its own approval.

## M7b: private servers (separate scope, not started)

Private servers that players run themselves (PvPGN-style): Battle.net-style logon (the `w3l`
logon-hash behaviour), `wininet`, the server's own checks and CD-key handling against it. This is
**network-facing beyond the LAN, touches CD keys** and needs its own plan, the owner's approval for
anything network-facing, and a legal check. It follows M7a only if the owner wants it.

## Order and effort (rough)

1. **Replay cross-check** (determinism), diagnostic only: **done** for reFrozen against itself
   (above), and the Wine reference repaired. **Done since (2026-10-28):** the same replay on the
   M1 and the M5 Mac, 381 of 381 turns identical; a 30-minute match, record against playback,
   33,024 of 33,024 identical.

   Windows comparison (a logging DLL under Wine) stays with the stretch goal.
2. Socket layer with unit tests and mutants: 3–5 days.
3. Two instances on one Mac, scripted: 2–4 days.
4. Two Macs, the owner's checklist: 1–2 sessions.
5. Windows interop, a stretch goal (only with a working Wine reference): 2–5 days.
6. Documentation: LAN set-up, permissions, known limitations.

Network code starts only after the cross-check's findings and this order have been reported to the
owner.
