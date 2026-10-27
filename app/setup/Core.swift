// The first-run setup's logic, without UI: what the window and the
// command-line mode (Main.swift) both drive.
//
// The player's own installers are checked by hash, installed and patched to
// 1.26a by the kit's installer (scripts/native_install.py on Apple's Python),
// then the game module is built on this Mac by the kit's builder
// (scripts/build_module.sh). Everything goes to the data folder,
// ~/Library/Application Support/reFrozen: game/ (the installed game), build/
// (the module), logs/. CD keys go to the installer on its standard input
// only: never in arguments, logs or files of ours.

import CryptoKit
import Foundation

enum Input: String, CaseIterable {
  case roc, tft, patch
}

struct KnownInput {
  let label: String
  let file: String?  // inside the chosen folder; nil: the chosen file itself
  let size: Int64
  let sha256: String
}

// The inputs reFrozen is verified with: the English (UK) 1.21b installers and
// the official 1.26a English patch. Only "Installer Tome.mpq" of an installer
// folder is read by the installer, so it is what identifies one.
let knownInputs: [Input: KnownInput] = [
  .roc: KnownInput(label: "Warcraft III: Reign of Chaos 1.21b (English)", file: "Installer Tome.mpq",
                   size: 645_534_718, sha256: "a88d5388f9c48f4538046ead9ae0f28a0874e1948cce0a1dfb2b8d906372a6c5"),
  .tft: KnownInput(label: "Warcraft III: The Frozen Throne 1.21b (English)", file: "Installer Tome.mpq",
                   size: 603_465_958, sha256: "43e33ad4b779f35419e4188759dbefba0b06e6ebf9ee2ad6a6181b60c37f480e"),
  .patch: KnownInput(label: "Patch 1.26a (English)", file: nil,
                     size: 58_718_061, sha256: "24d004397ab7f7c204b7e6312542f2269e212c43813e88f67b552ddd8a830ab2"),
]

func inputName(_ input: Input) -> String {
  switch input {
  case .roc: return "the Reign of Chaos installer folder"
  case .tft: return "the Frozen Throne installer folder"
  case .patch: return "the 1.26a patch (War3TFT_126a_English.exe)"
  }
}

struct SetupError: Error, CustomStringConvertible {
  let description: String
  init(_ d: String) { description = d }
}

// MARK: - Paths

struct Paths {
  let data: URL
  let kit: URL
  var game: URL { data.appendingPathComponent("game") }
  var build: URL { data.appendingPathComponent("build") }
  var module: URL { build.appendingPathComponent("current/war3.dylib") }
  var logs: URL { data.appendingPathComponent("logs") }
  var installMarker: URL { game.appendingPathComponent("reFrozen-install.json") }

  // REFROZEN_DATA and REFROZEN_KIT override the defaults (tests, development).
  static func standard() -> Paths {
    let env = ProcessInfo.processInfo.environment
    let data = env["REFROZEN_DATA"].map { URL(fileURLWithPath: $0) }
      ?? FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent("Library/Application Support/reFrozen")
    let kit = env["REFROZEN_KIT"].map { URL(fileURLWithPath: $0) }
      ?? Bundle.main.resourceURL!.appendingPathComponent("kit")
    return Paths(data: data, kit: kit)
  }
}

// MARK: - Prerequisites

struct Prerequisite {
  let name: String
  let ok: Bool
  let detail: String
}

// The install (1.1 GB), the builder's peak (0.6 GB) and the module (0.1 GB),
// with a margin.
let requiredFreeBytes: Int64 = 2_500_000_000

func commandLineToolsInstalled() -> Bool {
  // xcode-select -p first: without the tools, the /usr/bin shims would open
  // Apple's installer instead of failing.
  guard run("/usr/bin/xcode-select", ["-p"]).status == 0 else { return false }
  return run("/usr/bin/xcrun", ["--find", "clang++"]).status == 0
}

func prerequisites(_ paths: Paths) -> [Prerequisite] {
  var list: [Prerequisite] = []
  #if arch(arm64)
    list.append(Prerequisite(name: "Apple silicon", ok: true, detail: "arm64"))
  #else
    list.append(Prerequisite(name: "Apple silicon", ok: false, detail: "reFrozen runs on Apple silicon Macs only"))
  #endif
  let v = ProcessInfo.processInfo.operatingSystemVersion
  list.append(Prerequisite(name: "macOS 14 or later", ok: v.majorVersion >= 14,
                           detail: "macOS \(v.majorVersion).\(v.minorVersion).\(v.patchVersion)"))
  let free = freeBytes(near: paths.data)
  list.append(Prerequisite(name: "Free disk space", ok: free >= requiredFreeBytes,
                           detail: String(format: "%.1f GB free, %.1f GB needed", Double(free) / 1e9,
                                          Double(requiredFreeBytes) / 1e9)))
  let clt = commandLineToolsInstalled()
  list.append(Prerequisite(name: "Apple's Command Line Tools", ok: clt,
                           detail: clt ? "installed" : "needed to build the game on this Mac"))
  return list
}

func freeBytes(near url: URL) -> Int64 {
  var u = url
  while !FileManager.default.fileExists(atPath: u.path) && u.path != "/" { u.deleteLastPathComponent() }
  let values = try? u.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey])
  return values?.volumeAvailableCapacityForImportantUsage ?? 0
}

// MARK: - Inputs

func sha256(of url: URL, progress: ((Double) -> Void)? = nil) throws -> String {
  let handle = try FileHandle(forReadingFrom: url)
  defer { try? handle.close() }
  let total = (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? Int64) ?? 0
  var hasher = SHA256()
  var done: Int64 = 0
  while let chunk = try handle.read(upToCount: 8 << 20), !chunk.isEmpty {
    hasher.update(data: chunk)
    done += Int64(chunk.count)
    if total > 0 { progress?(Double(done) / Double(total)) }
  }
  return hasher.finalize().map { String(format: "%02x", $0) }.joined()
}

// The input's label if `url` is the expected one, else why not.
func verifyInput(_ input: Input, at url: URL, progress: ((Double) -> Void)? = nil) -> Result<String, SetupError> {
  let known = knownInputs[input]!
  let file = known.file.map { url.appendingPathComponent($0) } ?? url
  var isDir: ObjCBool = false
  guard FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir) else {
    return .failure(SetupError("\(url.lastPathComponent) does not exist"))
  }
  if known.file != nil {
    guard isDir.boolValue, FileManager.default.fileExists(atPath: file.path) else {
      return .failure(SetupError("\(url.lastPathComponent) has no Installer Tome.mpq: choose \(inputName(input))"))
    }
  } else if isDir.boolValue {
    return .failure(SetupError("choose the patch file itself, not a folder"))
  }
  let size = (try? FileManager.default.attributesOfItem(atPath: file.path)[.size] as? Int64) ?? -1
  guard let digest = try? sha256(of: file, progress: progress) else {
    return .failure(SetupError("\(file.lastPathComponent) cannot be read"))
  }
  if size == known.size && digest == known.sha256 { return .success(known.label) }
  if let other = knownInputs.first(where: { $0.key != input && $0.value.sha256 == digest }) {
    return .failure(SetupError("this is \(other.value.label): choose it in its own place"))
  }
  return .failure(SetupError("not \(known.label): reFrozen is verified with that version only"))
}

// MARK: - CD keys and the owner's name (as scripts/native_install.py checks them)

let keyAlphabet = Set("246789BCDEFGHJKMNPRTVWXYZ")

// The key as the installer stores it (26 characters, upper case, no dashes
// or spaces), or nil.
func normaliseKey(_ text: String) -> String? {
  let k = text.filter { !$0.isWhitespace && $0 != "-" }.uppercased()
  return k.count == 26 && k.allSatisfy { keyAlphabet.contains($0) } ? k : nil
}

func ownerProblem(_ name: String) -> String? {
  guard let bytes = name.data(using: .windowsCP1252) else {
    return "use Western European characters only (the game stores the name in Windows-1252)"
  }
  if bytes.isEmpty || bytes.count > 62 { return "1 to 62 characters" }
  if bytes.contains(0) { return "no control characters" }
  return nil
}

// MARK: - Status

enum SetupState: Equatable {
  case needsInstall, needsBuild, ready
}

func kitStamp(_ paths: Paths) -> String? {
  (try? String(contentsOf: paths.kit.appendingPathComponent("stamp.txt"), encoding: .utf8))?
    .trimmingCharacters(in: .whitespacesAndNewlines)
}

func state(_ paths: Paths) -> SetupState {
  guard FileManager.default.fileExists(atPath: paths.installMarker.path) else { return .needsInstall }
  let stampFile = paths.module.deletingLastPathComponent().appendingPathComponent("stamp.txt")
  let built = (try? String(contentsOf: stampFile, encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines)
  guard FileManager.default.fileExists(atPath: paths.module.path), let s = built, s == kitStamp(paths) else {
    return .needsBuild
  }
  return .ready
}

// MARK: - Processes

// Apple's tools only: what the kit was tested with (no Homebrew, no user PATH).
let cleanEnvironment = [
  "HOME": FileManager.default.homeDirectoryForCurrentUser.path,
  "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
]

@discardableResult
func run(_ tool: String, _ args: [String]) -> (status: Int32, output: String) {
  let p = Process()
  p.executableURL = URL(fileURLWithPath: tool)
  p.arguments = args
  p.environment = cleanEnvironment
  let pipe = Pipe()
  p.standardOutput = pipe
  p.standardError = pipe
  do { try p.run() } catch { return (-1, "\(error)") }
  let data = pipe.fileHandleForReading.readDataToEndOfFile()
  p.waitUntilExit()
  return (p.terminationStatus, String(decoding: data, as: UTF8.self))
}

// A long step (install or build): its output line by line, cancellable.
final class Step {
  private let process = Process()
  private(set) var cancelled = false
  private var secrets: [String] = []

  init(tool: String, args: [String]) {
    process.executableURL = URL(fileURLWithPath: tool)
    process.arguments = args
    process.environment = cleanEnvironment
  }

  // `input` goes to the process's standard input only. Any secret is removed
  // from its output before anyone sees a line.
  func run(input: String? = nil, secrets: [String] = [], onLine: @escaping (String) -> Void) throws -> Int32 {
    self.secrets = secrets.filter { !$0.isEmpty }
    let out = Pipe()
    process.standardOutput = out
    process.standardError = out
    let stdin = Pipe()
    process.standardInput = stdin
    var pending = Data()
    out.fileHandleForReading.readabilityHandler = { [weak self] h in
      let chunk = h.availableData
      guard let self = self, !chunk.isEmpty else { return }
      pending.append(chunk)
      while let nl = pending.firstIndex(of: 0x0A) {
        let line = String(decoding: pending[pending.startIndex..<nl], as: UTF8.self)
        pending.removeSubrange(pending.startIndex...nl)
        onLine(self.redact(line))
      }
    }
    try process.run()
    if let input = input { stdin.fileHandleForWriting.write(Data(input.utf8)) }
    try? stdin.fileHandleForWriting.close()
    process.waitUntilExit()
    out.fileHandleForReading.readabilityHandler = nil
    if !pending.isEmpty { onLine(redact(String(decoding: pending, as: UTF8.self))) }
    return process.terminationStatus
  }

  func cancel() {
    cancelled = true
    if process.isRunning { process.terminate() }  // SIGTERM: the builder stops its workers and cleans up
  }

  private func redact(_ line: String) -> String {
    secrets.reduce(line) { $0.replacingOccurrences(of: $1, with: "•••") }
  }
}

// MARK: - Install

struct Installation {
  let roc: URL, tft: URL, patch: URL
  let rocKey: String, tftKey: String  // normalised
  let owner: String
}

// Installs and patches into a temporary folder, then renames it to game/: a
// failed or cancelled install leaves no game folder.
func install(_ i: Installation, paths: Paths, step: Step, onLine: @escaping (String) -> Void) throws {
  let fm = FileManager.default
  guard !fm.fileExists(atPath: paths.game.path) else {
    throw SetupError("a game is already installed in \(paths.game.path)")
  }
  try fm.createDirectory(at: paths.data, withIntermediateDirectories: true)
  let tmp = paths.data.appendingPathComponent(".installing-\(ProcessInfo.processInfo.processIdentifier)")
  try? fm.removeItem(at: tmp)
  defer { try? fm.removeItem(at: tmp) }
  let status = try step.run(
    input: "\(i.rocKey)\n\(i.tftKey)\n", secrets: [i.rocKey, i.tftKey],
    onLine: onLine)
  if step.cancelled { throw SetupError("cancelled: nothing was installed") }
  guard status == 0 else { throw SetupError("the installation stopped (exit \(status)): nothing was installed") }
  let marker: [String: Any] = [
    "installed": ISO8601DateFormatter().string(from: Date()),
    "inputs": Input.allCases.map { knownInputs[$0]!.label },
  ]
  try JSONSerialization.data(withJSONObject: marker, options: [.prettyPrinted, .sortedKeys])
    .write(to: tmp.appendingPathComponent("reFrozen-install.json"))
  try fm.moveItem(at: tmp, to: paths.game)
}

func installStep(_ i: Installation, paths: Paths) -> Step {
  let tmp = paths.data.appendingPathComponent(".installing-\(ProcessInfo.processInfo.processIdentifier)")
  return Step(tool: "/usr/bin/python3", args: [
    "-I", paths.kit.appendingPathComponent("scripts/native_install.py").path,
    "--roc", i.roc.path, "--tft", i.tft.path, "--patch", i.patch.path,
    "--out", tmp.path, "--owner", i.owner,
  ])
}

// MARK: - Build

func buildStep(paths: Paths) -> Step {
  Step(tool: "/bin/bash", args: [
    paths.kit.appendingPathComponent("scripts/build_module.sh").path,
    paths.kit.path, paths.game.path, paths.data.path,
  ])
}

// The builder's exit codes (scripts/build_module.sh).
func buildFailure(_ status: Int32) -> String {
  switch status {
  case 10: return "Apple's Command Line Tools are needed"
  case 11: return "the installed game is incomplete"
  case 12: return "not enough free disk space"
  case 13: return "lifting the game stopped"
  case 14: return "a file did not compile"
  case 15: return "linking or signing the game module failed"
  case 130, 143: return "cancelled"
  default: return "the build stopped (exit \(status))"
  }
}

// One overall progress for the whole setup, from the installer's and the
// builder's own lines. It never moves back (a retry starts from where the
// stopped attempt stood) and reaches 100 % only once the built module is
// verified. Install, Compile and Finish follow completed work. The Lift has
// no measure of its own (the lifter is silent), so it shows estimated
// progress instead: from 3 % toward 19 % at a fifth of the speed of the
// measured average Lift (5 x the estimate to reach 19 %), held at 19 % with
// an activity shimmer if it takes longer, and 20 % only when it is done.
struct SetupProgress: Equatable {
  enum Stage: Int, CaseIterable {
    case install, lift, compile, finish, done
  }

  static let spans: [Stage: (from: Double, to: Double)] = [
    .install: (0, 0.03), .lift: (0.03, 0.20), .compile: (0.20, 0.98), .finish: (0.98, 0.995),
  ]
  static let liftCap = 0.19  // the estimate never reaches the end of the Lift
  static let liftSlowdown = 5.0  // the estimate runs at a fifth of the measured speed

  private(set) var stage: Stage
  private(set) var fraction: Double  // completed work (the Lift's estimate aside)
  private(set) var determinate = false
  private(set) var status: String
  let liftEstimate: TimeInterval  // the measured average Lift on this Mac
  private(set) var liftStart: Date?
  private(set) var stoppedAt: Date?
  private let floor: Double  // where a retried attempt's previous one stopped
  private var compileTotal = 0, compileDone = 0, installSteps = 0

  // A first run starts at the install; a build after an install where the install ended.
  init(installing: Bool, liftEstimate: TimeInterval = 60, floor: Double = 0) {
    stage = installing ? .install : .lift
    fraction = installing ? 0 : Self.spans[.install]!.to
    status = installing ? "Installing Warcraft III and patching it to 1.26a" : "Recompiling game code…"
    self.liftEstimate = max(liftEstimate, 1)
    self.floor = floor
  }

  // What the bar shows at `now`: completed work, the Lift's estimate, and
  // never below the floor; frozen once stopped.
  func display(at now: Date) -> Double {
    var shown = max(fraction, floor)
    if stage == .lift { shown = max(shown, liftEstimated(at: now)) }
    return shown
  }

  // The Lift's estimated position alone (no floor).
  private func liftEstimated(at now: Date) -> Double {
    guard let start = liftStart else { return fraction }
    let t = (stoppedAt ?? now).timeIntervalSince(start)
    let lift = Self.spans[.lift]!
    return max(fraction, lift.from + (Self.liftCap - lift.from) * min(max(t, 0) / (Self.liftSlowdown * liftEstimate), 1))
  }

  // The shimmer: work goes on that the bar cannot show (a held Lift, the
  // finishing steps, an install product, or a retry still below its floor).
  func active(at now: Date) -> Bool {
    guard stoppedAt == nil, stage != .done else { return false }
    if stage == .lift {  // held: at the cap, or at a retry's floor above its own estimate
      let shown = display(at: now)
      return shown >= Self.liftCap || shown > liftEstimated(at: now)
    }
    return !determinate || fraction < floor
  }

  func percent(at now: Date) -> Int { Int((display(at: now) * 100).rounded(.down)) }

  mutating func read(_ line: String, at now: Date = Date()) {
    if line.hasPrefix("install RoC:") || line.hasPrefix("install TFT:") || line.hasPrefix("patch 1.26a:") {
      installSteps = min(installSteps + 1, 3)
      enter(.install, determinate: false, ["Installed Reign of Chaos", "Installed The Frozen Throne", "Patched to 1.26a"][installSteps - 1])
      advance(within: .install, Double(installSteps) / 3)
    } else if line.hasPrefix("reFrozen game module ") || line.hasPrefix("prepared ") || line == "lifting the game code" {
      if liftStart == nil { liftStart = now }
      advance(within: .install, 1)
      enter(.lift, determinate: false, "Recompiling game code…")
    } else if line.hasPrefix("compiling "), let n = Int(line.split(separator: " ")[1]) {
      compileTotal = n
      compileDone = 0
      enter(.compile, determinate: true, "Compiling the game: 0 of \(n) files")
      advance(within: .compile, 0)
    } else if line.hasPrefix("compiled "), compileTotal > 0 {
      compileDone = min(compileDone + 1, compileTotal)
      enter(.compile, determinate: true, "Compiling the game: \(compileDone) of \(compileTotal) files")
      advance(within: .compile, Double(compileDone) / Double(compileTotal))
    } else if line == "linking" {
      enter(.finish, determinate: false, "Linking the game module")
      advance(within: .finish, 0)
    } else if line == "signing" {
      enter(.finish, determinate: false, "Signing the game module")
      advance(within: .finish, 0.4)
    } else if line == "installing the module" {
      enter(.finish, determinate: false, "Installing the game module")
      advance(within: .finish, 0.7)
    } else if line.hasPrefix("built: ") {
      enter(.finish, determinate: false, "Verifying the game module")
      advance(within: .finish, 1)
    }
  }

  // Cancelled or failed: the bar stays where it stood.
  mutating func stop(at now: Date = Date()) {
    if stoppedAt == nil { stoppedAt = now }
  }

  // Only once the installed module is checked (its stamp matches this app).
  mutating func verified() {
    stage = .done
    determinate = true
    fraction = 1
    status = "Ready"
  }

  private mutating func enter(_ s: Stage, determinate d: Bool, _ text: String) {
    if s.rawValue >= stage.rawValue { stage = s }
    determinate = d
    status = text
  }

  private mutating func advance(within s: Stage, _ part: Double) {
    let span = Self.spans[s]!
    fraction = max(fraction, span.from + (span.to - span.from) * min(max(part, 0), 1))
  }
}

// The measured average Lift on this Mac (the builder logs "lift <n>s"), or 60 s.
func measuredLiftEstimate(_ paths: Paths) -> TimeInterval {
  let logs = (try? FileManager.default.contentsOfDirectory(at: paths.logs, includingPropertiesForKeys: nil)) ?? []
  let times = logs.filter { $0.lastPathComponent.hasPrefix("build-") }.compactMap { url -> Double? in
    guard let text = try? String(contentsOf: url, encoding: .utf8),
          let r = text.range(of: #"; lift (\d+)s,"#, options: .regularExpression) else { return nil }
    return Double(text[r].filter(\.isNumber))
  }
  return times.isEmpty ? 60 : times.reduce(0, +) / Double(times.count)
}

// MARK: - Maps

enum MapImport: Equatable {
  case added(URL), alreadyInstalled(URL), renamed(URL)
  var url: URL {
    switch self { case .added(let u), .alreadyInstalled(let u), .renamed(let u): return u }
  }
}

// Imports a player-supplied map into the game's Maps/Download folder (the
// game lists it in Custom Game; nothing is reinstalled or rebuilt). A
// Warcraft III map starts with "HM3W" and 1.26a loads maps up to 8 MB.
// Existing maps are never overwritten: the same file again is reported as
// installed, a different map with the same name is added as "<name> (2)".
// The file appears under its final name only once complete.
func importMap(_ url: URL, paths: Paths) throws -> MapImport {
  let ext = url.pathExtension.lowercased()
  guard ext == "w3x" || ext == "w3m" else { throw SetupError("not a Warcraft III map (.w3x or .w3m)") }
  let data = try Data(contentsOf: url)
  guard data.count <= 8 << 20 else { throw SetupError("over 8 MB: Warcraft III 1.26a cannot load it") }
  guard data.starts(with: Array("HM3W".utf8)) else { throw SetupError("not a Warcraft III map (no map header)") }
  let fm = FileManager.default
  let dir = paths.game.appendingPathComponent("Maps/Download")
  try fm.createDirectory(at: dir, withIntermediateDirectories: true)
  let stem = url.deletingPathExtension().lastPathComponent, suffix = url.pathExtension
  for n in 1... {
    let dest = dir.appendingPathComponent(n == 1 ? url.lastPathComponent : "\(stem) (\(n)).\(suffix)")
    if fm.fileExists(atPath: dest.path) {
      if (try? Data(contentsOf: dest)) == data { return .alreadyInstalled(dest) }
      continue
    }
    let tmp = dir.appendingPathComponent(".importing-\(UUID().uuidString)")
    try data.write(to: tmp)
    do { try fm.moveItem(at: tmp, to: dest) } catch { try? fm.removeItem(at: tmp); throw error }
    return n == 1 ? .added(dest) : .renamed(dest)
  }
  fatalError("unreachable")
}

// The maps in Maps/Download, by name.
func installedMaps(_ paths: Paths) -> [String] {
  let dir = paths.game.appendingPathComponent("Maps/Download")
  let names = (try? FileManager.default.contentsOfDirectory(atPath: dir.path)) ?? []
  return names.filter { ["w3x", "w3m"].contains(($0 as NSString).pathExtension.lowercased()) }
    .sorted { $0.localizedStandardCompare($1) == .orderedAscending }
}

// MARK: - Play

// Replaces this process with the game (one app in the Dock).
func launchGame(_ paths: Paths) -> Never {
  let launcher = paths.kit.appendingPathComponent("bin/refrozen").path
  let args = [launcher, "--game", paths.game.path, "--module", paths.module.path]
  var cargs = args.map { strdup($0) } + [nil]
  execv(launcher, &cargs)
  fatalError("cannot start \(launcher): \(String(cString: strerror(errno)))")
}

// MARK: - Log

// logs/setup-<time>.log; lines are already free of secrets (Step.redact).
final class SetupLog {
  private let handle: FileHandle?

  init(paths: Paths) {
    try? FileManager.default.createDirectory(at: paths.logs, withIntermediateDirectories: true)
    let f = DateFormatter()
    f.dateFormat = "yyyyMMdd-HHmmss"
    let url = paths.logs.appendingPathComponent("setup-\(f.string(from: Date())).log")
    FileManager.default.createFile(atPath: url.path, contents: nil)
    handle = try? FileHandle(forWritingTo: url)
  }

  func write(_ line: String) {
    handle?.write(Data((line + "\n").utf8))
  }
}
