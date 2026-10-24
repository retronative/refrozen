// Print the window ID of the largest on-screen window whose owner name
// contains a given string, for `screencapture -l <id>` (captures only that
// window, never the whole screen). Dev evidence for launches.
//   swift scripts/capture_window.swift <owner substring>
import CoreGraphics
import Foundation

let args = CommandLine.arguments
guard args.count == 2 else {
    FileHandle.standardError.write("usage: capture_window <owner substring>\n".data(using: .utf8)!)
    exit(2)
}
let needle = args[1].lowercased()
let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as? [[String: Any]] ?? []
let candidates = info.filter { ($0[kCGWindowOwnerName as String] as? String ?? "").lowercased().contains(needle) }
func area(_ w: [String: Any]) -> Double {
    let b = w[kCGWindowBounds as String] as? [String: Double] ?? [:]
    return (b["Width"] ?? 0) * (b["Height"] ?? 0)
}
guard let win = candidates.max(by: { area($0) < area($1) }),
      let id = win[kCGWindowNumber as String] as? CGWindowID else {
    FileHandle.standardError.write("no window owned by '\(args[1])'\n".data(using: .utf8)!)
    exit(1)
}
print(id)
