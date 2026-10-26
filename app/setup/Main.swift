// reFrozen's first-run setup: the app's entry point.
//
//   reFrozen                      the setup window, or the game when setup is complete
//   reFrozen --setup <command>    the same steps without a window (tests, scripts):
//     status                      needs-install | needs-build | ready
//     prerequisites               one line per check; exit 1 if any fails
//     verify roc|tft|patch <path> the input's label, or why not (exit 1)
//     key                         a CD key on stdin: ok, or exit 1 (never echoed)
//     owner <name>                ok, or the problem (exit 1)
//     install <roc> <tft> <patch> <owner>   the two CD keys on stdin, one per line
//     build                       build the game module, "progress <n>/<total>" lines
//     add-map <file>
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
    if state(paths) == .ready && !args.contains("--show-setup") { launchGame(paths) }
    SetupApp.main()
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
      SetupView(model: model)
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
      var progress = BuildProgress()
      cancelOnSignal(step)
      let status = (try? step.run { line in
        progress.read(line)
        log.write(line)
        if line.hasPrefix("compiled ") { print("progress \(progress.done)/\(progress.total)") } else { print(line) }
      }) ?? -1
      if status != 0 { print("no: \(buildFailure(status))"); return 1 }
      print("built: \(paths.module.path)")
      return 0
    case ("add-map", 1):
      do { print("added: \(try copyMap(URL(fileURLWithPath: rest[0]), paths: paths).path)"); return 0 }
      catch { print("no: \(error)"); return 1 }
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
        m.rocKey = "XXXXXXXXXXXXXXXXXXXXXXXXXX"
        m.owner = "Player"
      }),
      ("4-build", { m in
        m.page = .work
        m.working = true
        m.phase = "Building the game for this Mac"
        m.progress = 0.37
        m.lines = ["— Installing Warcraft III and patching it to 1.26a", "installed: RoC 1.21b", "installed: TFT 1.21b",
                   "patch 1.26a: 723 files", "— Building the game for this Mac",
                   "reFrozen game module: 8 jobs, Apple clang 21.0.0", "compiling 243 files"]
          + (1...12).map { "compiled gen_game_\(String(format: "%03d", $0)).cpp" }
      }),
      ("4-failed", { m in
        m.page = .work
        m.failure = "a file did not compile"
        m.lines = ["— Building the game for this Mac", "compiling 243 files", "build failed: a file did not compile"]
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
    for (name, configure) in pages {
      let model = SetupModel(paths: paths)
      configure(model)
      let host = NSHostingView(rootView: SetupView(model: model))
      host.frame = NSRect(x: 0, y: 0, width: 760, height: 560)
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
}
