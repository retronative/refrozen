// The approved reFrozen design tokens (assets/design-tokens.md; values from
// .website/src/styles/main.css) and the site's typefaces, from the kit.

import CoreText
import SwiftUI

extension Color {
  init(hex: UInt32, opacity: Double = 1) {
    self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
              blue: Double(hex & 0xFF) / 255, opacity: opacity)
  }
}

enum Theme {
  static let abyss = Color(hex: 0x05080E)
  static let slab = Color(hex: 0x0B121B)
  static let slab2 = Color(hex: 0x111A26)
  static let seam = Color(hex: 0x233044)
  static let bone = Color(hex: 0xECE6D8)
  static let ash = Color(hex: 0xA7AFBC)
  static let frost = Color(hex: 0x88D3F9)
  static let frostDeep = Color(hex: 0x156EC5)
  static let iceCore = Color(hex: 0xDFEDFA)
  static let gold = Color(hex: 0xD4AE7A)
  static let goldBright = Color(hex: 0xEED2A7)
  static let goldDeep = Color(hex: 0xAB7F52)
  static let goldShadow = Color(hex: 0x47301C)
  static let verdant = Color(hex: 0xA3D58C)
  static let ember = Color(hex: 0xE59A5B)
  static let glow = Color(.sRGB, red: 79 / 255, green: 178 / 255, blue: 235 / 255, opacity: 0.55)
  static let goldMetal = LinearGradient(colors: [goldBright, goldDeep, goldShadow],
                                        startPoint: .topLeading, endPoint: .bottomTrailing)

  static func display(_ size: CGFloat) -> Font { .custom("Cinzel", size: size).weight(.semibold) }
  // Named instances of the variable fonts (a weight modifier does not reach them).
  static func serif(_ size: CGFloat) -> Font { .custom("CormorantGaramond-Medium", size: size) }
  static func serifItalic(_ size: CGFloat) -> Font { .custom("CormorantGaramond-MediumItalic", size: size) }
  static func body(_ size: CGFloat = 13) -> Font { .custom("Inter-Regular", size: size) }
  static func bodyMedium(_ size: CGFloat = 13) -> Font { .custom("Inter-Regular_Medium", size: size) }

  // Registers the kit's fonts for this process (CoreText reads the site's WOFF2 files).
  static func registerFonts(kit: URL) {
    let dir = kit.appendingPathComponent("resources")
    let files = (try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)) ?? []
    for f in files where f.pathExtension == "woff2" {
      CTFontManagerRegisterFontsForURL(f as CFURL, .process, nil)
    }
  }
}

// A stone panel with a weathered-gold rim and a cold top edge.
struct Panel<Content: View>: View {
  @ViewBuilder var content: Content
  var body: some View {
    content
      .padding(18)
      .frame(maxWidth: .infinity, alignment: .leading)
      .background(Theme.slab.opacity(0.92))
      .overlay(Rectangle().stroke(Theme.goldDeep.opacity(0.7), lineWidth: 1))
      .overlay(alignment: .top) { Rectangle().fill(Theme.iceCore.opacity(0.12)).frame(height: 1) }
  }
}

// The website's loading bar: a navy-to-ice fill in a bronze-tinted iron frame, ending in a soft
// glowing edge (FrostFill, FrostEdge). `sweeping`: setup is working, shown by a light crossing the
// whole track, dim over the unfilled part (FrostSweep), and the edge's rays turning. `active`: work
// is going on that has no measure yet, the light brighter. One timeline drives it, at most 30 frames
// a second, paused when nothing moves or the window is not active. Under reduced motion: no sweep and
// still rays. `frozenAt` draws one moment, `stillPreview` as under reduced motion (previews).
struct FrostBar: View {
  let value: Double?
  var active = false
  var sweeping = false
  var frozenAt: Double? = nil
  var stillPreview = false
  @Environment(\.accessibilityReduceMotion) private var reduceMotion
  @Environment(\.controlActiveState) private var windowState
  private static let height = 8.0

  var body: some View {
    GeometryReader { g in
      let track = g.size.width, fill = track * min(max(value ?? 0, 0), 1)
      let moving = (sweeping || active) && !reduceMotion && !stillPreview
      let o = FrostEdge.overflow
      // Drawn once: the track, the fill with its softened end, the frame and the edge glow.
      ZStack(alignment: .leading) {
        Rectangle().fill(Theme.abyss)
        Rectangle()
          .fill(LinearGradient(colors: FrostFill.colors.map { Color(hex: $0) }, startPoint: .leading, endPoint: .trailing))
          .frame(width: fill)
          .mask(LinearGradient(stops: [.init(color: .black, location: 0),
                                       .init(color: .black, location: max(0, 1 - 6 / max(fill, 1))),
                                       .init(color: .black.opacity(0.55), location: 1)],
                               startPoint: .leading, endPoint: .trailing))
      }
      .clipped()
      .overlay(Rectangle().stroke(Theme.goldShadow.opacity(0.9), lineWidth: 1))
      .overlay(alignment: .leading) { glow(fill: fill).frame(width: track + 2 * o, height: Self.height + 2 * o).offset(x: -o) }
      // Redrawn on the timeline: only the light and the edge's rays.
      .overlay(alignment: .leading) {
        Group {
          if let t = frozenAt {
            moment(track: track, fill: fill, t: t, moving: moving)
          } else if moving {
            TimelineView(.animation(minimumInterval: 1.0 / 30, paused: windowState == .inactive)) { context in
              moment(track: track, fill: fill, t: context.date.timeIntervalSinceReferenceDate, moving: true)
            }
          } else {
            moment(track: track, fill: fill, t: 0, moving: false)
          }
        }
        .frame(width: track + 2 * o, height: Self.height + 2 * o)
        .offset(x: -o)
        .allowsHitTesting(false)
      }
    }
    .frame(height: Self.height)
    .accessibilityElement()
    .accessibilityValue(active ? "working" : value.map { "\(Int($0 * 100)) percent" } ?? "working")
  }

  // The moving parts at time t, in a frame `overflow` points wider than the track on each side.
  // Each frame changes only transforms: the light's position (one pre-drawn band, dimmed beyond
  // the fill by a still mask) and the rays' turn and length (drawn once).
  private func moment(track: Double, fill: Double, t: Double, moving: Bool) -> some View {
    let o = FrostEdge.overflow, h = Self.height
    let r = FrostEdge.rays(at: t, reduceMotion: !moving)
    let lit = FrostSweep.opacity(at: 0, fill: 1, active: active)
    return ZStack(alignment: .leading) {
      if moving {
        Rectangle()
          .fill(LinearGradient(colors: [.clear, Theme.frost, .clear], startPoint: .leading, endPoint: .trailing))
          .frame(width: FrostSweep.band, height: h)
          .offset(x: FrostSweep.lead(track: track, at: t))
          .frame(width: track, height: h, alignment: .leading)
          .clipped()
          .mask(alignment: .leading) {
            HStack(spacing: 0) {
              Rectangle().frame(width: fill)
              Rectangle().opacity(FrostSweep.trackOpacity / lit)
            }
          }
          .opacity(lit)
          .offset(x: o)
      }
      if fill > 0 {
        FrostRays()
          .rotationEffect(.radians(r.angle))
          .scaleEffect(r.length / FrostRays.length)
          .frame(width: 2 * FrostRays.length, height: 2 * FrostRays.length)
          .offset(x: o + FrostEdge.center(fill: fill) - FrostRays.length)
          .frame(width: track + 2 * o, height: h + 2 * o, alignment: .leading)
          .clipped()
      }
    }
  }

  // The soft glow on the fill's end (still).
  private func glow(fill: Double) -> some View {
    let x = FrostEdge.center(fill: fill), r = FrostEdge.glowRadius, o = FrostEdge.overflow
    return Canvas { ctx, size in
      let c = CGPoint(x: x + o, y: size.height / 2)
      ctx.fill(Path(ellipseIn: CGRect(x: c.x - r, y: c.y - (Self.height / 2 + o), width: 2 * r, height: Self.height + 2 * o)),
               with: .radialGradient(Gradient(colors: [Theme.frost.opacity(0.6), Theme.frost.opacity(0)]),
                                     center: c, startRadius: 0, endRadius: r))
    }
    .clipped()
    .opacity(fill > 0 ? 1 : 0)
    .allowsHitTesting(false)
  }

}

// The edge's faint rays, drawn once around the centre of a square `2 * length` points wide.
struct FrostRays: View {
  static let length = 7.0
  var body: some View {
    Canvas { ctx, size in
      let c = CGPoint(x: size.width / 2, y: size.height / 2)
      for i in 0..<FrostEdge.rays {
        let a = Double(i) * 2 * .pi / Double(FrostEdge.rays)
        var ray = Path()
        ray.move(to: c)
        ray.addLine(to: CGPoint(x: c.x + cos(a) * Self.length, y: c.y + sin(a) * Self.length))
        ctx.stroke(ray, with: .color(Theme.iceCore.opacity(0.22)), lineWidth: 0.8)
      }
    }
    .drawingGroup()
  }
}

// "Show Details" / "Hide Details" with its arrow: one control, clicked anywhere on
// the words or the arrow, or focused with Tab and toggled with Space or Return.
struct DetailsToggle: View {
  @Binding var expanded: Bool
  @FocusState private var focused: Bool
  @Environment(\.accessibilityReduceMotion) private var reduceMotion
  var body: some View {
    HStack(spacing: 6) {
      Image(systemName: "chevron.right").font(.system(size: 10, weight: .semibold))
        .rotationEffect(.degrees(expanded ? 90 : 0))
      Text(DetailsControl.title(expanded: expanded)).font(Theme.body(12))
    }
    .foregroundStyle(Theme.frost)
    .contentShape(Rectangle())
    .overlay(RoundedRectangle(cornerRadius: 3).stroke(Theme.frost.opacity(focused ? 0.9 : 0), lineWidth: 1).padding(-3))
    .onTapGesture { toggle() }
    .focusable()
    .focused($focused)
    .focusEffectDisabled()
    .onKeyPress(.space) { toggle(); return .handled }
    .onKeyPress(.return) { toggle(); return .handled }
    .accessibilityElement(children: .ignore)
    .accessibilityLabel(DetailsControl.accessibilityLabel)
    .accessibilityValue(DetailsControl.accessibilityValue(expanded: expanded))
    .accessibilityAddTraits(.isButton)
    .accessibilityAction { toggle() }
  }

  private func toggle() {
    withAnimation(reduceMotion ? nil : .easeOut(duration: 0.15)) { expanded.toggle() }
  }
}

// The four-point stud from the icon's frame.
struct Stud: View {
  var color = Theme.gold
  var body: some View {
    Image(systemName: "sparkle").font(.system(size: 9, weight: .bold)).foregroundStyle(color)
  }
}

struct FrostButtonStyle: ButtonStyle {
  var prominent = true
  @Environment(\.isEnabled) private var enabled
  func makeBody(configuration: Configuration) -> some View {
    configuration.label
      .font(Theme.display(13))
      .tracking(1.5)
      .foregroundStyle(prominent ? Theme.iceCore : Theme.gold)
      .padding(.horizontal, 22).padding(.vertical, 9)
      .background(prominent ? Theme.frostDeep.opacity(configuration.isPressed ? 0.55 : 0.4) : Theme.slab2)
      .overlay(Rectangle().stroke(prominent ? Theme.frost.opacity(0.8) : Theme.goldDeep, lineWidth: 1))
      .overlay(alignment: .top) { Rectangle().fill(Theme.iceCore.opacity(0.18)).frame(height: 1) }
      .shadow(color: prominent && enabled ? Theme.glow : .clear, radius: 8)
      .opacity(enabled ? 1 : 0.45)
  }
}
