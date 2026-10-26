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

// The website's loading bar: icy fill in a bronze-tinted iron frame. nil: working, no measure yet.
struct FrostBar: View {
  let value: Double?
  var body: some View {
    GeometryReader { g in
      ZStack(alignment: .leading) {
        Rectangle().fill(Theme.abyss)
        Rectangle()
          .fill(LinearGradient(colors: [Theme.frostDeep, Theme.frost, Theme.iceCore], startPoint: .leading, endPoint: .trailing))
          .frame(width: g.size.width * min(max(value ?? 0.08, 0), 1))
          .shadow(color: Theme.glow, radius: 6)
      }
      .overlay(Rectangle().stroke(Theme.goldShadow.opacity(0.9), lineWidth: 1))
    }
    .frame(height: 8)
    .accessibilityElement()
    .accessibilityValue(value.map { "\(Int($0 * 100)) percent" } ?? "working")
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
