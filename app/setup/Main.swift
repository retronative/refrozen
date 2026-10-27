// reFrozen's first-run setup: the app's entry point.
//
//   reFrozen                      the setup wizard, or the Mini Launcher once setup is complete
//   reFrozen --setup <command>    the same steps without a window (tests, scripts):
//     status                      needs-install | needs-build | ready
//     prerequisites               one line per check; exit 1 if any fails
//     verify roc|tft|patch <path> the input's label, or why not (exit 1)
//     key                         a CD key on stdin: ok, or exit 1 (never echoed)
//     owner <name>                ok, or the problem (exit 1)
//     install <roc> <tft> <patch> <owner>   the two CD keys on stdin, one per line
//     build                       build the game module; "progress <percent> <stage>: <status>" lines
//     replay-progress [build] [estimate=<s>] [floor=<f>]
//                                 the overall progress for timed lines on stdin, "<seconds> <line>";
//                                 "<seconds> ?" asks, "<seconds> #stop" stops, "<seconds> #verified"
//                                 verifies; per line "<shown> <stage> <active> <status>"
//     sweep <track>               the progress light over one sweep of a <track>-point bar:
//                                 per 1/60 s "<seconds> <lead> <start> <end>", or "<seconds> -"
//     sweep-light <fill> <x> [active]   the light's opacity at <x> points on a bar filled <fill>
//     fill-colors                 the fill's colours, start to edge, as hex
//     edge <fill> <track>         the edge glow: "<centre> <from> <to>" in points
//     edge-rays [still]           the edge's rays every 0.25 s for 3 s: "<seconds> <angle> <length>"
//     bars <dir>                  the progress bar in sample states as one PNG (bars.png)
//     bar-bench <seconds> <value> the bar sweeping in a window for <seconds>: the CPU time it took
//     details                     the Show/Hide Details control: "<expanded> <title>|<label>|<value>"
//     add-map <file>              import a map (never overwrites one)
//     play                        start the game (the Mini Launcher's Start Game)
//     render <dir>                the window's pages as PNGs (previews)
// Paths: REFROZEN_DATA (default ~/Library/Application Support/reFrozen) and
// REFROZEN_KIT (default the app's Resources/kit).

import AppKit
import SwiftUI

@main
enum Entry {
  static func main() {
    let args = Array(CommandLine.arguments.dropFirst())
    let paths = Paths.standard()
    if args.first == "--setup" {
      exit(SetupCLI.run(Array(args.dropFirst()), paths: paths))
    }
    SetupApp.main()  // the Mini Launcher when setup is complete, else the wizard
  }
}

struct SetupApp: App {
  @StateObject private var model: SetupModel

  init() {
    let paths = Paths.standard()
    Theme.registerFonts(kit: paths.kit)
    NSApplication.shared.setActivationPolicy(.regular)
    _model = StateObject(wrappedValue: SetupModel(paths: paths))
  }

  var body: some Scene {
    Window("reFrozen", id: "setup") {
      Group {
        if model.showLauncher { LauncherView(model: model) } else { SetupView(model: model) }
      }
      .onAppear { NSApplication.shared.activate(ignoringOtherApps: true) }
    }
    .windowResizability(.contentSize)
    .windowStyle(.hiddenTitleBar)
  }
}

enum SetupCLI {
  static func run(_ args: [String], paths: Paths) -> Int32 {
    guard let command = args.first else { return usage() }
    let rest = Array(args.dropFirst())
    switch (command, rest.count) {
    case ("status", 0):
      print(["needs-install", "needs-build", "ready"][[SetupState.needsInstall, .needsBuild, .ready]
        .firstIndex(of: state(paths))!])
      return 0
    case ("prerequisites", 0):
      let list = prerequisites(paths)
      for p in list { print("\(p.ok ? "ok  " : "FAIL") \(p.name): \(p.detail)") }
      return list.allSatisfy(\.ok) ? 0 : 1
    case ("verify", 2):
      guard let input = Input(rawValue: rest[0]) else { return usage() }
      switch verifyInput(input, at: URL(fileURLWithPath: rest[1])) {
      case .success(let label): print("ok \(label)"); return 0
      case .failure(let e): print("no: \(e)"); return 1
      }
    case ("key", 0):
      let ok = normaliseKey(readLine() ?? "") != nil
      print(ok ? "ok" : "no: not a 26-character CD key")
      return ok ? 0 : 1
    case ("owner", 1):
      if let p = ownerProblem(rest[0]) { print("no: \(p)"); return 1 }
      print("ok")
      return 0
    case ("install", 4):
      let urls = rest[0...2].map { URL(fileURLWithPath: $0) }
      for (input, url) in zip(Input.allCases, urls) {
        if case .failure(let e) = verifyInput(input, at: url) { print("no: \(input.rawValue): \(e)"); return 1 }
      }
      guard let roc = normaliseKey(readLine() ?? ""), let tft = normaliseKey(readLine() ?? "") else {
        print("no: two 26-character CD keys are needed on stdin")
        return 1
      }
      if let p = ownerProblem(rest[3]) { print("no: owner: \(p)"); return 1 }
      let i = Installation(roc: urls[0], tft: urls[1], patch: urls[2], rocKey: roc, tftKey: tft, owner: rest[3])
      let step = installStep(i, paths: paths)
      let log = SetupLog(paths: paths)
      cancelOnSignal(step)
      do {
        try install(i, paths: paths, step: step) { print($0); log.write($0) }
        print("installed: \(paths.game.path)")
        return 0
      } catch {
        print("no: \(error)")
        return 1
      }
    case ("build", 0):
      let step = buildStep(paths: paths)
      let log = SetupLog(paths: paths)
      var progress = SetupProgress(installing: false)
      cancelOnSignal(step)
      let status = (try? step.run { line in
        let before = progress
        progress.read(line)
        log.write(line)
        if progress != before { print("progress \(progress.percent(at: Date()))% \(progress.stage): \(progress.status)") }
        if !line.hasPrefix("compiled ") && !line.hasPrefix("prepared ") { print(line) }
      }) ?? -1
      if status != 0 { print("no: \(buildFailure(status))"); return 1 }
      guard state(paths) == .ready else { print("no: the built game module could not be verified"); return 1 }
      progress.verified()
      print("progress \(progress.percent(at: Date()))% \(progress.stage): \(progress.status)")
      print("built: \(paths.module.path)")
      return 0
    case ("replay-progress", _):
      let opt = { (k: String) in rest.first { $0.hasPrefix(k + "=") }.flatMap { Double($0.dropFirst(k.count + 1)) } }
      var progress = SetupProgress(installing: !rest.contains("build"), liftEstimate: opt("estimate") ?? 60,
                                   floor: opt("floor") ?? 0)
      let t0 = Date(timeIntervalSinceReferenceDate: 0)
      while let input = readLine() {
        guard let space = input.firstIndex(of: " "), let t = Double(input[..<space]) else { continue }
        let now = t0.addingTimeInterval(t), line = String(input[input.index(after: space)...])
        switch line {
        case "#verified": progress.verified()
        case "#stop": progress.stop(at: now)
        case "?": break
        default: progress.read(line, at: now)
        }
        print(String(format: "%.4f", progress.display(at: now)), progress.stage, progress.active(at: now) ? 1 : 0,
              progress.status)
      }
      return 0
    case ("sweep", 1):
      guard let track = Double(rest[0]) else { return 2 }
      let p = FrostSweep.period(track: track)
      for i in 0..<Int((p * 60).rounded(.up)) {
        let t = Double(i) / 60
        if let v = FrostSweep.visible(track: track, at: t) {
          print(String(format: "%.4f %.2f %.2f %.2f", t, FrostSweep.lead(track: track, at: t), v.lowerBound, v.upperBound))
        } else {
          print(String(format: "%.4f -", t))
        }
      }
      return 0
    case ("sweep-light", 2), ("sweep-light", 3):
      guard let fill = Double(rest[0]), let x = Double(rest[1]) else { return 2 }
      print(String(format: "%.2f", FrostSweep.opacity(at: x, fill: fill, active: rest.count == 3)))
      return 0
    case ("fill-colors", 0):
      print(FrostFill.colors.map { String(format: "%06X", $0) }.joined(separator: " "))
      return 0
    case ("edge", 2):
      guard let fill = Double(rest[0]), let track = Double(rest[1]) else { return 2 }
      let e = FrostEdge.extent(fill: fill, track: track)
      print(String(format: "%.2f %.2f %.2f", FrostEdge.center(fill: fill), e.lowerBound, e.upperBound))
      return 0
    case ("edge-rays", 0), ("edge-rays", 1):
      for i in 0...12 {
        let t = Double(i) / 4, r = FrostEdge.rays(at: t, reduceMotion: rest.first == "still")
        print(String(format: "%.2f %.4f %.4f", t, r.angle, r.length))
      }
      return 0
    case ("bars", 1):
      return MainActor.assumeIsolated { Previews.bars(to: URL(fileURLWithPath: rest[0]), paths: paths) }
    case ("bar-bench", 2):
      guard let secs = Double(rest[0]), let value = Double(rest[1]) else { return 2 }
      return MainActor.assumeIsolated { Previews.benchBar(seconds: secs, value: value) }
    case ("details", 0):
      for expanded in [false, true] {
        print(expanded ? 1 : 0, [DetailsControl.title(expanded: expanded), DetailsControl.accessibilityLabel,
                                 DetailsControl.accessibilityValue(expanded: expanded)].joined(separator: "|"))
      }
      return 0
    case ("add-map", 1):
      do {
        switch try importMap(URL(fileURLWithPath: rest[0]), paths: paths) {
        case .added(let u): print("added: \(u.path)")
        case .alreadyInstalled(let u): print("already installed: \(u.path)")
        case .renamed(let u): print("added as: \(u.path)")
        }
        return 0
      } catch {
        print("no: \(error)")
        return 1
      }
    case ("play", 0):
      guard state(paths) == .ready else { print("no: setup is not complete (\(state(paths)))"); return 1 }
      launchGame(paths)
    case ("render", 1):
      return MainActor.assumeIsolated { Previews.render(to: URL(fileURLWithPath: rest[0]), paths: paths) }
    default:
      return usage()
    }
  }

  private static func usage() -> Int32 {
    print("usage: reFrozen --setup status|prerequisites|verify <input> <path>|key|owner <name>|"
      + "install <roc> <tft> <patch> <owner>|build|add-map <file>|render <dir>")
    return 2
  }

  // Ctrl+C or a kill cancels the step cleanly (the builder stops its workers).
  private static var signalSources: [DispatchSourceSignal] = []
  private static func cancelOnSignal(_ step: Step) {
    for sig in [SIGINT, SIGTERM] {
      signal(sig, SIG_IGN)
      let s = DispatchSource.makeSignalSource(signal: sig, queue: .global())
      s.setEventHandler { step.cancel() }
      s.resume()
      signalSources.append(s)
    }
  }
}

// The window's pages rendered to PNG at 2x, with sample states (no input is
// verified and nothing is installed).
@MainActor
enum Previews {
  static func render(to dir: URL, paths: Paths) -> Int32 {
    Theme.registerFonts(kit: paths.kit)
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    let pages: [(String, (SetupModel) -> Void)] = [
      ("1-welcome", { m in
        m.page = .welcome
        m.prereqs = [
          Prerequisite(name: "Apple silicon", ok: true, detail: "arm64"),
          Prerequisite(name: "macOS 14 or later", ok: true, detail: "macOS 27.0.1"),
          Prerequisite(name: "Free disk space", ok: true, detail: "38.4 GB free, 2.5 GB needed"),
          Prerequisite(name: "Apple's Command Line Tools", ok: false, detail: "needed to build the game on this Mac"),
        ]
      }),
      ("2-files", { m in
        m.page = .files
        let src = URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Code/retronative/DOTA/ICC Game client install")
        m.urls = [.roc: src.appendingPathComponent("Warcraft III 1.21b ROC Installer enGB"),
                  .tft: src.appendingPathComponent("Warcraft III 1.21b TFT Installer enGB")]
        m.checks = [.roc: .ok(knownInputs[.roc]!.label), .tft: .checking(0.42)]
      }),
      ("3-keys", { m in
        m.page = .keys
        m.rocKey = String(repeating: "X", count: 26)  // no key-shaped literal in the binary
        m.owner = "Player"
      }),
      ("4-build", { m in
        m.page = .work
        m.working = true
        m.phase = "Building the game for this Mac"
        m.started = Date().addingTimeInterval(-154)
        let ls: [String] = ["— Installing Warcraft III and patching it to 1.26a", "install RoC: {'file': 77}", "install TFT: {'file': 194}",
                  "patch 1.26a: {'disk': 147}", "— Building the game for this Mac", "reFrozen game module 1234-abcd: 8 jobs"]
          + (1...11).map { i in "prepared module (\(i)/11)" } + ["lifting the game code", "compiling 244 files"]
          + (1...96).map { i in "compiled gen_game_\(String(format: "%03d", i)).cpp" }
        for l in ls { m.overall.read(l); m.lines.append(l) }
      }),
      ("4-lifting", { m in
        m.page = .work
        m.working = true
        m.phase = "Building the game for this Mac"
        m.started = Date().addingTimeInterval(-41)
        m.overall = SetupProgress(installing: false, liftEstimate: 63)
        m.showDetails = true
        let ls: [String] = ["— Building the game for this Mac", "reFrozen game module 1234-abcd: 8 jobs"] + (1...11).map { i in "prepared module (\(i)/11)" }
          + ["lifting the game code"]
        for l in ls { m.overall.read(l, at: Date().addingTimeInterval(-41)); m.lines.append(l) }
      }),
      ("4-failed", { m in
        m.page = .work
        m.failure = "a file did not compile"
        m.started = Date().addingTimeInterval(-131)
        m.finished = Date()
        m.overall = SetupProgress(installing: false)
        let ls: [String] = ["— Building the game for this Mac", "reFrozen game module 1234-abcd: 8 jobs"] + (1...11).map { i in "prepared module (\(i)/11)" }
          + ["lifting the game code", "compiling 244 files", "compiled gen_000.cpp", "build failed: a file did not compile"]
        for l in ls { m.overall.read(l); m.lines.append(l) }
      }),
      ("5-ready", { m in
        m.page = .done
        m.mapNote = "Added DotA v6.83dAI PMV 1.42 EN.w3x to Maps/Download"
      }),
    ]
    // A real window, drawn into a bitmap by this process: native controls
    // (text fields) render as they do on screen, and no screen recording
    // permission is involved.
    _ = NSApplication.shared
    let launcher: (String, (SetupModel) -> Void) = ("6-launcher", { m in
      m.showLauncher = true
      m.maps = ["DotA v6.83dAI PMV 1.42 EN.w3x", "reFrozen Import Test.w3x"]
      m.importNotes = ["Added reFrozen Import Test.w3x", "DotA v6.83dAI PMV 1.42 EN.w3x is already installed"]
    })
    for (name, configure) in pages + [launcher] {
      let model = SetupModel(paths: paths)
      model.showLauncher = false
      configure(model)
      let view = model.showLauncher ? AnyView(LauncherView(model: model)) : AnyView(SetupView(model: model))
      let host = NSHostingView(rootView: view)
      host.frame = model.showLauncher ? NSRect(x: 0, y: 0, width: 560, height: 330) : NSRect(x: 0, y: 0, width: 760, height: 560)
      let window = NSWindow(contentRect: host.frame, styleMask: [.borderless], backing: .buffered, defer: false)
      window.contentView = host
      window.appearance = NSAppearance(named: .darkAqua)
      host.layoutSubtreeIfNeeded()
      RunLoop.main.run(until: Date().addingTimeInterval(0.4))
      guard let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) else {
        print("no: cannot render \(name)")
        return 1
      }
      host.cacheDisplay(in: host.bounds, to: rep)
      try? rep.representation(using: .png, properties: [:])?.write(to: dir.appendingPathComponent("\(name).png"))
      print("rendered \(name).png")
    }
    return 0
  }
  // The bar in sample states, one row each, at one moment of the sweep (bars.png).
  static func bars(to dir: URL, paths: Paths) -> Int32 {
    Theme.registerFonts(kit: paths.kit)
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    _ = NSApplication.shared
    let t = 0.55  // the light about a third of the way along a 600-point track
    let rows: [(String, AnyView)] = [
      ("3 %, lifting", AnyView(FrostBar(value: 0.03, sweeping: true, frozenAt: t))),
      ("20 %", AnyView(FrostBar(value: 0.20, sweeping: true, frozenAt: t))),
      ("50 %", AnyView(FrostBar(value: 0.50, sweeping: true, frozenAt: t))),
      ("98 %", AnyView(FrostBar(value: 0.98, sweeping: true, frozenAt: t))),
      ("19 %, held (no measure yet)", AnyView(FrostBar(value: 0.19, active: true, sweeping: true, frozenAt: t))),
      ("20 %, stopped or failed", AnyView(FrostBar(value: 0.20, frozenAt: t))),
      ("100 %, done", AnyView(FrostBar(value: 1, frozenAt: t))),
      ("50 %, reduced motion", AnyView(FrostBar(value: 0.50, sweeping: true, frozenAt: t, stillPreview: true))),
    ]
    let sheet = VStack(alignment: .leading, spacing: 18) {
      ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
        VStack(alignment: .leading, spacing: 8) {
          Text(row.0).font(Theme.body(12)).foregroundStyle(Theme.ash)
          HStack(spacing: 10) {
            row.1.frame(width: 600)
            Text("…").font(Theme.body(12)).foregroundStyle(Theme.ash).frame(width: 40, alignment: .trailing)
          }
        }
      }
    }
    .padding(28)
    .background(Theme.slab)
    let host = NSHostingView(rootView: sheet)
    host.frame = NSRect(x: 0, y: 0, width: 720, height: 520)
    let window = NSWindow(contentRect: host.frame, styleMask: [.borderless], backing: .buffered, defer: false)
    window.contentView = host
    window.appearance = NSAppearance(named: .darkAqua)
    host.layoutSubtreeIfNeeded()
    RunLoop.main.run(until: Date().addingTimeInterval(0.4))
    guard let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) else { return 1 }
    host.cacheDisplay(in: host.bounds, to: rep)
    try? rep.representation(using: .png, properties: [:])?.write(to: dir.appendingPathComponent("bars.png"))
    print("rendered bars.png")
    return 0
  }

  // The bar sweeping in a window for `seconds`, on the app's own event loop (as the setup runs):
  // the process's CPU time over that span. Launch it as an app (`open`), so the window is active.
  static func benchBar(seconds: Double, value: Double) -> Int32 {
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)
    let host = NSHostingView(rootView: FrostBar(value: value, sweeping: true).frame(width: 600).padding(20).background(Theme.slab))
    host.frame = NSRect(x: 0, y: 0, width: 640, height: 48)
    let window = NSWindow(contentRect: host.frame, styleMask: [.titled], backing: .buffered, defer: false)
    window.contentView = host
    window.makeKeyAndOrderFront(nil)
    app.activate(ignoringOtherApps: true)
    var start = (cpu: 0.0, wall: Date())
    Timer.scheduledTimer(withTimeInterval: 1, repeats: false) { _ in
      start = (cpuSeconds(), Date())
      Timer.scheduledTimer(withTimeInterval: seconds, repeats: false) { _ in
        app.stop(nil)  // takes effect on the next event: post one
        app.postEvent(NSEvent.otherEvent(with: .applicationDefined, location: .zero, modifierFlags: [], timestamp: 0,
                                         windowNumber: 0, context: nil, subtype: 0, data1: 0, data2: 0)!, atStart: true)
      }
    }
    app.run()
    let c = cpuSeconds() - start.cpu, w = Date().timeIntervalSince(start.wall)
    print("active \(app.isActive) " + String(format: "cpu %.3f s over %.1f s (%.1f %% of one core)", c, w, 100 * c / w))
    return 0
  }

  nonisolated static func cpuSeconds() -> Double {
    var u = rusage()
    getrusage(RUSAGE_SELF, &u)
    return Double(u.ru_utime.tv_sec + u.ru_stime.tv_sec) + Double(u.ru_utime.tv_usec + u.ru_stime.tv_usec) / 1e6
  }
}
