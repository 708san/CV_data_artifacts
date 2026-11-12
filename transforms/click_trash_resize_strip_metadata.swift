import Foundation
import ImageIO
import CoreGraphics

let args = CommandLine.arguments
if args.count != 3 { fatalError("usage: click_trash_resize_strip_metadata.swift SOURCE_IMAGES DEST_IMAGES") }
let sourceRoot = URL(fileURLWithPath: args[1], isDirectory: true)
let outputRoot = URL(fileURLWithPath: args[2], isDirectory: true)
let fileManager = FileManager.default
try fileManager.createDirectory(at: outputRoot, withIntermediateDirectories: true)

var images: [URL] = []
for split in ["train", "val", "test"] {
    let directory = sourceRoot.appendingPathComponent(split)
    images += try fileManager.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
        .filter { $0.pathExtension.lowercased() == "jpg" }
}
images.sort { $0.path < $1.path }
var failures: [String] = []
for (index, source) in images.enumerated() {
    autoreleasepool {
        let relative = source.deletingLastPathComponent().lastPathComponent + "/" + source.lastPathComponent
        let destination = outputRoot.appendingPathComponent(relative)
        do {
            try fileManager.createDirectory(at: destination.deletingLastPathComponent(), withIntermediateDirectories: true)
            guard let sourceImage = CGImageSourceCreateWithURL(source as CFURL, nil) else {
                throw NSError(domain: "click_trash", code: 1)
            }
            let options: [CFString: Any] = [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: 1024,
                kCGImageSourceShouldCacheImmediately: true,
            ]
            guard let image = CGImageSourceCreateThumbnailAtIndex(sourceImage, 0, options as CFDictionary),
                  let destinationImage = CGImageDestinationCreateWithURL(destination as CFURL, "public.jpeg" as CFString, 1, nil) else {
                throw NSError(domain: "click_trash", code: 2)
            }
            // Passing only the quality option intentionally drops source EXIF, GPS, and camera metadata.
            CGImageDestinationAddImage(destinationImage, image, [kCGImageDestinationLossyCompressionQuality: 0.88] as CFDictionary)
            guard CGImageDestinationFinalize(destinationImage) else {
                throw NSError(domain: "click_trash", code: 3)
            }
        } catch {
            failures.append(relative + ": " + error.localizedDescription)
        }
    }
    if (index + 1) % 100 == 0 { print("resized \(index + 1)/\(images.count)") }
}
print("images=\(images.count) failures=\(failures.count)")
if !failures.isEmpty {
    print(failures.joined(separator: "\n"))
    exit(1)
}
