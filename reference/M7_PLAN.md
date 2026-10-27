# M7 plan: LAN multiplayer (planning only, 2026-10-27)

Nothing here is implemented. **Approved direction (the owner, 2026-10-27):**
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

- No asynchronous Winsock (`WSAAsyncSelect`, `WSAEventSelect`, overlapped I/O): the game polls with
  `select` and non-blocking sockets (`ioctlsocket(FIONBIO)`), so a direct mapping onto BSD sockets
  fits.
- The game also tries `LoadLibrary("mswsock.dll")` and carries on without it; that stays so.
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
2. **One Mac, two instances (automated, m1-air):** two reFrozen instances with separate data
   folders, the second on another `netgameport`. Scripted input (as M4/M5): host a LAN game,
   discover it, join, chat, start, play a short scripted match, quit. Whether the client finds a
   host on a non-default port is measured first, since discovery is on 6112.
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

## M7b: private servers (separate scope, not started)

Private servers that players run themselves (PvPGN-style): Battle.net-style logon (the `w3l`
logon-hash behaviour), `wininet`, the server's own checks and CD-key handling against it. This is
**network-facing beyond the LAN, touches CD keys** and needs its own plan, the owner's approval for
anything network-facing, and a legal check. It follows M7a only if the owner wants it.

## Order and effort (rough)

1. **Replay cross-check** (determinism), diagnostic only, before any socket code. The Wine
   reference repair is time-boxed within it.
2. Socket layer with unit tests and mutants: 3–5 days.
3. Two instances on one Mac, scripted: 2–4 days.
4. Two Macs, the owner's checklist: 1–2 sessions.
5. Windows interop, a stretch goal (only with a working Wine reference): 2–5 days.
6. Documentation: LAN set-up, permissions, known limitations.

Network code starts only after the cross-check's findings and this order have been reported to the
owner.
