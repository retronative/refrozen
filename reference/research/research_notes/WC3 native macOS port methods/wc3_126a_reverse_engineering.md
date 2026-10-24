# Warcraft III 1.26a Reverse-Engineering Knowledge (war3.exe, Game.dll, Storm.dll) for a Native arm64 macOS Port

Method note: web research (bnetdocs, GitHub, Hive Workshop, Liquipedia, legal sources), plus **static header-only parsing** of binaries already on this machine: the iCCup launcher folder (`/Users/thixpin/Code/retronative/DOTA/iCCup_Launcher/app/Launcher/`) and the official Blizzard patch `/Users/thixpin/Code/retronative/DOTA/ICC Game client install/War3TFT_126a_English.exe`. Nothing was executed. I parsed PE headers and the patch's MPQ archives with throwaway Python scripts in the session scratchpad. Findings from that parsing are cited as "local analysis" with the file path. Most Hive Workshop pages returned HTTP 403 to the fetcher, and the GitHub search API hit its rate limit partway through, so XGM.guru and the Chinese forums (KKDZ, YDWE bbs) were **not** reviewed directly.

## 1. Binary facts: compiler, size/structure, imports, packing/Warden, threading

### Takeaway
1.26 (1.26.0.6401) was released on 2011-03-24. Its binaries were built on 2011-03-18 with **MSVC 2005 (VC++ 8.0, build 50727, linked against MSVCR80.dll)**. The patch MPQ headers give the 1.26a target sizes: **Game.dll 12,042,240 bytes, War3.exe 471,040 bytes, Storm.dll 339,968 bytes**. The official patch ships these as **BSDIFF40 binary deltas**, not as whole files, so getting a clean Game.dll means applying the patch to a 1.21b-era install (the iCCup kit includes the 1.21b installers for this). The Blizzard binaries themselves are not packed. The third-party iCCup DLLs (w3lh.dll, d3d8.dll) are UPX-packed.

### Cited Findings
- Patch 1.26 is version 1.26.0.6401, released March 24, 2011 (NetEase China re-release October 23, 2015). Changes: Hex/Metamorphosis fix and a fix for "Mac patches that could lead to disconnections during Battle.net games". — [Liquipedia Patch 1.26](https://liquipedia.net/warcraft/Patch_1.26)
- Softpedia dates the 1.26a manual patch to Apr 1, 2011, with the same change list. I found no separate 1.26a page on Liquipedia. — [Softpedia changelog](https://games.softpedia.com/progChangelog/Warcraft-III-The-Frozen-Throne-English-Patch-Changelog-27188.html)
- **Patch structure (local analysis):** `War3TFT_126a_English.exe` (58,718,061 bytes) is a PE32 stub with an MPQ at offset 0x29000. That MPQ contains `(signature)`, `BNUpdate.exe`, `Patch_War3_Low.mpq`, `Patch_War3_Med.mpq`, `Patch_War3x.mpq`, `mpqs.lst`, `patch.txt` and `prepatch.lst`. The nested `Patch_War3x.mpq` (58,264,863 bytes) holds `Game.dll`, `War3.exe` and `Storm.dll` as **BSDIFF40 delta patches**, each behind a 0x18-byte header. — local analysis of `/Users/thixpin/Code/retronative/DOTA/ICC Game client install/War3TFT_126a_English.exe`
- **Target sizes and build times from the delta headers (local analysis):** Game.dll = 0x00B7C000 = **12,042,240 bytes**, FILETIME 2011-03-18 20:05:51 UTC. War3.exe = 0x73000 = **471,040 bytes**, 2011-03-18 20:03:55. Storm.dll = 0x53000 = **339,968 bytes**, 2011-03-18 19:56:03. The Storm.dll header size and time match the iCCup Storm.dll exactly (339,968 bytes, PE timestamp 2011-03-18 19:56:02), which confirms both that the field means target size and that **the iCCup-shipped Storm.dll is the stock Blizzard 1.26a Storm.dll** (SHA-1 5144e6bb77223936d4dff31758db71c189e9b63c). — local analysis of the same patch and `/Users/thixpin/Code/retronative/DOTA/iCCup_Launcher/app/Launcher/Storm.dll`
- **Compiler (local analysis of Storm.dll 1.26a):** PE linker version 8.0. The Rich header shows VS2005 toolchain entries at build 50727, plus older MASM/import objects (builds 9044 and 4035). It imports `MSVCR80.dll` (57 functions, including `__CxxFrameHandler3` and `_except_handler4_common`, so C++ with EH). Image base is 0x15000000. Sections are .text 0x3FBFA, .rdata, .data, .rsrc, .reloc. — local analysis
- **Storm.dll exports (local analysis):** 814 export slots with ordinal base 101. Only 53 are named, all MSVC-mangled C++ (`SFile::Open/Read/Close/LoadFile`, `SCritSect`, `CSRWLock`, `SEvent`, `SThread::Create`, `SFile::EnableHash` and others). Everything else, the classic `SFile*`, `SMem*`, `SStr*`, `SReg*`, `SNet*` and `SBmp*` C API, is **ordinal-only**. — local analysis
- **Storm.dll imports (local analysis):** MSVCR80, VERSION, KERNEL32 (84 functions, including `CreateThread`, `WaitForMultipleObjects`, critical sections, `IsDebuggerPresent`), USER32 (74, a full window/dialog message loop), GDI32 (29), comdlg32 (`GetSaveFileNameA`) and ADVAPI32 (the registry `Reg*` family and `GetUserNameA`). **No Winsock import** in this Storm.dll. — local analysis
- Community-known Storm ordinals: 251 SFileAuthenticateArchive, 252 SFileCloseArchive, 265 SFileGetFileSize, 266 SFileOpenArchive, 267 SFileOpenFile, 268 SFileOpenFileEx, 269 SFileReadFile, 281 SFileLoadFileEx. Ordinal 262 is disputed (SFileDdaDestroy vs SFileDestroy). — [Valhalla Legends forum](https://vl.bnetdocs.org/index.php?msg=159804); [CSDN Delphi import](https://bbs.csdn.net/topics/390832350)
- Function names (no ordinals) for the Storm C API appear in BWAPI's StarCraft headers. — [BWAPI docs](https://pages.cs.wisc.edu/~starr/bwapi-read-only/html/globals_0x73.html)
- War3.exe historically imported Winsock through `wsock32.dll` by ordinal (recv #0x16, send #0x19, plus recvfrom/accept/socket/closesocket). This comes from a 2006-era post, so it predates 1.26. — [Valhalla Legends forum](https://vl.bnetdocs.org/index.php?msg=156573)
- **Renderer:** the Windows client defaults to Direct3D and also has a built-in OpenGL renderer selected with `-opengl`. In 1.29 these switches became `-graphicsapi Direct3D9|OpenGL2`. — [Hive command-line guide](https://www.hiveworkshop.com/threads/complete-command-line-arguments-guide.288224); [CodeWeavers tip](https://codeweavers.com/compatibility/crossover/tips/warcraft-iii-reign-of-chaos/use-opengl-instead-of-direct3d)
- **Direct3D 8 in 1.26a (local analysis + community):** the iCCup launcher ships a UPX-packed `d3d8.dll` proxy (182,272 bytes, VS2005, PE timestamp 2012-04-03) that exports `Direct3DCreate8`. That only works if Game.dll loads `d3d8.dll` and calls `Direct3DCreate8`. WarcraftHelper recommends a "d3d8to9" wrapper for 1.20e and 1.24e to reduce stuttering, and YDWE lists a Direct3D8to9 sub-project. — local analysis `/Users/thixpin/Code/retronative/DOTA/iCCup_Launcher/app/Launcher/d3d8.dll`; [WarcraftHelper](https://github.com/LoveBeforT/WarcraftHelper); [YDWE](https://github.com/actboy168/YDWE)
- **.mix plugin loading:** the iCCup launcher ships `FPSUnlocker.mix`, and RenderEdge Widescreen is distributed as a `.mix` file referenced by Lutris installers. WC3 loads `*.mix` files from its folder (the Miles Sound System plugin mechanism), which makes them a standard DLL-injection vector. — local file `/Users/thixpin/Code/retronative/DOTA/iCCup_Launcher/app/Launcher/FPSUnlocker.mix`; [Lutris installer](https://lutris.net/games/install/38682/view)
- **Warden:** Warcraft III includes Blizzard's Warden anti-cheat, which hashes running programs and reports to Blizzard servers. BNETDocs notes a Warden update for WC3 dated April 14, 2009. — [Wowpedia: Warden](https://wowpedia.fandom.com/wiki/Warden_(software)); [BNETDocs news](https://bnetdocs.org/news?page=18)

### Inferences
- War3.exe 1.26a is a small (460 KB) launcher. The real game, including the engine, JASS VM, UI, net and renderer front-end, is the 12 MB Game.dll, and Storm.dll is Blizzard's runtime library (MPQ, memory, strings, registry, windowing/dialogs). w3lh.dll exports `GameMain` (see section 2), which matches the community understanding that War3.exe does `LoadLibrary("Game.dll")` and calls its exported `GameMain`. I did not verify this in the 1.26a War3.exe because only the delta was available.
- Game.dll was very likely built with the same VS2005/MSVCR80 toolchain (same build day, about 9 minutes after Storm.dll). Confirm this from a patched Game.dll's Rich header.
- Warden in WC3 is delivered by the Battle.net server as downloadable modules. It is not code baked into the shipped binaries, and PvPGN-based servers (iCCup, Eurobattle) do not run Blizzard Warden. iCCup runs its own "Anti-Hack" launcher instead (see section 2). For a port this means no packer or obfuscation layer in the stock binaries. I saw no UPX or other packer section names in the stock Storm.dll.
- Because Storm.dll exports almost everything by ordinal, a reimplementation or shim must match Game.dll's imports **by ordinal number**. StormLib (section 2) gives MPQ semantics but not ABI-compatible ordinals.

### Gaps
- **Game.dll's import table** (d3d8 / opengl32 / Mss32 / Winsock / Bink / dsound / ijl) and its section layout could not be read. The patch has only deltas against an older base. Next step: install 1.21b TFT from the local installers, apply `War3TFT_126a_English.exe` in Wine or a Windows VM, then parse with the scratchpad `pe.py`.
- I found no source on the threading model (main thread with a Storm worker plus a Miles audio thread is commonly assumed, but it is unsourced).
- I found no published hash list (MD5/SHA) for stock 1.26a Game.dll.
- Not verified: whether 1.26a's Game.dll links `Mss32.dll` statically or through import (it is assumed to be in the install folder), and whether Bink (`binkw32.dll`) is used for cinematics or the cinematics are .mpq/.avi.

## 2. Community RE resources (offsets, SDKs, japi, loaders, decompilations)

### Takeaway
No public full decompilation of Game.dll or Storm.dll exists outside leaks. The usable knowledge lives in hook projects that hard-code per-version Game.dll addresses: UjAPI (MIT, active 2026), WarcraftHelper (GPL-3.0), RenderEdge (no license), YDWE (GPL-3.0), the w3l PvPGN loader (source on GitHub, which is what iCCup's w3lh.dll is) and UnrealKaraulov's 1.26a client/server code (Unlicense). StormLib (MIT, active) reimplements MPQ but not Storm.dll's ABI.

### Cited Findings
| Project | What it is | License | Activity (repo `pushed_at`) | Source |
|---|---|---|---|---|
| UnryzeC/UjAPI | "Unryze Jass API", adds new JASS natives to WC3 by hooking the game | MIT | pushed 2026-08-10; 42 stars, ~414 commits | [GitHub](https://github.com/UnryzeC/UjAPI) |
| nazarpunk/wc3-ujapi | UjAPI tooling | MIT | 2026-03-08 | [GitHub](https://github.com/nazarpunk/wc3-ujapi) |
| LoveBeforT/WarcraftHelper | plugin: map-size limit, widescreen, FPS unlock, auto-replay, HP bars; supports **1.20e, 1.24e, 1.26a, 1.27a, 1.27b**; CMake + VS2022; cites YDWE and RenderEdge as references | GPL-3.0 | 249 stars, 69 commits | [GitHub](https://github.com/LoveBeforT/WarcraftHelper) |
| ENAleksey/RenderEdge | "Graphic modification for WarCraft 3" (Launcher/Loader/RenderEdge; d3d9 tags) | none shown | pushed 2019-02-06; 48 stars | [GitHub](https://github.com/ENAleksey/RenderEdge) |
| ENAleksey/RenderEdge_Widescreen | widescreen for WC3 | none | pushed 2022-02-14; 102 stars | [GitHub](https://github.com/ENAleksey/RenderEdge_Widescreen) |
| actboy168/YDWE | Chinese World Editor extension, sub-projects ydhost, Direct3D8to9, w3x2lni, pjass, jasshelper | GPL-3.0 | 550 stars, 3,019 commits | [GitHub](https://github.com/actboy168/YDWE); [Gitee mirror](https://gitee.com/yjbdsky/YDWE) |
| w4454962/embedded-japi-plugin | docs for the built-in japi plugin (Chinese) | none | 2022-07-10; 41 stars | [GitHub](https://github.com/w4454962/embedded-japi-plugin) |
| w3lh/w3l | "Warcraft III TFT/RoC PvPGN Loader" (C) | not shown on profile page | 67 stars, 30 forks | [GitHub](https://github.com/w3lh) |
| UnrealKaraulov/war3_my_platforms | complete PvPGN server + GHost bot + enhanced **1.26a client** (anti-cheat, gproxy DLL, voice chat), released 2026 as unfinished code | Unlicense | pushed 2026-03-16 | [GitHub](https://github.com/UnrealKaraulov/war3_my_platforms) |
| UnrealKaraulov/FileListExtractorFor1.26a | 1.26a tool | Unlicense | 2021-09-19 | [GitHub](https://github.com/UnrealKaraulov/FileListExtractorFor1.26a) |
| luciouskami/war3-lua-engine | Lua scripting engine for WC3 (Game.dll hook) | GPL-2.0 | 2013-12-30 | [GitHub](https://github.com/luciouskami/war3-lua-engine) |
| EX3-0/wc3extender | WIP "SKSE equivalent for WC3" | GPL-2.0 | 2026-08-06 | [GitHub](https://github.com/EX3-0/wc3extender) |
| Whimsyduke/War3GameDllBaseAddress | gets Game.dll base address (Chinese) | none | 2017 | [GitHub](https://github.com/Whimsyduke/War3GameDllBaseAddress) |
| WFE (Warcraft Feature Extender) | feature-extension loader, works on 1.26a, "all versions on Github" | ? | Hive thread | [Hive](https://www.hiveworkshop.com/threads/wfe-warcraft-feature-extender.310863/) |
| ladislav-zezula/StormLib | MPQ read/write library (clean-room) | MIT | pushed 2026-10-12; 655 stars | [GitHub](https://github.com/ladislav-zezula/StormLib) |

- The README of UnrealKaraulov/war3_my_platforms (Russian) describes "Warcis": PvPGN with bcrypt passwords, multithreaded GHost bots, DotA Elo stats, and a client part with anti-cheat, gproxy as a DLL and in-game game-creation menus. The 2026 note says the client "contains many bugs and is unstable". — [GitHub](https://github.com/UnrealKaraulov/war3_my_platforms)
- **iCCup's w3lh.dll (local analysis):** 35,328 bytes, UPX-packed, built with VS2008 (linker 9.0, Rich build 30729), PE timestamp 2011-03-16. It exports `@w3l_hash_init@4`, `@w3l_lph_checked@16`, `GameMain`, `w3l_do_hash` and `w3l_logon_proof_hash`. Those names match the w3l PvPGN loader. It provides its own `GameMain` and replaces Battle.net logon-proof/hash handling so the stock client can log on to PvPGN. SHA-1 691d26accd672f6716c817da5a6e8dee4a6bc390. — local analysis `/Users/thixpin/Code/retronative/DOTA/iCCup_Launcher/app/Launcher/w3lh.dll`; [w3l](https://github.com/w3lh)
- The iCCup "Anti-Hack launcher" has a history of failing under Wine ("Warcraft III was unable to initialize"). — [WineHQ bug 23873](https://www.winehq.org/pipermail/wine-bugs/2011-May/275877.html)
- Blizzard accidentally shipped **debug symbols** (plus unreleased content) in an archive with **Reforged 2.0.1** (Dec 2024). Those symbols are for the Reforged-era codebase, not 1.26a, and are of uncertain legal status. — [Hive Workshop](https://hiveworkshop.com/threads/blizzard-accidentally-releases-debug-symbols-maps-and-exclusive-content-in-warcraft-3-update-version-2-0-1.357413)
- Blizzard's own Battle.net 1.26 patch shipped the BSDIFF40 delta format inside MPQ (local analysis above). StormLib documents the MPQ "patch" handling. — [StormLib](https://github.com/ladislav-zezula/StormLib)

### Inferences
- The richest public source of **1.26a Game.dll offsets** is the source code of WarcraftHelper, UjAPI, RenderEdge and the w3l loader. All of them hard-code per-version addresses (1.26a vs 1.27a and so on). UjAPI and UnrealKaraulov's code are permissively licensed. WarcraftHelper and YDWE are GPL-3.0, which would infect a port that copies code, though not one that only reads them as documentation.
- A port must replicate w3l's logon-hash behavior (or link equivalent code) to talk to iCCup and Eurobattle-style PvPGN servers.
- The leaked "war3 source" and the Reforged symbols are legal hazards. Do not use them as recompile inputs.

### Gaps
- Not located or verified: "MemHack"/"memhack japi" repositories, KKDZ/Chinese japi offset tables, XGM.guru 1.26a threads (the site was not fetched), shared Ghidra/IDA databases for 1.26a, and a canonical "war3 natives table" with Game.dll addresses. The GitHub search API rate limit cut these searches short.
- w3l's license was not visible from the org page. Check `github.com/w3lh/w3l` for LICENSE.
- No public Game.dll or Storm.dll decompilation project (non-leak) was found.

## 3. Network: Battle.net/PvPGN, W3GS, LAN, open servers

### Takeaway
The W3GS game protocol and the Battle.net chat/logon protocol are thoroughly documented on BNETDocs. PvPGN (GPL-2.0, active Aug 2026) and GHost++ / Aura provide reference server and host implementations. A port that speaks byte-identical W3GS with 1.26a version checks, and that reproduces the deterministic lockstep simulation, could interoperate with existing players.

### Cited Findings
- BNETDocs documents W3GS packets with ID, direction, byte layout and version applicability. Examples: 0x2F W3GS_SEARCHGAME (LAN broadcast probe, product WAR3/W3XP), 0x30 W3GS_GAMEINFO (UDP broadcast about every 5 s on LAN), 0x48 W3GS_INCOMING_ACTION2 (overflow of 0x0C actions), 0x28/0x0F chat, 0x46 PONG_TO_HOST, 0x10 START_LAG. Some packets are marked "In Research". — [BNETDocs headers](https://bnetdocs.org/document/16); [0x2F](https://bnetdocs.org/packet/434/w3gs-searchgame); [0x30](https://bnetdocs.org/packet/435/w3gs-gameinfo); [0x48](https://bnetdocs.org/packet/468/w3gs-incoming-action2); [0x10](https://bnetdocs.org/packet/519/w3gs-start-lag)
- BNETDocs maintains packet-bnetp, a Wireshark dissector with W3GS support (added 2011). — [GitHub](https://github.com/BNETDocs/packet-bnetp)
- pvpgn/pvpgn-server: "Next generation of PvPGN server", GPL-2.0, 650 stars, pushed 2026-08-17. — [GitHub](https://github.com/pvpgn/pvpgn-server)
- GHost++ (hosting bot that acts as game host, by Trevor Hogan, 2008) is described as unmaintained, with Aura pointed to as the maintained alternative. A FOSDEM 2026 talk slide lists GHost++ as Apache 2.0, while some forks (uc-ghost/ent-ghost) are GPLv3. — [Stannnnn/ghostpp](https://github.com/Stannnnn/ghostpp); [FOSDEM 2026 "20 years of Eurobattle.net"](https://fosdem.org/2026/events/attachments/F3VSDB-20-years-of-eurobattle-net-a-retrospective/slides/267442/20_years_irgzzsr.pdf); [w3gh/ghostplusplus mirror](https://github.com/w3gh/ghostplusplus)
- The Mac client on OS X 10.9+ cannot use Battle.net/LAN because Open Transport was deprecated. That shows the original Mac networking used **Open Transport** (Classic Mac OS networking) rather than BSD sockets. — [Hive Workshop Wineskin guide (search snippet; page 403)](https://www.hiveworkshop.com/threads/warcraft-iii-on-wineskin-mac.257050)

### Inferences
- LAN discovery runs over UDP 6112 broadcast (SEARCHGAME/GAMEINFO) and game traffic over TCP 6112 by default. This is standard community knowledge, consistent with the UDP broadcast behavior on BNETDocs, but no page here states the port number. Verify before relying on it.
- W3GS is pure lockstep: only player actions are sent (0x0C/0x48), so a native port must reproduce Game.dll's simulation **bit-exactly**, including x87 float semantics, RNG and iteration order, or it will desync with Windows 1.26a players. On arm64 this is the hardest compatibility constraint, because x87 80-bit intermediates and MSVC 2005 codegen are not reproduced by clang on arm64 by default.
- Replay (.w3g) compatibility follows from the same determinism requirement.

### Gaps
- I found no source detailing the 1.26a version/EXE-hash checks (SID_AUTH_CHECK with the war3.exe/Storm/Game.dll checksum) that PvPGN servers use for version gating. bnetdocs has the general mechanism, but I did not fetch it.
- The FOSDEM 2026 Eurobattle slides could not be text-extracted, so details such as player counts and the versions Eurobattle supports remain unverified.

## 4. Original macOS client (1.26a Mac): architecture, APIs, symbols

### Takeaway
The Mac client became a Universal (PPC + Intel) build with patch 1.21 (Jan 2007), and 1.26 included Mac-specific fixes. It used Open Transport networking and an OpenGL renderer (the Windows build also has an OpenGL path). The original installers were PPC-only, so they fail on 10.7+ without Rosetta. I found **no evidence that the 1.26a Mac binaries shipped with symbols**. The only known WC3 symbol release is from Reforged 2.0.1.

### Cited Findings
- Patch 1.21 (Jan 22, 2007) was a "Universal binary patch" that made WC3 run on Intel Macs. — [Macworld](https://www.macworld.com/article/183256/war3-2.html)
- On OS X 10.7+ the game cannot be installed because the installer is PPC format, and 10.9+ cannot play Battle.net/LAN due to the Open Transport deprecation. — [Hive Workshop (search snippet)](https://www.hiveworkshop.com/threads/warcraft-iii-on-wineskin-mac.257050)
- Forum reports: install discs were PPC-only, but once patched through Battle.net "the apps are patched as universal". This is anecdotal. Another user needed "Open with Rosetta". — [MacRumors](https://forums.macrumors.com/threads/some-blizzard-games-not-supported-in-10-7-lion.1128527/)
- CodeWeavers: WC3 "actually runs fine on Intel Macs, it's the installer that won't run", and the 1.26a patch can be installed from a 10.6-or-earlier Mac or VM. — [CodeWeavers tip](https://codeweavers.com/compatibility/crossover/tips/warcraft-iii-reign-of-chaos/install-from-battlenet)
- Patch 1.26 fixed "an issue where some Mac patches could lead to disconnections during Battle.net games", so the Mac and Windows 1.26 builds were meant to interoperate in multiplayer. — [Liquipedia](https://liquipedia.net/warcraft/Patch_1.26)
- From 1.31 (May 2019) WC3 requires a 64-bit OS and Metal on Mac. Reforged's Mac app is x86_64. — [Blizzard support](https://support.blizzard.com/article/000191926); [Blizzard forum crash report](https://us.forums.blizzard.com/en/warcraft3/t/help-with-constant-crashes/38304)
- Debug symbols leaked through an archive in Reforged 2.0.1. The platform was not specified. — [Hive Workshop](https://hiveworkshop.com/threads/blizzard-accidentally-releases-debug-symbols-maps-and-exclusive-content-in-warcraft-3-update-version-2-0-1.357413)

### Inferences
- The 1.26a Mac app is most likely a 32-bit Mach-O fat binary (ppc + i386) using Carbon, OpenGL and Open Transport. It is 32-bit only, so it cannot run on any macOS since 10.15 or on Apple Silicon without full emulation.
- As a **recompile or lifting input**, the Mac i386 build offers some advantages: an OpenGL renderer that maps more directly onto modern GL/Metal shims, Mac-native file/input code, and possibly richer Mach-O symbol tables (Mach-O executables often keep more exported or local symbols than stripped PE files). It also shares the lockstep simulation with Windows 1.26, since cross-platform play worked. Its disadvantages: Carbon and Open Transport are dead APIs that must be stubbed anyway, the community offset knowledge targets the Windows Game.dll only, and the PPC slice is irrelevant. Inspecting a 1.26a Mac `Warcraft III.app` with `nm`/`otool -l` would quickly show whether symbols survive. That check should run before choosing an input.

### Gaps
- I could not confirm the actual architecture slices, frameworks (Carbon vs Cocoa), symbol presence or binary layout of the 1.26a Mac app. No source describes them, and no Mac 1.26a binary is on this machine.
- Not confirmed: whether the Mac build bundles its engine as one executable or as a Mac equivalent of Game.dll and Storm.

## 5. Legal: EULA, Reforged, takedowns

### Takeaway
The classic WC3 EULA explicitly bans reverse engineering, decompiling, derivative works and **Battle.net protocol emulation**. The bnetd case (8th Cir. 2005) upheld these clauses and found that they waive the DMCA interoperability exception. Blizzard forced the clean-room-ish Java WC3 engine Warsmash off GitHub in July 2022. A port of 1.26a code is high legal risk. Distributing only a loader or translation layer that needs the user's own game files is lower risk but still contested.

### Cited Findings
- WC3 EULA §3A: no "reverse engineer, derive source code, modify, disassemble, decompile, create derivative works based on the Program" without written consent. §3C(iv): no emulating or redirecting Battle.net "communication protocols … through protocol emulation, tunneling, modifying or adding components to the Program". §3C(v): no tools connecting to "Battle.net's private binary interface". — [Warcraft3_EULA (Gentoo overlay copy)](https://data.gpo.zugaina.org/src_prepare-overlay/licenses/Warcraft3_EULA)
- The current Blizzard EULA §1.C keeps the "translate, reverse engineer, derive source code from, modify, disassemble, decompile, or create derivative works" ban for the whole Platform. This is quoted by a fan site, not taken from Blizzard's page. — [Warcraft Tavern](https://www.warcrafttavern.com/wow/news/blizzard-reminds-players-that-third-party-software-is-not-allowed-in-world-of-warcraft/)
- *Davidson & Associates v. Jung*, 422 F.3d 630 (8th Cir. 2005): Blizzard won against the bnetd developers. The court held the EULA and TOU enforceable, found that reverse-engineering rights were waived, and found DMCA anti-circumvention and trafficking violations (bnetd skipped CD-key checks). — [8th Cir. opinion PDF](https://ecf.ca8.uscourts.gov/opndir/05/09/043654P.pdf); [EFF case page](https://www.eff.org/cases/blizzard-v-bnetd); [Harvard summary](https://cyber.harvard.edu/people/tfisher/IP/2005_Blizzard.pdf)
- Warsmash (an MIT-licensed Java 8 alternative WC3 engine that required the user's own game assets) got a Blizzard demand in July 2022 to cease and remove it within 17 days. It disappeared from GitHub. — [80.lv](https://80.lv/articles/blizzard-demanded-to-stop-the-development-of-the-warsmash-engine/)
- Earlier precedent: Blizzard took down a fan HTML5 StarCraft remake in 2015. — [Ubergizmo](https://ubergizmo.com/2015/10/blizzard-takes-down-html5-starcraft/amp)
- Since 1.31/Reforged, classic patches cannot be downloaded from Blizzard, and the official client is the 64-bit Metal build. — [Blizzard support](https://support.blizzard.com/article/000191926)

### Inferences
- Projects that survived for years (PvPGN, GHost++, StormLib, UjAPI, WarcraftHelper, RenderEdge) are interop tools or mods that do not redistribute Blizzard code. Warsmash, a complete engine replacement, was targeted. A native port that redistributes recompiled Game.dll code would be more exposed than either. Distributing only a "bring your own 1.26a files" translator or loader is the lowest-risk form.
- Leaked 1.x source and the Reforged 2.0.1 symbols would taint a project. Do not use or link them.

### Gaps
- I did not retrieve the exact text of the Reforged-era custom-game/EULA changes (Blizzard's ownership of custom maps, 2020) from a primary source.
- I found no WC3 classic-specific takedown of a hook or loader project (UjAPI, japi, RenderEdge) and no Blizzard action against iCCup or Eurobattle in this pass.
