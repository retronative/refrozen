# Open-source Warcraft III engine reimplementations and supporting libraries (as of 2026-10-24)

Method note: Repo metadata (license, language, stars, last push, last commit) comes from the GitHub API, queried 2026-10-24. "pushed_at" means the last push to any branch. Hive Workshop pages returned HTTP 403 to the fetcher, so claims that rest only on Hive come from search snippets and are marked that way. Nothing here was built or run locally. Every "can it play DotA" statement is what the project says about itself.

## Engine reimplementations: status, license, and which can load or simulate DotA

### Takeaway
As of late October 2026, three engines are actively pushing DotA forward. **None of them plays DotA 6.83 at retail fidelity, and none can join a real 1.26a game.**
- **OpenWar3** (elevchyt, TypeScript, MIT) is the furthest along on DotA. On 2026-10-23 it showed creep waves walking all three lanes, hero skills and the scoreboard working, but on **DotA v6.77b AI**, and it **requires the user's install to be TFT 1.30.4** (it refuses pre-1.30 MPQ installs).
- **OpenRealm / openwarcraft3** (corepunch, C, MIT) uses the user's own War3.mpq/War3x.mpq and builds on macOS (SDL2, arm64-capable from source). Its own doc says "cannot yet *play*" DotA 6.83d. It parses the 4.1 MiB script and enters `main()`, and custom-ability and HUD work is ongoing.
- **Warsmash** (Retera, Java/LibGDX, AGPL-3.0) is the most mature general engine, with 1.22–1.28 MPQ support and its own JASS VM. I found no evidence that it plays DotA.

### Cited Findings

**OpenWar3 (elevchyt/openwar3)**
- "A recreation of the Warcraft III engine in TypeScript. Ships zero Blizzard assets — uses your own install at runtime." License MIT. — [README](https://github.com/elevchyt/openwar3)
- Repo created 2026-07-01. 15 stars. Last release v0.3.61 on 2026-10-23, with commits on 2026-10-23 adding "the stock abilities custom maps build hero skills on: Magic Leash, Spellbook…". — [GitHub API / repo](https://github.com/elevchyt/openwar3)
- **Version gate:** "The Frozen Throne 1.30.4 is required, and the game checks it… Pre-1.30 MPQ-era installs are older than that build by construction and are not accepted." The reason given: every stat and ability is read from each player's install, so a mismatch would desync host and client tables. — [README](https://github.com/elevchyt/openwar3)
- Platforms: browser, an Electron desktop app, Linux AppImage, Windows installer, and `pnpm dist:mac` (.dmg). macOS auto-update needs an Apple signature; unsigned builds install by hand. — [README](https://github.com/elevchyt/openwar3)
- **DotA progress:** Issue #224 (closed 2026-10-23) is titled "second round of DotA v6.77b AI (Fun) fixes". Fixes:
  - Timer-expiry semantics. `TimerGetRemaining` returned -0.0067 and so creep waves never spawned.
  - `.tga`/extension-less icon paths now resolve to `.blp`.
  - `Aamk` Attribute Bonus is now learnable.
  - The multiboard can be expanded.
  - The opening camera uses the script's start location, because DotA's w3i is truncated by its protector.
  - Verified in headless Chrome: "The first wave spawns at about 2:00 game time and walks all three lanes", "Drow's learn list shows all five skills."
  - Still open: a raw `TRIGSTR_50016` key shows, and tavern roofs render black.
  — [openwar3 #224](https://github.com/elevchyt/openwar3/issues/224)
- Native-coverage baseline on 2026-09-21: "136 natives, 5019 call sites" missing across its map corpus. A missing native "is logged once and returns a safe default, so the map RUNS and that one system silently does nothing." Coverage work goes in passes, e.g. hero attributes (452 sites) and widget life / `UnitDamageTarget` (196). — [docs/map-compatibility.md](https://github.com/elevchyt/openwar3/blob/main/docs/map-compatibility.md)
- An unimplemented boolean native returns FALSE, which "inverts" behaviour: "DotA gates most of its targeting on `IsUnitVisible`… all 153 of those calls said 'nobody has eyes on it'". Hashtable Save/Load handle pairs total "~450 call sites in DotA alone". — [docs/map-compatibility.md](https://github.com/elevchyt/openwar3/blob/main/docs/map-compatibility.md)
- Protected maps: DotA's w3i "has been truncated by a map protector (each ends in a lone `0xff` mid-structure)". The fix is partial-tolerant w3i parsing. — [docs/map-compatibility.md](https://github.com/elevchyt/openwar3/blob/main/docs/map-compatibility.md)
- **Multiplayer:** host-authoritative ("One machine owns truth; that machine is the host"), with delta snapshots at about 10–20 Hz over LAN/WebRTC/relay. "Determinism: Not required for sync — only one machine simulates." — [docs/multiplayer.md](https://github.com/elevchyt/openwar3/blob/main/docs/multiplayer.md)

**OpenRealm / openwarcraft3 (corepunch/open-realm)**
- "Open-source, Quake-style engine and compatibility project for Blizzard-era game data. Warcraft III is the primary playable target and runs on Windows, Linux, macOS, and iPad." C, MIT. Build with `brew install sdl2; make build`, plus optional FFmpeg for movies and music. Run as `openwarcraft3 -data "/path/to/Warcraft III"`, which scans for top-level MPQs. The iPad build uses War3.mpq/War3Local.mpq/War3x.mpq/War3xLocal.mpq. — [README](https://github.com/corepunch/open-realm)
- 355 stars and 50 forks. Created 2023-05-13. Last commit 2026-10-23. Latest release v0.0.11-alpha (2026-10-04) ships `openwarcraft3-macos-x64.tar.gz` and no prebuilt arm64 mac binary (an arm64 build would come from source). — [releases](https://github.com/corepunch/open-realm/releases)
- Architecture: "id-Tech (Quake 2 / Quake 3) inspired… strictly separates authoritative server simulation, client presentation". Networking is UDP with entity delta snapshots (`svc_packetentities`), which is client/server rather than WC3 lockstep. — [ARCHITECTURE.md](https://github.com/corepunch/open-realm/blob/main/ARCHITECTURE.md)
- **DotA status, from the project's own doc:** "OpenRealm cannot yet *play* Defense of the Ancients (custom `A00Y` abilities, HUD draw)." It now "parses the 4.1 MiB CR-only Vexorian script and enters `main()`". The target map is "DotA v6.83dAI PMV 1.42 EN". — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)
- Facts about DotA 6.83d gathered by that project, useful for any engine:
  - The script is `scripts\war3map.j` (4,164,351 bytes, 132,869 lines, 5,708 functions). There is no root `war3map.j`.
  - `war3map.w3a` has 1,364 original-table ability modifications.
  - Heroes, items and abilities live in map-local `Units\Campaign*Func.txt` and `Item*.txt`.
  - `war3mapMisc.txt` sets `MaxHeroLevel=25` and `MaxUnitSpeed=522`.
  - The MPQ uses `wSectorSizeShift=15` (16 MiB sectors), and its `(listfile)` is fake.
  - The script uses 525 natives. 137 were initially unregistered, 53 of them hashtable natives with 8,692 refs.
  - "This map's live state is hashtables, not game cache."
  — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)
- Tracking issue #431 (2026-09-18) said "We are not close." Follow-ups #434–#448 were closed on 2026-09-18:
  - Hashtables (#437) and minified-JASS parsing (#441).
  - MPQ sector sizes above 64 KiB (#435).
  - DotA HUD natives: multiboard and texttag (#434).
  - Shop and combat natives (#436).
  - Custom rawcode to base-mechanic inference (#448). "custom JASS-triggered behavior remains follow-up".
  — [open-realm #431](https://github.com/corepunch/open-realm/issues/431), [#448](https://github.com/corepunch/open-realm/issues/448)
- The doc warns: "Do not treat a later `completed` audit row as playable DotA. Spawn, shops, items, and win conditions are all script-driven." Also: "`main()` then spends a long time filling arrays… before returning to the frame loop." — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)

**wc3-wasm (rgnv/wc3-wasm)**: a WebAssembly/WebSocket port of OpenRealm with 29 patches.
- Claims melee, all RoC+TFT campaigns, and multiplayer through a WebSocket⇄UDP bridge. "JASS coverage completed for campaign content (70 previously-missing natives…)". Protected maps open.
- Uses Reforged-era CASC data that it extracts itself, not 1.26a MPQs.
- Created 2026-10-16, 2 stars, licence NOASSERTION (README says MIT). I saw no DotA claim.
— [README](https://github.com/rgnv/wc3-wasm)

**Warsmash (Retera/WarsmashModEngine)**
- "A Warcraft III emulator made using LibGDX game engine." Assets are not included. AGPL-3.0, switched from MIT because a dependency is GPL. Java 17. — [README](https://github.com/Retera/WarsmashModEngine)
- Supports TFT patches 1.22–1.28 with MPQ files plus a Warsmash "resources" folder (requires `MaxPlayers=16`). Also supports 1.29, 1.30/1.31 (extracted folders), and 1.32.10+ CASC. It does **not** support 1.33+ models. — [README](https://github.com/Retera/WarsmashModEngine)
- Activity:
  - 585 stars, pushed_at 2026-10-05.
  - The `main` branch's last commit is 2025-12-09.
  - The active feature branch `thirdperson-ek-big-andkal-merge-e2-ai-v` last committed on 2026-09-11.
  - There is an `arm64-testing` branch (last 2023-09-05) and a `run-on-rpi5` branch (2024-09-29).
  — [GitHub API branches](https://github.com/Retera/WarsmashModEngine/branches)
- Architecture:
  - Rendering code is transcribed from mdx-m3-viewer, and terrain from HiveWE.
  - BLP uses DrSuperGood's blp-iio-plugin (GPL-3.0), and MPQ uses DrSuperGood's parser.
  - Object-editor data comes from a port of PitzerMike's Grimoire/Widgetizer parsers.
  - There is its own ANTLR-based `jassparser` module with an instruction-based interpreter (`com/etheller/interpreter/ast/execution/instruction/*`).
  - There is a `server` module ("uberserver" TCP lobby/game server), and the client sends orders (`WarsmashClientSendingOrderListener`).
  — [README](https://github.com/Retera/WarsmashModEngine), [source tree](https://github.com/Retera/WarsmashModEngine/tree/main/server/src/com/etheller/warsmash/networking/uberserver)
- The only DotA-related issue: #99 (2026-04-29), "Hero units lose last-hit credit to allied units in same tick due to update ordering". A user was building "an AI training environment for Dota-style last-hitting using Warsmash", using Warsmash's own units, not the DotA map. — [Warsmash #99](https://github.com/Retera/WarsmashModEngine/issues/99)
- Hive Workshop describes it as a mostly "clean-room engineered" rewrite, "a platform for prototype strange spinoffs of the Warcraft III concept". Hive media shows a "This Winter in Warsmash" thread with single-player posts from Dec 2025 to Jan 2026. These come from search snippets, because the page returned 403. — [Hive: overview](https://www.hiveworkshop.com/threads/overview-and-setup.331776), [Hive: This Winter in Warsmash](https://www.hiveworkshop.com/threads/this-winter-in-warsmash.369535/)
- A web search found no source saying DotA is playable on Warsmash. — (absence noted. See Gaps.)

**Other or smaller projects**
- `LiGameAcademy/godot_warcraft3`: a Godot 4.7.2 plus C# (`rts_kernel_cs`) re-creation. MIT, 13 stars, last commit 2026-10-14. It needs the user's classic War3.mpq/War3x.mpq. Its README says the kernel is "still in early development" and the smoke test is a town hall plus peasants moving on Echo Isles. No JASS or DotA. — [README](https://github.com/LiGameAcademy/godot_warcraft3)
- `BMoradi1/foc-web`: a browser port of a single community map ("Fight of Characters"). MIT, last commit 2026-09-14. — [repo](https://github.com/BMoradi1/foc-web)
- `Grimgrents2/WarsmashModEngine`: an MIT-era fork, last push 2022-09-06 (stale). `Ev3nt/MM-Engine`: "modding platform for Warcraft III", C++, last push 2021-11 (stale, and it is an extender for the original game, not a reimplementation). — [GitHub search](https://github.com/Grimgrents2/WarsmashModEngine), [MM-Engine](https://github.com/Ev3nt/MM-Engine)
- `seoup/wc3-moba` (created 2026-09) is a mirror or fork that uses the OpenRealm description, with 0 stars. — [repo](https://github.com/seoup/wc3-moba)
- Searches for "openwarcraft3", "wc3 engine rust" and "warcraft3 godot" found no other Rust or C++ engine reimplementation beyond those listed. — GitHub search API, 2026-10-24

**Viewers and editors (rendering and format references, not game engines)**
- `flowtsohg/mdx-m3-viewer`: WebGL viewer for MDX/M3 (and W3X maps). TypeScript, MIT, 178 stars, last push 2025-08-27 (slowing). Warsmash's renderer descends from it. — [repo](https://github.com/flowtsohg/mdx-m3-viewer)
- `stijnherfst/HiveWE`: "A Warcraft III world editor". C++, AGPL-3.0, 486 stars, last push 2026-10-11 (active). Warsmash's terrain rendering is transcribed from it. — [repo](https://github.com/stijnherfst/HiveWE)
- `Retera/ReterasModelStudio`: "Retera's Java WC3 libraries" (model editor). MIT, last push 2026-09-23. — [repo](https://github.com/Retera/ReterasModelStudio)
- `d07RiV/wc3data`: C, last push 2023-01 (stale). Warsmash took its water/splat/shadow enhancements from it. — [repo](https://github.com/d07RiV/wc3data)

### Inferences
- For DotA 6.83 specifically, OpenWar3 is the furthest along on gameplay (lanes, heroes, shops), but its hard requirement for 1.30.4 data conflicts with a 1.26a-based project. Using it means also owning 1.30.4 assets, or forking out the version gate. That would be legal and technical work, and the effect on the 1.24–1.29 JASS/ability table semantics is unknown.
- OpenRealm is the best fit for a "native arm64 macOS app that uses the user's own 1.26a MPQs": it is C and SDL2, already targets iPad (arm64 Apple), and is MIT-licensed. On DotA it is roughly at "script loads, `main()` runs, custom abilities partly inferred".
- Warsmash runs on 1.26a-era MPQs and is the most mature for melee, but it is AGPL. Being Java/LibGDX, it should run on arm64 macOS through an arm64 JDK. That is an inference: the `arm64-testing` branch exists, but I found no doc confirming macOS arm64.
- In all three engines DotA support is ongoing work. Expect long-tail gaps in triggered spells, the item-combination system, AI, and the -modes or commands.

### Gaps
- I could not read Hive Workshop threads or Discord (403/auth), so Warsmash's 2026 feature claims (custom-map JASS coverage, multiplayer usability) are unverified beyond the code tree.
- I found no YouTube or demo evidence of a complete 5v5 DotA game on any reimplementation.
- No tested confirmation of OpenWar3 running DotA **6.83** (versus 6.77b), or of OpenRealm getting past `main()` into a playable frame loop on 6.83d.
- I found no repo named "OpenW3" (the `Dr-Bandi/OpenW3` and `tinyterrors/OpenW3` guesses 404'd).

## JASS VMs, interpreters, compilers and tooling

### Takeaway
There is no standalone, embeddable, production-grade JASS VM library. The working JASS interpreters live inside the engines: Warsmash's Java `jassparser`, OpenRealm's C VM (`jdo.c`, with hashtables and snapshot save), and OpenWar3's TypeScript `src/jass`. The tooling ecosystem around them (pjass, jassdoc, WurstScript, jhcr, JASS→Lua converters) is active and permissively licensed, and is useful for validating behaviour against the real natives.

### Cited Findings
- `lep/pjass`: "The famous jass syntax checker". C, BSD-2-Clause, last push 2026-10-13. — [repo](https://github.com/lep/pjass)
- `lep/jassdoc`: "Document the WarCraft 3 API" (an annotated common.j/blizzard.j). Last push 2026-10-19, no licence detected. OpenWar3 cites Hive threads for native semantics, and jassdoc is the community reference for them. — [repo](https://github.com/lep/jassdoc)
- `lep/jhcr`: "A compiler to allow hot code reload in WarCraft 3". Haskell, LGPL-3.0, last push 2026-10-13. — [repo](https://github.com/lep/jhcr)
- `wurstscript/WurstScript`: "Programming language and toolkit to create Warcraft III Maps". Java, Apache-2.0, last push 2026-10-24 (very active). The toolchain contains a JASS/Wurst parser and compile-time interpreter. The interpreter detail is my understanding of the toolchain and is not verified in this session. — [repo](https://github.com/wurstscript/WurstScript)
- Warsmash JASS VM: ANTLR grammar plus an instruction interpreter in `jassparser/src/com/etheller/interpreter`. It has a `CHashtable` simulation class (`core/.../simulation/util/CHashtable.java`). — [source tree](https://github.com/Retera/WarsmashModEngine)
- OpenRealm JASS VM:
  - In C. `jass_dobuffer` and `jass_remove_comments` are in `jdo.c`.
  - There is a "JSVM snapshot version 4".
  - Hashtable natives are host-owned registry slots (`api_hashtable.h`, `g_hashtable.c`), with save format v31.
  - Its lexer had to be fixed for Vexorian-minified tokens such as `'Hpal'or`, `851983then`, `I2R(0x540BE3FF)`.
  — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)
- OpenRealm native coverage: `common.txt` lists 1,549 natives and `api_module.c` registers 965 callbacks. "Registered-but-stub" natives DotA still calls include `SetPlayerAbilityAvailable` (650 refs), `UnitApplyTimedLife`, `PauseUnit`, and `SetUnitInvulnerable`. The last three had stub status when that doc was written. — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)
- OpenWar3 JASS runtime: TypeScript `src/jass/lexer.ts`, `src/jass/natives/*`, with test commands `pnpm jass:test` and `pnpm sim:test`. — [openwar3 #224](https://github.com/elevchyt/openwar3/issues/224), [GitHub code search](https://github.com/elevchyt/openwar3/tree/main/src/jass)
- JASS→Lua:
  - War3Net (C#) "can transpile JASS to C# or Lua" (the `War3Net.CSharpLua` NuGet package). — [NuGet](https://www.nuget.org/packages/War3Net.CSharpLua/1.3.0)
  - `BribeFromTheHive/vJass2Lua`: browser-based, last push 2022-12-31, no licence. — [repo](https://github.com/BribeFromTheHive/vJass2Lua), [Hive search snippet](https://www.hiveworkshop.com/threads/cjass2lua-powerfull-cjass-converter.320171)
  - `goshante/cjass2lua` (redirected from fullmetal-a): C++, GPL-2.0, last push 2024-09-21. — [repo](https://github.com/goshante/cjass2lua)
  - "Map Transpiler" only converts war3map.j→war3map.lua and is Windows-only. — [Hive snippet](https://www.hiveworkshop.com/threads/map-transpiler.329486)
- `sumneko/w3x2lni`: map format converter (w3x⇄lni/slk). Lua, GPL-3.0, 172 stars, last push 2025-12-18. — [repo](https://github.com/sumneko/w3x2lni)
- Rust JASS tooling: `WarRaft/JASS-Tree-sitter-Rust` (MIT, 2026-04), `deliro/glass` (a language that compiles to JASS, 2026-04), and `ceres-wc3/ceres` (Rust, MIT, last push 2020-09, stale). — [GitHub search](https://github.com/WarRaft/JASS-Tree-sitter-Rust), [ceres](https://github.com/ceres-wc3/ceres)
- `hackwaly/jass2`: "Jass2 interpreter", 0 stars, last push 2020-04 (stale toy). — [repo](https://github.com/hackwaly/jass2)

### Inferences
- A from-scratch engine would most likely reuse an engine-embedded VM: OpenRealm's in C (MIT, easiest to embed natively) or Warsmash's in Java (AGPL). pjass and jassdoc are the practical way to check grammar and native semantics.
- Converting JASS to Lua (Reforged-style) does not help a 1.26a target. Lua map scripts first appeared in 1.31, so a 1.26a client cannot run them. That is from general knowledge and was not re-verified in this session.

### Gaps
- I did not find a project literally called "jass runner".
- No benchmark of JASS VM speed on DotA's 132k-line script (OpenRealm notes a long array-fill `main()`).
- I did not verify how Warsmash's JASS VM performs on DotA.

## File-format libraries (MPQ, CASC, BLP, MDX/MDL, W3X/W3E/W3U/SLK)

### Takeaway
The format layer is solved and permissively licensed:
- **StormLib** (MPQ) and **CascLib** (CASC), both MIT, C/C++, actively maintained by Ladislav Zezula.
- **War3Net** (C#, MIT) covers nearly every W3X sub-format, as does **wc3libs** (Java, Apache-2.0).
- Several MIT BLP/MDX parsers exist, including Rust and TypeScript ones.

The main pitfall for DotA is protected-map quirks: 16 MiB sectors, a fake listfile, and a truncated w3i.

### Cited Findings
- `ladislav-zezula/StormLib`: "Official GitHub repository of the StormLib library". C, MIT, 655 stars, last push 2026-10-12. — [repo](https://github.com/ladislav-zezula/StormLib)
- `ladislav-zezula/CascLib`: "reading CASC storages from Blizzard games since 2014". C++, MIT, 501 stars, last push 2026-09-25. wc3-wasm's CASC extractor is built on CascLib. — [repo](https://github.com/ladislav-zezula/CascLib), [wc3-wasm](https://github.com/rgnv/wc3-wasm)
- `Drake53/War3Net`: "The complete .NET toolkit for Warcraft III modding". C#, MIT, 167 stars, last push 2026-10-17. — [repo](https://github.com/Drake53/War3Net)
- `inwc3/wc3libs`: "Java library for reading and modifying Warcraft III maps and game files". Apache-2.0, last push 2026-10-20. — [repo](https://github.com/inwc3/wc3libs)
- `ChiefOfGxBxL/WC3MapTranslator`: "Translate war3map ⇄ json formats for .w3x maps". MIT, last push 2026-07-12. — [repo](https://github.com/ChiefOfGxBxL/WC3MapTranslator)
- `Luashine/wc3-file-formats`: Kaitai Struct specs. No licence, last push 2023-04 (stale but a useful reference). — [repo](https://github.com/Luashine/wc3-file-formats)
- MPQ in Rust:
  - `WarRaft/mpq-rs`: MIT, 2026-03, WC3-focused. — [repo](https://github.com/WarRaft/mpq-rs)
  - `wowemulation-dev/warcraft-rs`: Apache-2.0, 2026-07. It absorbed `mopaq`, but is WoW-focused. — [repo](https://github.com/wowemulation-dev/warcraft-rs)
- BLP:
  - `WarRaft/blp-lib`: Rust with a C/C++ interface, MIT, 2025-10. — [repo](https://github.com/WarRaft/blp-lib)
  - `Pinta365/blp`: TypeScript, MIT, 2026-03. — [repo](https://github.com/Pinta365/blp)
  - `DrSuperGood/blp-iio-plugin`: Java, GPL-3.0, 2018. Warsmash notes it misses alpha on some campaign textures. — [repo](https://github.com/DrSuperGood/blp-iio-plugin), [Warsmash README](https://github.com/Retera/WarsmashModEngine)
  - `Dennis1000/libblp`: Delphi, GPL-3.0, 2016 (stale). — [repo](https://github.com/Dennis1000/libblp)
- MDX/MDL:
  - mdx-m3-viewer parsers (TypeScript, MIT). — [repo](https://github.com/flowtsohg/mdx-m3-viewer)
  - Retera Model Studio (Java, MIT). — [repo](https://github.com/Retera/ReterasModelStudio)
  - `speige/MdxLib`: Magos's C# MDX/MDL parser, no licence, 2025-01. — [repo](https://github.com/speige/MdxLib)
  - OpenRealm tools: `mdxtool`, `maptool`, `mpqtool`, `blp2jpg`. — [README](https://github.com/corepunch/open-realm)
- **Protected-map quirks that matter for DotA:**
  - MPQ v1 at offset 512, with `wSectorSizeShift`=15 (16 MiB sectors). Readers that clamp sector size above 64 KiB fail on `war3map.j`, `w3e`, `w3a` and `doo`.
  - The `(listfile)` is fake binary, so lookups must go through the hash table.
  - "war3map.w3i extraction is byte-identical to StormLib on a protected test map" (wc3-wasm).
  — [open-realm doc](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md), [wc3-wasm](https://github.com/rgnv/wc3-wasm)

### Inferences
- StormLib is the reference for matching Storm's behaviour on protected maps. Any reimplementation should be tested against it.
- War3Net and wc3libs give independent parsers to cross-check object-data (w3a/w3u) semantics.

### Gaps
- I did not audit parser correctness on DotA beyond the projects' own reports.
- `cipherxof/w3x-parser` and similar guessed names do not exist (404).

## Fidelity: determinism and lockstep compatibility with real 1.26a clients, and the data tables

### Takeaway
**No open-source reimplementation aims to interoperate with real 1.26a clients in a lockstep game, or to reproduce 1.26a's exact simulation.**
- OpenWar3 and OpenRealm both use host or server authority with state snapshots, and OpenWar3 says outright that determinism is "not required".
- Warsmash uses its own order-relay server.

All three read unit and ability data from the user's own MPQs and the map's overrides. That is the right data model, but it does not give bit-exact behaviour.

### Cited Findings
- OpenWar3: "Determinism — Not required for sync. Only one machine simulates." Snapshots run at about 10–20 Hz, with no client prediction. — [docs/multiplayer.md](https://github.com/elevchyt/openwar3/blob/main/docs/multiplayer.md)
- OpenRealm: authoritative server, entity delta snapshots, UDP. — [ARCHITECTURE.md](https://github.com/corepunch/open-realm/blob/main/ARCHITECTURE.md)
- Warsmash: has its own `server` "uberserver" (TCP lobby and game) and a client order-sending listener. — [source tree](https://github.com/Retera/WarsmashModEngine/tree/main/server/src/com/etheller/warsmash/networking/uberserver)
- Warsmash #99 shows that simulation details such as unit update order within a tick change outcomes (kill credit). This is the kind of divergence that breaks lockstep parity. — [Warsmash #99](https://github.com/Retera/WarsmashModEngine/issues/99)
- Data tables come from the user's install:
  - OpenWar3's `src/data` "holds SLK loaders, not tables — `loadUnitRegistry(vfs)` reads `Units\UnitBalance.slk`… out of the user's MPQs at runtime". — [docs/multiplayer.md](https://github.com/elevchyt/openwar3/blob/main/docs/multiplayer.md)
  - OpenRealm's lookup order is map archive → `Custom_V1\` → base MPQ. — [dota-map-playability.md](https://github.com/corepunch/open-realm/blob/main/docs/games/warcraft-3/dota-map-playability.md)
- OpenWar3 copies semantics from the real engine piece by piece:
  - `IsUnitInRange` is measured to the collision edge.
  - `IsTerrainPathable` is inverted.
  - `ReviveHero` follows the altar rules.
  - BlzSet* stat semantics are taken from Hive threads.
  — [docs/map-compatibility.md](https://github.com/elevchyt/openwar3/blob/main/docs/map-compatibility.md)

### Inferences
- Playing DotA online with existing 1.26a players (Garena, RGC or PvPGN-style hosts, real War3.exe clients) would need bit-exact lockstep. That means identical RNG, fixed-point/float behaviour, order processing, and pathing. None of these projects attempts that.
- A reimplementation is therefore viable only for games where everyone runs the same reimplementation. Even then, gameplay will diverge from 1.26a in many small ways until a long tail of mechanics is matched: attack timing, the damage/armor table, buff stacking, pathing, and orb/lifesteal behaviour.
- For "true" 1.26a DotA with real-client compatibility, recompiling or emulating the original binary (the other track in this research) remains the only route.

### Gaps
- I found no project documenting 1.26a's RNG or tick model for lockstep parity.
- I did not research replay (.w3g) compatibility in any engine.

## Legal model: engines that require the user's own War3.mpq/War3x.mpq

### Takeaway
Every active engine uses the bring-your-own-data model and ships no Blizzard assets:
- **OpenRealm** and **Warsmash** accept classic MPQ installs, so 1.26a-era War3.mpq/War3x.mpq work.
- **godot_warcraft3** also needs classic MPQs.
- **OpenWar3** requires a 1.30.4 install.
- **wc3-wasm** extracts from a Reforged-era CASC install.

Licences split into MIT (OpenRealm, OpenWar3, godot_warcraft3) and AGPL-3.0 (Warsmash, HiveWE).

### Cited Findings
- OpenRealm: "The project does not include retail game data. Use it only with data you legally own. OpenRealm is not affiliated with Blizzard Entertainment." — [README](https://github.com/corepunch/open-realm)
- Warsmash: "you need to purchase a valid copy of Warcraft III… and then configure Warsmash to use those assets". AGPL because of GPL dependencies. The README also says the rumoured 2022 cease-and-desist "did not happen". — [README](https://github.com/Retera/WarsmashModEngine)
- OpenWar3: "zero copyrighted assets. Assets read from your local install, client-side, never uploaded or hosted." Its multiplayer design is shaped by the rule that no Blizzard data sits on servers it controls. — [README](https://github.com/elevchyt/openwar3), [docs/multiplayer.md](https://github.com/elevchyt/openwar3/blob/main/docs/multiplayer.md)
- wc3-wasm: "you supply your own legally obtained copy (an installation made through your own Battle.net account, i.e. the Reforged-era client with the classic data)". — [README](https://github.com/rgnv/wc3-wasm)
- godot_warcraft3: requires a genuine classic client with `War3.mpq` / `War3x.mpq`, not a modern CASC `Data/`. — [README](https://github.com/LiGameAcademy/godot_warcraft3)

### Inferences
- For a reFrozen-style project built on owned 1.26a MPQs, OpenRealm (MIT) and Warsmash (AGPL) are directly compatible with that data. OpenWar3 is not, unless it is forked.
- AGPL (Warsmash, HiveWE) brings source-disclosure obligations, including for network use, if code is reused. The MIT projects (OpenRealm, OpenWar3, mdx-m3-viewer, StormLib, CascLib, War3Net) do not.

### Gaps
- No legal opinion was researched. The licence and bring-your-own-data statements above are the projects' own claims.
