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

- **An intermittent crash in long AI matches** (as in 0.1.0) is under investigation; 0.2.0 will not
  be released until it is fixed.
- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game paints a full-screen window with a Windows drawing call (GDI's FillRect) that reFrozen
  does not implement yet. A known compatibility limitation, not blocking 0.2.0; planned for after
  it. The Founding of Durotar starts and its opening sequence plays (the rest of that campaign is
  not verified); the other campaigns are not verified yet.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded** (as in 0.1.0).

## [0.1.0]: 2026-10-27, alpha (offline only)

First public pre-release, for Apple silicon Macs with macOS 14 or later.
[Download and release notes](https://github.com/retronative/refrozen/releases/tag/v0.1.0); the
SHA-256 of `reFrozen-0.1.0.dmg` is
`0658af0ad31185e83b5b6af14e6eec7589a6c3a5739b394b759098eff4e46153`.

### Added

- Offline custom games from the Custom Game screen, with maps you supply
- DotA AI maps with computer allies and opponents
- Audio, mouse and keyboard
- Borderless fullscreen and Retina / HiDPI, with the 4:3 interface preserved
- Replays written after each match, and played back in the game

### Known limitations

- **An intermittent crash in long AI matches.** Its cause is not known and it is not fixed. If it
  happens, please report it with the crash report from `~/Library/Application Support/reFrozen/crashes`.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded.** Saving works,
  but loading such a save shows "The save file is unavailable or corrupted", and then the game
  crashes and closes. This is specific to that map version, not to DotA AI maps in general: saving
  and loading work on a standard map (Booty Bay) and on DotA v6.78c AI 1.4e. How the original
  Warcraft III client behaves with this map's saves has not been checked yet.
- **A short pause before loading starts** (about half a second) when you select a map and when you
  press Start Game. This comes from the game itself.
- **The loading bar freezes for a few seconds** while a large map loads, and audio may stutter during
  match loading. Gameplay itself runs smoothly.
- The scoreboard may show expanded during a match.
- reFrozen is not notarized: macOS blocks the first open until you choose **Open Anyway** (see
  [Getting started](docs/getting-started.md)).

### Not part of 0.1.0

- LAN and private multiplayer (M7)
- iCCup online (M8)
- Battle.net

[Unreleased]: https://github.com/retronative/refrozen/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/retronative/refrozen/releases/tag/v0.1.0
