# Changelog

All notable changes to reFrozen are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Each published release also has its notes on
[GitHub Releases](https://github.com/retronative/refrozen/releases).

## [Unreleased]: 0.2.0 Beta, LAN multiplayer (in preparation)

Not released. What is planned and how far it is tested are in [docs/status.md](docs/status.md).

### Added

- Mac-to-Mac LAN games: hosting, finding games on the local network, joining, the lobby and chat.
- Custom map download when you join a game whose map you don't have.
- Hosting works with a VPN as the Mac's primary network connection: the game's LAN announcements go
  to each local network.
- The game's launcher carries reFrozen's name and a description of why it uses the local network,
  for macOS's local network permission.
- Installer: a refined progress bar (the light sweeps the whole track, a softer fill and a glowing
  progress edge; it stays still when Reduce Motion is on).

### Known issues

- **Release blocker: the intermittent crash in long AI matches** (as in 0.1.0). It has now also
  occurred on the dedicated test Mac. It is under investigation, and 0.2.0 will not be released
  until it is fixed.
- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game paints a full-screen window with a Windows drawing call (GDI's FillRect) that reFrozen
  does not implement yet. A known compatibility limitation, not blocking 0.2.0; planned for after
  it. The Founding of Durotar starts and its opening sequence plays (the rest of that campaign is
  not verified); the other campaigns are not verified yet.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded** (as in 0.1.0).

## [0.1.0]: 2026-10-27, alpha (offline only)

reFrozen 0.1.0 (alpha, offline), the first public pre-release: Warcraft III: The Frozen Throne 1.26a
recompiled to run natively on Apple silicon Macs with macOS 14 or later, built on your Mac from your
own game files. The full notes, with the requirements and installation steps, are on the
[release page](https://github.com/retronative/refrozen/releases/tag/v0.1.0).

### What works

- Offline custom games: Single Player → Custom Game, including DotA maps you supply and DotA AI maps
  with computer players; choosing a hero by mouse.
- Sound, mouse and keyboard; fullscreen (Ctrl+Cmd+F switches to a window); Retina displays.
- Replays are written, and can be played back in the game.

Verified display configurations, from human playtests on an Apple M5 MacBook (the game's saved
settings): 1600 × 1200 and 2940 × 1912, both 32-bit colour, 60 Hz. No other resolution or display
mode is marked verified.

### Known limitations (alpha)

- **An intermittent crash in long AI matches.** It was seen 6 times in 12 runs on a development Mac
  running other heavy work at the same time. It was not seen in 3 clean 30-minute runs on a dedicated
  test Mac. Its cause is not known and it is not fixed. If it happens to you, please report it with
  the crash report from `~/Library/Application Support/reFrozen/crashes`.
- **A short pause before loading starts** (about half a second) when you select a map and when you
  press Start Game. The game fades its music out there and draws no frames meanwhile. This comes
  from the game itself.
- **The loading bar freezes for a few seconds** while a large map loads: one step of about 4.5 s on
  an M1 and less on newer Macs, plus shorter ones. Audio may stutter during match loading. Gameplay
  itself runs smoothly.
- The scoreboard may show expanded during a match.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded.** Saving works,
  but loading such a save shows "There was an error trying to load the save game. The save file is
  unavailable or corrupted.", and then the game crashes and closes. Your save files are not
  changed. This is specific to that map version, not to DotA AI maps in general: saving and loading
  work on a standard map (Booty Bay) and on DotA v6.78c AI 1.4e. How the original Warcraft III
  client behaves with this map version's saves has not been checked yet.

### Not in this release

LAN and private multiplayer, iCCup and Battle.net. Network menus are present but not supported.

### Checksum

`reFrozen-0.1.0.dmg` SHA-256: `0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`
(tag `v0.1.0`, commit `57a0db5`). The app is ad hoc signed and not notarized: see
[Getting started](docs/getting-started.md) for opening it.

[Unreleased]: https://github.com/retronative/refrozen/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/retronative/refrozen/releases/tag/v0.1.0
