# Win32 Runtime / Compatibility Layers and Dynamic Translators for WC3 1.26a on arm64 macOS

Research date: 2026-10-24. About 20 web searches and fetches. Several primary pages returned HTTP 403 to the fetcher: the CodeWeavers WC3 1.26a forum guide, the CodeWeavers arm64 blog post (2026-07-31), and the MacRumors M1 thread. Claims about those pages therefore come from search-engine snippets, not full reads, and are marked "(snippet)".

## 1. Wine-family runtimes on macOS arm64 (Wine upstream, CrossOver, GPTK, Whisky, Kegworks/Sikarugir)

### Takeaway
As of late 2026, every *shipping, stable* Wine distribution on Apple Silicon is still an **x86-64 Wine running under Rosetta 2**. 32-bit Windows code runs in Wine's own 32-on-64 "WoW64" mode, inside that 64-bit process. CodeWeavers shipped the first **native-arm64 Wine + FEX** CrossOver *Preview* in July 2026. CrossOver 27 (expected early 2027) is slated to make that the default and to drop 32-bit bottles. Whisky is dead upstream. Kegworks has been renamed Sikarugir.

### Cited Findings
**Upstream Wine**
- Wine 11.0 was released in January 2026, around Jan 13 (inferred from article timing). It "eliminates the separation between 32-bit and 64-bit commands": a single `wine` runs 32-bit binaries on 64-bit systems internally (new WoW64). The Register notes this is "nothing new for macOS", because macOS Wine has no 32-bit host libraries. — [The Register, 2026-01-15](https://www.theregister.com/software/2026/01/15/wine-11-runs-windows-apps-in-linux-macos-better-than-ever/5087238)
- Wine's macOS build "is an x86-64 program" that runs on Apple Silicon "using Rosetta 2". On arm64 *Linux*, Wine uses FEX-Emu for x86 translation. — [The Register](https://www.theregister.com/software/2026/01/15/wine-11-runs-windows-apps-in-linux-macos-better-than-ever/5087238)
- History (2023, stale): Gcenx said macOS Wine packages fall back to WoW mode on Catalina and later. Only 32-bit CLI apps worked without unmerged patches; 32-bit GUI support in WineHQ wow64 builds was experimental. — [winetricks #2040](https://github.com/Winetricks/winetricks/issues/2040)
- Natively built aarch64 Wine on macOS did not launch in a recent dev build: the loader was reported as a "Malformed Mach-O file". — [Wine Bug 58567](https://list.winehq.org/hyperkitty/list/wine-bugs@list.winehq.org/thread/AIEGB45LZWRUP7UAVUWQPPRXFVZU5I7L/)
- Community fork `aabluedragon/wine` is "optimized for macOS builds (Apple Silicon)". It is based on wine-11.14, has a full macOS build recipe with WoW64, MoltenVK/Vulkan and bundled deps, and fixes legacy-GL extension detection (unverified). — [GitHub aabluedragon/wine](https://github.com/aabluedragon/wine)

**CrossOver (CodeWeavers; proprietary, paid; its Wine changes are LGPL)**
- Historically, CrossOver ran 32-bit Windows apps on 64-bit-only macOS via "wine32on64", which used a modified LLVM/Clang to build 32→64 thunks. — [Wikipedia: CrossOver](https://en.wikipedia.org/wiki/CrossOver_(software))
- CrossOver 24 was based on Wine 9.0 (Feb 2024). — [AlternativeTo](https://alternativeto.net/news/2024/2/crossover-24-released-with-wine-9-0-and-support-for-more-games-on-macos)
- CrossOver 26 shipped 2026-02-10/11 with Wine 11.0, D3DMetal 3.0, DXMT v0.72, vkd3d 1.18 and Wine Mono 10.4.1. — [AlternativeTo, 2026-02-11](https://alternativeto.net/news/2026/2/crossover-26-released-with-wine-11-ntsync-on-linux-and-support-for-many-new-games-on-mac)
- The CrossOver Preview of 2026-07-31 "includes native ARM64 support for macOS". CodeWeavers made "a custom version of FEX compatible with macOS", and the ARM64 pieces require macOS 26.5 or later (snippet). — [CodeWeavers blog "The Right to Bear ARM64 on Mac"](https://www.codeweavers.com/blog/mjohnson/2026/7/31/crossover-preview-the-right-to-bear-arm64-on-mac); [MacRumors thread](https://forums.macrumors.com/threads/crossover-announces-arm64-support.2486233/)
- Stable CrossOver 26 still relies on Rosetta 2. CrossOver 27 "will use native ARM64 Wine components and FEX". One review expects early 2027 (secondary source). CodeWeavers reportedly confirmed that CrossOver 27 removes 32-bit bottles entirely, while saying "almost all 32-bit applications run inside a 64-bit bottle". — [machow2 CrossOver 26 review](https://machow2.com/crossover-mac-review/); [machow2 32-bit apps 2026](https://machow2.com/run-32-bit-apps-mac/)
- An independent FEX-on-macOS port also exists. — [GitHub Jpkovas/FEX_MacOs](https://github.com/Jpkovas/FEX_MacOs)

**Apple Game Porting Toolkit (GPTK) / D3DMetal**
- A GPTK beta update added support for 32-bit games (per Wikipedia's Sonoma article; no primary Apple source found). — [Wikipedia: macOS Sonoma](https://en.wikipedia.org/wiki/MacOS_Sonoma)
- **D3DMetal covers only DX11/DX12 and is 64-bit only.** It does not support DX9, so it cannot handle D3D8/D3D9 games. — [carette.xyz deep dive](https://carette.xyz/posts/deep_dive_into_crossover/); [pyrosoft DXVK vs D3DMetal](https://pyrosoft.pro/blog/dxvk-vs-d3dmetal); [highball PR #142](https://github.com/gauthierpiarrette/highball/pull/142)
- A CodeWeavers forum poster argues that GPTK depends on Rosetta 2 because its Wine base does (opinion). — [CodeWeavers forum](https://www.codeweavers.com/support/forums/general/?t=27&forumc__=&forumcurPos=450&msg=330322)
- One guide says the arm64 CrossOver Preview targets macOS 27 and GPTK 4 (secondary, unverified). — [blendlogic guide](https://blendlogic.com/posts/crossover-mac-gaming-guide.html)

**Whisky**
- Upstream was archived on 2025-05-11 and is read-only. It "will not be upgrading to WINE 8+" and there will be no app-specific fixes. It was built on CrossOver 22.1.1 plus GPTK. — [GitHub Whisky-App/whisky](https://github.com/Whisky-App/whisky); [AppleInsider 2025-04-16](https://appleinsider.com/articles/25/04/16/whisky-development-ends-on-macos-to-help-wine-flourish)
- As of Oct 2026, fresh installs fail because the WhiskyWine runtime download returns a 404. The community fork `frankea/Whisky` continues (needs macOS 15+, Apple Silicon), and `brew install --cask whisky` still installs the dead original. — [Technobezz](https://www.technobezz.com/how-to-use-whisky-on-mac); [frankea/Whisky](https://github.com/frankea/Whisky)

**Kegworks / Wineskin → Sikarugir**
- Kegworks is the Wineskin successor and supports macOS 10.15.4 and later. It offers D3DMetal (64-bit D3D11/12) and DXMT toggles. — [GitHub gxgl/Kegworks](https://github.com/gxgl/Kegworks)
- It has reportedly been renamed Sikarugir and targets Tahoe and Apple Silicon (secondary). — [machow2](https://machow2.com/kegworks-officially-renamed-to-sikarugir/)
- An anecdotal dyld crash was reported on macOS 26.2. — [itch.io](https://itch.io/profile/phenomenal32)

### Inferences
- Today the runtime chain for WC3 1.26a on a Mac is: x86-64 Wine (Rosetta 2) → WoW64 thunks → i386 Game.dll, which runs as 32-bit code under Rosetta (see §2). The Rosetta phase-out (§2) is an existential deadline for this chain. The CrossOver/FEX path is the industry's answer.
- GPTK and D3DMetal add nothing for WC3. It is D3D8 (§4), so it goes through wined3d or DXVK, not D3DMetal.

### Gaps
- CodeWeavers' full arm64 post (403) was not read: FEX i386 coverage, performance and GPU path are unverified.
- No primary Apple source was found for GPTK 32-bit support.
- I could not confirm whether upstream WineHQ macOS packages for Wine 10/11 run 32-bit *GUI/D3D* apps well in new WoW64 mode, or still need CrossOver patches.

## 2. Rosetta 2, Box86/Box64, FEX-Emu, Hangover: dynamic translators on macOS arm64

### Takeaway
Rosetta 2 does **not** run standalone 32-bit x86 Mach-O apps; macOS dropped i386 in Catalina. Wine instead runs 32-bit Windows code inside a 64-bit process (wine32on64 / WoW64). That Rosetta executes the 32-bit code segments in this case is background knowledge; I found no source for it in this session. Apple said at WWDC25 that macOS 27 is the last release with full Rosetta, and macOS 28 (2027) keeps only a gaming subset. Hangover, Box64 and upstream FEX target Linux. The only macOS FEX is CodeWeavers' custom fork (plus a hobby port).

### Cited Findings
- Rosetta 2 "can only translate 64-bit Intel apps. It doesn't support 32-bit apps". 32-bit macOS apps were removed in Catalina (10.15). — [Apple Community](https://discussions.apple.com/thread/253527701)
- Rosetta for Linux VMs also does not cover i386. — [Finch #218](https://github.com/runfinch/finch/issues/218); [UTM Debian Rosetta](https://mac.getutm.app/gallery/debian-12-rosetta)
- WWDC 2025: Rosetta 2 stays fully available through macOS 27. From macOS 28, only "a subset" is kept for older unmaintained Intel games. — [MacRumors 2025-06-10](https://www.macrumors.com/2025/06/10/apple-to-phase-out-rosetta-2/); [Wikipedia: Rosetta](https://en.wikipedia.org/wiki/Rosetta_(software))
- OSNews (June 2026) reports macOS 27 drops Intel Macs and is the last release with Rosetta 2. That headline is stronger than Apple's "subset" wording, so the two conflict. — [OSNews](https://www.osnews.com/story/145279/macos-27-drops-intel-support-will-be-last-release-with-rosetta-2/); [MacG 2026-06](https://www.macg.co/macos/2026/06/avec-macos-27-apple-prepare-deja-la-fin-de-rosetta-2-prevue-dans-macos-28-309177)
- One anecdotal report says a macOS 27 update uninstalled Rosetta for some users, which broke PortingKit and Wine ports (Sept 2026, single source). — [paulthetall.com](https://www.paulthetall.com/rosetta-de-installed-on-mac-os-27-golden-gate/)
- It is unclear how Apple's gaming subset will apply to GPTK and CrossOver. — [BigGo](https://biggo.com/news/202510291336_rosetta-2-sunset-developer-concerns)
- Hangover (LGPL Wine + FEX or Box64) runs x86 and x86-64 Windows apps on **arm64 Linux**. It dropped QEMU in 11.0 and upstreamed box64cpu.dll as WowBox64.dll. Recent releases bundle FEX 2605–2608 and Box64 v0.4.2–0.4.4. I found no macOS support. — [Hangover releases](https://github.com/AndreRH/hangover/releases); [Phoronix Hangover 10.14](https://www.phoronix.com/news/Hangover-10.14); [lavx Hangover 11.0](https://news.lavx.hu/article/hangover-11-0-release-unlocks-windows-x86-apps-on-arm64-linux)
- CrossOver's Linux ARM64 Preview integrated FEX for i386 and x86-64 before the Mac version did. — [machow2](https://machow2.com/crossover-mac-review/); [HN](https://news.ycombinator.com/item?id=45999900)

### Inferences
- For option (b), running WC3 today: it works only while Rosetta exists. After macOS 28, users depend on Apple's game subset covering Wine's usage, or on CrossOver 27+/FEX.
- For option (a), a static recompile: removing the dynamic translator is the main value proposition. FEX's i386 frontend, together with Wine's WoW64 PE layer, is the closest open-source prior art for 32-bit x86 → arm64 with Win32 thunks. Box64's WowBox64.dll does the same job.
- Box86, the 32-bit sibling of Box64, needs a 32-bit ARM host. Apple Silicon has no AArch32, so Box86 cannot run there. This comes from architecture knowledge; I found no source for it in this session.

### Gaps
- No Apple primary doc was fetched to confirm the exact scope of the macOS 28 "subset".
- No mainline FEX or Box64 macOS host support was found.

## 3. Winelib: linking Wine's DLL implementations into a native arm64 process, and licensing

### Takeaway
Winelib, which builds Win32 source against Wine as native Unix ELF or Mach-O, is legacy. Since Wine 8 every module builds as **PE**, with a separate Unix-side syscall layer. The ".dll.so" mixed builds still work but lose new-WoW64 features, and 32-bit ELF dlls cannot be built in new-WoW64 mode. Native aarch64 Wine on macOS was still broken in recent dev builds. Wine is **LGPL-2.1**: proprietary code may link against it dynamically, but modified Wine source must be released.

### Cited Findings
- Wine 8.0: all modules can be built as PE. Mixed ELF ".dll.so" builds are still supported for Winelib apps, but "won't support features enabled by the NT syscall interface, such as WoW64 without 32-bit libraries". — [Wine 8.0 notes via Admin Magazine](https://admin-magazine.com/News/Wine-8.0-Released)
- A maintainer said 32-bit ELF dlls cannot be built in new wow64 mode and recommended building such code as PE. — [Bug 58377 winegcc -m32](https://list.winehq.org/hyperkitty/list/wine-bugs@list.winehq.org/thread/GYU4T2FJDR5MVSGCD3ID7G253EA7KNJS/)
- Wine 10 macOS clang build: DLLEXT handling breaks creation of the `.a` import libraries, so winegcc cannot link libadvapi32 and others. — [Wine bug thread](https://list.winehq.org/hyperkitty/list/wine-bugs@list.winehq.org/thread/BVK2ADK7KFDKHCXU7H3LWLDQFSZSC5DH/)
- Native aarch64 Wine on macOS fails with a "Malformed Mach-O" loader. — [Bug 58567](https://list.winehq.org/hyperkitty/list/wine-bugs@list.winehq.org/thread/AIEGB45LZWRUP7UAVUWQPPRXFVZU5I7L/)
- Wine 9.0 added running Windows apps on ARM64, tied to the completed PE/Unix split. — [Ubunlog Wine 9.0](https://en.ubunlog.com/wine-9-0/)
- Old (2003) Winelib HOWTO docs, for historical reference. — [HOWTO-winelib](https://goma.googlesource.com/wine/+/refs/tags/wine-20030618/documentation/HOWTO-winelib)
- Wine is LGPLv2.1 (wiki.winehq.org/Licensing). A WineHQ moderator declined to answer the static-linking question, saying to ask a lawyer. — [WineHQ forum](https://forum.winehq.org/viewtopic.php?p=113945)
- LGPL does not force a commercial publisher to release the whole application, but modified library source must be released (Parallels case). — [BetaNews](https://betanews.com/article/does-a-leading-windows-environment-for-mac-violate-the-lgpl/)
- Precedent: Hangover and CrossOver-arm64 are, in effect, "native arm64 Wine hosting translated x86 guest code". Guest calls cross into native arm64 Wine DLLs through WoW64 thunks. — [Hangover](https://github.com/AndreRH/hangover/releases); [CodeWeavers arm64](https://www.codeweavers.com/blog/mjohnson/2026/7/31/crossover-preview-the-right-to-bear-arm64-on-mac)

### Inferences
- The most viable way to back recompiled WC3 code with Wine is not classic Winelib. Instead, emit the recompiled code as an **arm64 PE**, which could be ARM64EC or arm64 with 32-bit pointer thunks, and run it inside an arm64 Wine prefix. Arm64 Wine on macOS is now real via CrossOver Preview, while upstream native aarch64 on macOS was still broken in recent dev builds (Bug 58567). Alternatively, write a thin custom HLE layer for only the APIs the game imports, and borrow Wine pieces dynamically.
- WC3 is a 32-bit pointer program. Recompiled code must either keep a 32-bit address space (low-4GB mapping) and thunk structs to Wine's 64-bit APIs, as Wine's WoW64 does, or reuse Wine's wow64 thunk layer directly.
- LGPL linking: dynamically link unmodified or published Wine dylibs/DLLs, and ship Wine source plus modifications. Static linking requires providing relinkable objects. The recompiled game itself does not have to be LGPL.

### Gaps
- I found no public "static recompile + Winelib" project that uses Wine this way on macOS.
- No authoritative legal FAQ from WineHQ was fetched.

## 4. Graphics: which D3D WC3 1.26a uses, and translation paths

### Takeaway
WC3 1.26a on Windows is a **Direct3D 8.1** title by default; `-opengl` on the command line switches to its OpenGL renderer. The Mac-native 1.26 client was OpenGL, while the later 1.3x Mac builds use `-graphicsapi` and Metal. Under Wine the D3D8 options are wined3d (to OpenGL or Vulkan), DXVK ≥2.4 d3d8 on MoltenVK, d3d8to9 followed by a D3D9 path, or experimental D3D9→Metal drivers. D3DMetal and DXMT do not apply.

### Cited Findings
- WC3 errors with "Please ensure you have DirectX 8.1 or newer". — [Wine Bug 1211 (2003)](https://list.winehq.org/pipermail/wine-bugs/2003-June/005641.html); [Vogons](https://www.vogons.org/viewtopic.php?p=1190556)
- CodeWeavers tip: "To switch to OpenGL, just add -opengl to the end of the command line" (Windows build). — [CodeWeavers tip](https://codeweavers.com/compatibility/crossover/tips/warcraft-iii-reign-of-chaos/use-opengl-instead-of-direct3d)
- Blizzard FAQ (classic era): "We support Direct3D and OpenGL". — [classic.battle.net FAQ](https://classic.battle.net/war3/faq/features.shtml)
- Later Mac builds take `-graphicsapi OpenGL|Direct3D9|Metal`. Forum posters say ≤1.31 is the last version supporting OpenGL on Mac (forum claims). — [Blizzard forum](https://us.forums.blizzard.com/en/warcraft3/t/mac-unable-to-initialize-graphics/6817); [Blizzard forum](https://us.forums.blizzard.com/en/warcraft3/t/unable-to-open-after-new-patch-on-mac/6317/18)
- A Linux/Proton user ran WC3 with a dxwrapper `d3d8.dll` and `WINEDLLOVERRIDES="d3d8=n"`. — [pengwings wiki](https://pengwings.theleruby.com/Warcraft_III)
- DXVK added Direct3D 8 support in v2.4 (July 2024). DXVK runs on macOS via MoltenVK. — [Wikipedia: DXVK](https://en.wikipedia.org/wiki/DXVK); [carette.xyz](https://carette.xyz/posts/deep_dive_into_crossover/)
- d3d8to9 by crosire converts D3D8 API calls and shaders to D3D9. It is BSD 2-clause, built from source with VS2013+ and needs legacy D3DX. — [ReShade forum](https://reshade.me/releases/419-d3d8to9]); [fork README](https://github.com/Fanatic-64/d3d8to9)
- D3DMetal is DX11/12 and 64-bit only. DXMT is D3D10/11 only; its maintainer said x86 support is "really tricky, because we don't have a x86 Metal API". — [highball PR](https://github.com/gauthierpiarrette/highball/pull/142); [DXMT discussion #4](https://github.com/3Shain/dxmt/discussions/4)
- Experimental D3D9→Metal drivers:
  - d9mt (Wine on Apple Silicon, 32 and 64-bit, "only a few games" tested). — [jdrly/d9mt](https://github.com/jdrly/d9mt); [neo773/d9mt](https://github.com/neo773/d9mt)
  - mtld3d (D3D9 on Metal; D3D8 planned). — [trozzelle/mtld3d](https://github.com/trozzelle/mtld3d)
  - UTM's d3dmetal-native. — [utmapp/d3dmetal-native](https://github.com/utmapp/d3dmetal-native)
- The CodeWeavers WC3 1.26a guide (CrossOver 25.0.1, Sonoma) recommends a dedicated bottle, winetricks components, a windowed config and the "D3DMetal" backend (snippet). This conflicts with D3DMetal's DX11/12-only scope; in practice it likely falls back to wined3d for d3d8. — [CodeWeavers forum](https://www.codeweavers.com/compatibility/crossover/forum/warcraft-iii-patch-126a?msg=332996)

### Inferences
- For option (a), a static recompile: the cleanest target is to intercept D3D8 at the COM interface and implement it natively on Metal, with mtld3d as a prior-art reference for D3D9/8 on Metal. Alternatively, reuse WC3's own OpenGL renderer path (`-opengl`) on a GL→Metal layer; macOS still ships deprecated OpenGL 4.1. Taking the OpenGL path avoids D3D entirely.
- For option (b), today: wined3d (GL), or DXVK-d3d8 on MoltenVK, inside CrossOver or Wine. Trying `-opengl` is a cheap test.

### Gaps
- I found no source confirming exactly which D3D8 or GL renderer CrossOver uses for WC3 1.26a, and no benchmarks comparing renderers.

## 5. Audio, network and other subsystems (Miles/Mss32, DirectSound, Winsock)

### Takeaway
WC3 1.26a ships Miles Sound System (`Mss32.dll`), which sits on DirectSound. Under Wine, the real Mss32.dll runs as guest code over Wine's dsound → winecoreaudio (CoreAudio). I found no Miles replacement project specific to WC3.

### Cited Findings
- Games reach DirectSound through mss32.dll, and a dsound wrapper in the game folder may not be picked up (GTA example). — [libertycity EAX Alchemy fix](https://libertycity.net/files/gta-vice-city/128403-eax-alchemy-fix.html)
- Historic Wine bugs: "[Bug 4035] Dsound related hang in Warcraft 3" (2006), and OSS noise with WC3 (Wine 0.9.44). Both are stale. — [wine-bugs April 2006](https://list.winehq.org/pipermail/wine-bugs/2006-April/date.html); [WineHQ forum](https://forum.winehq.org/viewtopic.php?p=16699)

### Inferences
- For option (a): either recompile Mss32.dll along with the game, since it is x86 code like the rest, and back its dsound/waveOut imports with CoreAudio. Or HLE the subset of the Miles API that Game.dll imports (AIL_* functions) onto CoreAudio or AVAudioEngine. Winsock maps nearly 1:1 to BSD sockets, and Wine's ws2_32 is the reference implementation.

### Gaps
- No source was found for the exact Miles API version or call set in WC3 1.26a, or for any open-source Miles reimplementation.

## 6. Does WC3 1.26a plus DotA run on Mac today, and how well?

### Takeaway
Yes, with tweaks. It works in CrossOver (25/26) and older Whisky. Known issues include an Options-menu crash in one shared bottle and poor DotA FPS on M1 in an older report (9–20 FPS). I found no iCCup, Eurobattle or ProtectedDotA-specific Mac reports.

### Cited Findings
- A CodeWeavers user guide reports WC3 1.26a "running reliably" in CrossOver 25.0.1 on Sonoma, using a dedicated bottle, winetricks, windowed mode and the D3DMetal setting (snippet; page 403). — [CodeWeavers forum](https://www.codeweavers.com/compatibility/crossover/forum/warcraft-iii-patch-126a?msg=332996)
- A prebuilt CrossOver bottle (RoC and TFT) on Apple Silicon, Aug 2025: "clicking on Options will cause your game to crash", and Battle.net does not work. — [Johnny Matthews blog 2025-08-06](https://johnnymatthews.dev/blog/2025-08-06-install-the-original-warcraft-3-on-apple-silicon/)
- An M1 user (2021, stale) got DotA / DotA LoD 6.88 at "9 to 20 fps" under CrossOver/Wine even with DXVK (snippet). — [MacRumors thread](https://forums.macrumors.com/threads/warcraft-iii-tft-1-26a-on-macbook-pro-m1.2283317/)
- Similar older Blizzard 32-bit clients, such as WoW 3.3.5, run via CrossOver and Whisky with mixed results. — [Warmane forum](https://forum.warmane.com/showthread.php?t=473276); [rk.edu.pl](https://rk.edu.pl/en/running-old-world-of-warcraft-clients-on-apple-silicon-devices/)
- Reforged (a different client) is rated "Unplayable" in CrossOver. — [AppleGamingWiki](https://www.applegamingwiki.com/wiki/Warcraft_III:_Reforged)

### Inferences
- The practical baseline is CrossOver 26 with a 64-bit bottle (32-bit bottles are going away in CrossOver 27). Try wined3d versus DXVK-d3d8, and `-opengl`. Expect late-game DotA FPS to be CPU-bound, since a Rosetta-translated i386 game logic thread does the work. That is an assumption, but it is consistent with the M1 report.

### Gaps
- No iCCup, Eurobattle.net or ProtectedDotA / Garena / RGC Mac-specific reports were found.
- Anti-hack and launcher compatibility for those platforms under Wine is unknown.
- No 2026 benchmarks were found on M3/M4 hardware or the arm64 CrossOver Preview.
