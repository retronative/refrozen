// Prints the text macOS's Vision framework recognizes in an image, one line
// per recognized line, for acceptance scripts that check what the game shows
// (M6: the victory announcement and the score screen in a long AI match).
//
//   build/oracle_keys/ocr_text <image>...    (compiled by the script using it)
//
// With several images, each line is prefixed by "<image>: ". Exit 1 if an
// image cannot be read.
import Foundation
import Vision

let paths = Array(CommandLine.arguments.dropFirst())
var failed = false
for path in paths {
  guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
        let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
    FileHandle.standardError.write("ocr_text: cannot read \(path)\n".data(using: .utf8)!)
    failed = true
    continue
  }
  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.usesLanguageCorrection = false
  try? VNImageRequestHandler(cgImage: image).perform([request])
  for obs in request.results ?? [] {
    guard let text = obs.topCandidates(1).first?.string else { continue }
    print(paths.count > 1 ? "\(path): \(text)" : text)
  }
}
exit(failed ? 1 : 0)
