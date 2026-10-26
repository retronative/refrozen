// The first-run setup window: prerequisites, the player's installers, CD keys
// and name, install and build with progress, then play.

import AppKit
import SwiftUI
import UniformTypeIdentifiers

enum Page: Int, CaseIterable {
  case welcome, files, keys, work, done
}

enum InputCheck: Equatable {
  case none, checking(Double), ok(String), bad(String)
}

@MainActor
final class SetupModel: ObservableObject {
  let paths: Paths
  @Published var page: Page = .welcome
  @Published var prereqs: [Prerequisite] = []
  @Published var urls: [Input: URL] = [:]
  @Published var checks: [Input: InputCheck] = [:]
  @Published var rocKey = ""
  @Published var tftKey = ""
  @Published var owner = NSFullUserName()
  @Published var phase = ""
  @Published var progress: Double?
  @Published var lines: [String] = []
  @Published var failure: String?
  @Published var working = false
  @Published var mapNote: String?
  @Published var picking: Input?  // the file dialog open for this input
  @Published var pickingMap = false
  private var current: Step?
  private var log: SetupLog?

  init(paths: Paths) {
    self.paths = paths
    switch state(paths) {
    case .needsInstall: page = .welcome
    case .needsBuild: page = .work  // installed earlier: only the game module is (re)built
    case .ready: page = .done
    }
  }

  var prereqsOK: Bool { !prereqs.isEmpty && prereqs.allSatisfy(\.ok) }
  var filesOK: Bool { Input.allCases.allSatisfy { if case .ok = checks[$0] { return true } else { return false } } }
  var rocKeyOK: Bool { normaliseKey(rocKey) != nil }
  var tftKeyOK: Bool { normaliseKey(tftKey) != nil }
  var keysOK: Bool { rocKeyOK && tftKeyOK && normaliseKey(rocKey) != normaliseKey(tftKey) && ownerProblem(owner) == nil }

  func checkPrerequisites() {
    let paths = self.paths
    Task.detached { let p = prerequisites(paths); await MainActor.run { self.prereqs = p } }
  }

  func installCommandLineTools() {
    run("/usr/bin/xcode-select", ["--install"])  // Apple's own installer dialog
  }

  func choose(_ input: Input, _ url: URL) {
    urls[input] = url
    checks[input] = .checking(0)
    Task.detached {
      let r = verifyInput(input, at: url) { f in Task { @MainActor in
        if case .checking = self.checks[input] { self.checks[input] = .checking(f) } } }
      await MainActor.run {
        switch r {
        case .success(let label): self.checks[input] = .ok(label)
        case .failure(let e): self.checks[input] = .bad(e.description)
        }
      }
    }
  }

  // Install (first run only) then build; ends on .done or with `failure`.
  func start() {
    page = .work
    working = true
    failure = nil
    lines = []
    log = SetupLog(paths: paths)
    let paths = self.paths
    let needsInstall = state(paths) == .needsInstall
    let installation = needsInstall ? Installation(
      roc: urls[.roc]!, tft: urls[.tft]!, patch: urls[.patch]!,
      rocKey: normaliseKey(rocKey)!, tftKey: normaliseKey(tftKey)!, owner: owner) : nil
    rocKey = ""
    tftKey = ""  // the keys are only needed by the installer
    Task.detached {
      do {
        if let i = installation {
          let step = installStep(i, paths: paths)
          await self.begin(step, "Installing Warcraft III and patching it to 1.26a", nil)
          try install(i, paths: paths, step: step) { l in Task { @MainActor in self.add(l) } }
        }
        let step = buildStep(paths: paths)
        await self.begin(step, "Building the game for this Mac", 0)
        var progress = BuildProgress()
        let status = try step.run { l in
          progress.read(l)
          let f = progress.fraction
          Task { @MainActor in self.add(l); if let f = f { self.progress = f } }
        }
        guard status == 0 else { throw SetupError(buildFailure(status)) }
        await MainActor.run { self.working = false; self.page = .done }
      } catch {
        await MainActor.run { self.working = false; self.failure = "\(error)" }
      }
    }
  }

  func cancel() { current?.cancel() }

  func addMap(_ url: URL) {
    do { mapNote = "Added \(try copyMap(url, paths: paths).lastPathComponent) to Maps/Download" }
    catch { mapNote = "\(error)" }
  }

  private func begin(_ step: Step, _ phase: String, _ progress: Double?) {
    current = step
    self.phase = phase
    self.progress = progress
    add("— " + phase)
  }

  private func add(_ line: String) {
    log?.write(line)
    lines.append(line)
    if lines.count > 400 { lines.removeFirst(lines.count - 400) }
  }
}

// MARK: - Views

struct SetupView: View {
  @ObservedObject var model: SetupModel

  var body: some View {
    VStack(spacing: 0) {
      header
      Rectangle().fill(Theme.goldMetal).frame(height: 1).opacity(0.8)
      Group {
        switch model.page {
        case .welcome: WelcomePage(model: model)
        case .files: FilesPage(model: model)
        case .keys: KeysPage(model: model)
        case .work: WorkPage(model: model)
        case .done: DonePage(model: model)
        }
      }
      .padding(28)
      .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
    .frame(width: 760, height: 560)
    .background(
      LinearGradient(colors: [Theme.slab2, Theme.abyss], startPoint: .top, endPoint: .bottom)
    )
    .foregroundStyle(Theme.bone)
    .tint(Theme.frost)
  }

  private var header: some View {
    HStack(spacing: 14) {
      if let image = NSImage(contentsOf: model.paths.kit.appendingPathComponent("resources/icon.png")) {
        Image(nsImage: image).resizable().frame(width: 52, height: 52)
      }
      VStack(alignment: .leading, spacing: 2) {
        (Text("re").font(Theme.serifItalic(30)).foregroundStyle(Theme.frost)
          + Text("FROZEN").font(Theme.display(28)).foregroundStyle(Theme.goldBright))
        Text("NATIVE ON APPLE SILICON").font(Theme.display(10)).tracking(3).foregroundStyle(Theme.gold)
      }
      Spacer()
      StepTrail(page: model.page)
    }
    .padding(.horizontal, 28).padding(.vertical, 16)
    .background(Theme.abyss)
  }
}

struct StepTrail: View {
  let page: Page
  private let names = ["Mac", "Game files", "CD keys", "Build", "Play"]
  var body: some View {
    HStack(spacing: 8) {
      ForEach(Page.allCases, id: \.self) { p in
        VStack(spacing: 4) {
          Image(systemName: p.rawValue < page.rawValue ? "checkmark.diamond.fill" : p == page ? "diamond.fill" : "diamond")
            .font(.system(size: 11)).foregroundStyle(p.rawValue <= page.rawValue ? Theme.frost : Theme.seam)
          Text(names[p.rawValue]).font(Theme.body(9)).foregroundStyle(p == page ? Theme.bone : Theme.ash)
        }
      }
    }
  }
}

struct PageTitle: View {
  let title: String, subtitle: String
  var body: some View {
    VStack(alignment: .leading, spacing: 6) {
      HStack(spacing: 8) { Stud(); Text(title).font(Theme.display(20)).foregroundStyle(Theme.goldBright) }
      Text(subtitle).font(Theme.serif(17)).foregroundStyle(Theme.ash)
    }
    .padding(.bottom, 16)
  }
}

struct StatusMark: View {
  let ok: Bool?
  var body: some View {
    Image(systemName: ok == nil ? "circle.dotted" : ok! ? "checkmark.seal.fill" : "exclamationmark.triangle.fill")
      .foregroundStyle(ok == nil ? Theme.ash : ok! ? Theme.verdant : Theme.ember)
      .frame(width: 18)
  }
}

struct WelcomePage: View {
  @ObservedObject var model: SetupModel
  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      PageTitle(title: "Welcome",
                subtitle: "reFrozen builds Warcraft III: The Frozen Throne 1.26a for this Mac from your own game files. "
                  + "Nothing of the game is downloaded or sent anywhere.")
      Panel {
        VStack(alignment: .leading, spacing: 10) {
          if model.prereqs.isEmpty { Text("Checking this Mac…").font(Theme.body()).foregroundStyle(Theme.ash) }
          ForEach(model.prereqs, id: \.name) { p in
            HStack(spacing: 10) {
              StatusMark(ok: p.ok)
              Text(p.name).font(Theme.bodyMedium(13))
              Spacer()
              Text(p.detail).font(Theme.body(12)).foregroundStyle(p.ok ? Theme.ash : Theme.ember)
              if !p.ok && p.name.hasPrefix("Apple's Command") {
                Button("Install") { model.installCommandLineTools() }.buttonStyle(FrostButtonStyle(prominent: false))
              }
            }
          }
        }
      }
      Spacer()
      HStack {
        Button("Check again") { model.checkPrerequisites() }.buttonStyle(FrostButtonStyle(prominent: false))
        Spacer()
        Button("Continue") { model.page = .files }.buttonStyle(FrostButtonStyle()).disabled(!model.prereqsOK)
      }
    }
    .onAppear { model.checkPrerequisites() }
  }
}

struct FilesPage: View {
  @ObservedObject var model: SetupModel

  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      PageTitle(title: "Your game files",
                subtitle: "Choose your Warcraft III installers and the official 1.26a patch. They are read, never changed.")
      Panel {
        VStack(alignment: .leading, spacing: 14) {
          ForEach(Input.allCases, id: \.self) { input in row(input) }
        }
      }
      Spacer()
      HStack {
        Button("Back") { model.page = .welcome }.buttonStyle(FrostButtonStyle(prominent: false))
        Spacer()
        Button("Continue") { model.page = .keys }.buttonStyle(FrostButtonStyle()).disabled(!model.filesOK)
      }
    }
    .fileImporter(isPresented: Binding(get: { model.picking != nil }, set: { if !$0 { model.picking = nil } }),
                  allowedContentTypes: model.picking == .patch ? [.item] : [.folder]) { result in
      if let input = model.picking, case .success(let url) = result { model.choose(input, url) }
      model.picking = nil
    }
  }

  private func row(_ input: Input) -> some View {
    let check = model.checks[input] ?? InputCheck.none
    let ok: Bool? = { if case .ok = check { return true }; if case .bad = check { return false }; return nil }()
    return HStack(alignment: .top, spacing: 10) {
      StatusMark(ok: ok)
      VStack(alignment: .leading, spacing: 3) {
        Text(input == .roc ? "Reign of Chaos installer" : input == .tft ? "The Frozen Throne installer" : "Patch 1.26a")
          .font(Theme.bodyMedium(13))
        Group {
          switch check {
          case .none: Text(model.urls[input]?.path ?? "not chosen").foregroundStyle(Theme.ash)
          case .checking(let f): FrostBar(value: f).frame(width: 220)
          case .ok(let label): Text(label).foregroundStyle(Theme.verdant)
          case .bad(let reason): Text(reason).foregroundStyle(Theme.ember)
          }
        }
        .font(Theme.body(12))
      }
      Spacer()
      Button("Choose…") { model.picking = input }.buttonStyle(FrostButtonStyle(prominent: false))
    }
  }
}

struct KeysPage: View {
  @ObservedObject var model: SetupModel
  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      PageTitle(title: "CD keys and name",
                subtitle: "As the official installer asks for them. They are stored only inside your game's files, "
                  + "never sent anywhere or written to a log.")
      Panel {
        VStack(alignment: .leading, spacing: 14) {
          field("Reign of Chaos CD key", ok: model.rocKey.isEmpty ? nil : model.rocKeyOK) {
            SecureField("26 characters", text: $model.rocKey)
          }
          field("The Frozen Throne CD key", ok: model.tftKey.isEmpty ? nil : model.tftKeyOK) {
            SecureField("26 characters", text: $model.tftKey)
          }
          field("Your name", ok: ownerProblem(model.owner) == nil) { TextField("", text: $model.owner) }
          if model.rocKeyOK && model.tftKeyOK && normaliseKey(model.rocKey) == normaliseKey(model.tftKey) {
            Text("The two keys are the same: each game has its own key.").font(Theme.body(12)).foregroundStyle(Theme.ember)
          } else if let p = ownerProblem(model.owner) {
            Text("Name: \(p).").font(Theme.body(12)).foregroundStyle(Theme.ember)
          }
        }
      }
      Spacer()
      HStack {
        Button("Back") { model.page = .files }.buttonStyle(FrostButtonStyle(prominent: false))
        Spacer()
        Button("Install and build") { model.start() }.buttonStyle(FrostButtonStyle()).disabled(!model.keysOK)
      }
    }
  }

  private func field<F: View>(_ label: String, ok: Bool?, @ViewBuilder _ input: () -> F) -> some View {
    HStack(spacing: 10) {
      StatusMark(ok: ok)
      Text(label).font(Theme.bodyMedium(13)).frame(width: 190, alignment: .leading)
      input().textFieldStyle(.plain).font(Theme.body(13)).padding(7)
        .background(Theme.abyss).overlay(Rectangle().stroke(Theme.seam))
    }
  }
}

struct WorkPage: View {
  @ObservedObject var model: SetupModel
  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      PageTitle(title: model.failure == nil ? "Installing and building" : "Setup stopped",
                subtitle: model.failure ?? (model.phase.isEmpty
                  ? "The game is installed; the game module needs to be built for this version of reFrozen."
                  : model.phase + ". This takes a few minutes; you can cancel at any time."))
      Panel {
        VStack(alignment: .leading, spacing: 10) {
          if model.working || model.progress != nil { FrostBar(value: model.progress) }
          ScrollViewReader { proxy in
            ScrollView {
              VStack(alignment: .leading, spacing: 1) {
                ForEach(Array(model.lines.suffix(200).enumerated()), id: \.offset) { i, l in
                  Text(l).font(.system(size: 10, design: .monospaced)).foregroundStyle(Theme.ash).id(i)
                }
              }
              .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(height: 220)
            .onChange(of: model.lines.count) { _, _ in proxy.scrollTo(min(model.lines.count, 200) - 1) }
          }
        }
      }
      Spacer()
      HStack {
        if model.failure != nil {
          Button("Back") { model.page = state(model.paths) == .needsInstall ? .keys : .welcome }
            .buttonStyle(FrostButtonStyle(prominent: false))
          Text("Details are in logs/ in the data folder.").font(Theme.body(11)).foregroundStyle(Theme.ash)
        }
        Spacer()
        if model.working {
          Button("Cancel") { model.cancel() }.buttonStyle(FrostButtonStyle(prominent: false))
        } else if model.failure != nil || model.phase.isEmpty {
          Button(model.failure == nil ? "Build" : "Try again") { model.start() }.buttonStyle(FrostButtonStyle())
        }
      }
    }
  }
}

struct DonePage: View {
  @ObservedObject var model: SetupModel
  var body: some View {
    VStack(alignment: .leading, spacing: 0) {
      PageTitle(title: "Ready", subtitle: "reFrozen is installed and built for this Mac.")
      Panel {
        VStack(alignment: .leading, spacing: 10) {
          Text("Maps").font(Theme.bodyMedium(13))
          Text("Add a map you have (for example a DotA AI map) to Single Player → Custom Game.")
            .font(Theme.body(12)).foregroundStyle(Theme.ash)
          HStack {
            Button("Add a map…") { model.pickingMap = true }.buttonStyle(FrostButtonStyle(prominent: false))
            if let note = model.mapNote { Text(note).font(Theme.body(12)).foregroundStyle(Theme.ash) }
          }
        }
      }
      Spacer()
      HStack {
        Text("Fullscreen by default; Ctrl+Cmd+F switches to a window.").font(Theme.body(11)).foregroundStyle(Theme.ash)
        Spacer()
        Button("Play") { launchGame(model.paths) }.buttonStyle(FrostButtonStyle())
      }
    }
    .fileImporter(isPresented: $model.pickingMap, allowedContentTypes: [.item]) { result in
      if case .success(let url) = result { model.addMap(url) }
    }
  }
}
