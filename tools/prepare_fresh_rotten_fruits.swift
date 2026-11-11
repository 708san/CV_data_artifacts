import Foundation
import ImageIO
import CoreGraphics
import CryptoKit

struct Row: Codable {
    let image: String
    let label: String
    let label_id: Int
    let fruit: String
    let freshness: String
    let split: String
    let sample_id: String
}
func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func shaFile(_ url: URL) throws -> String { try sha(Data(contentsOf: url, options: .mappedIfSafe)) }
let fm = FileManager.default
let args = CommandLine.arguments
guard args.count == 4 else { fatalError("usage: prepare_fresh_rotten_fruits.swift SOURCE_ROOT OUTPUT_ROOT ARTIFACT_MANIFEST") }
let sourceRoot = URL(fileURLWithPath: args[1], isDirectory: true)
let outputRoot = URL(fileURLWithPath: args[2], isDirectory: true)
let artifactManifestURL = URL(fileURLWithPath: args[3])
guard !fm.fileExists(atPath: outputRoot.path), !fm.fileExists(atPath: artifactManifestURL.path) else { fatalError("refusing to overwrite existing output") }
let expectedSourceSHA = "f89d67d4c4b24810bcd8406db877db6b1ac9834cea0b0cb56d65acebe59e66ff"
let sourceArchiveSHA = try shaFile(URL(fileURLWithPath: "/private/tmp/fresh-rotten-original-v1.zip"))
guard sourceArchiveSHA == expectedSourceSHA else { fatalError("fixed source archive SHA mismatch") }
let dataRoot = sourceRoot.appendingPathComponent("Original Image", isDirectory: true)
let classDirs = try fm.contentsOfDirectory(at: dataRoot, includingPropertiesForKeys: nil).filter { $0.hasDirectoryPath }.sorted { $0.lastPathComponent < $1.lastPathComponent }
guard classDirs.count == 16 else { fatalError("expected 16 source class folders, got \(classDirs.count)") }
let datasetRoot = outputRoot.appendingPathComponent("fresh_rotten_fruits", isDirectory: true)
try fm.createDirectory(at: datasetRoot, withIntermediateDirectories: true)
let imagesRoot = datasetRoot.appendingPathComponent("images", isDirectory: true)
var classImages: [String: [URL]] = [:]
for dir in classDirs {
    let paths = try fm.contentsOfDirectory(at: dir, includingPropertiesForKeys: [.isSymbolicLinkKey], options: [.skipsHiddenFiles]).sorted { $0.lastPathComponent < $1.lastPathComponent }
    guard paths.allSatisfy({ !$0.lastPathComponent.hasPrefix(".") && $0.pathExtension.lowercased() == "jpg" }) else { fatalError("unexpected non-JPEG entry in \(dir.lastPathComponent)") }
    guard paths.count == 200 else { fatalError("expected 200 images in \(dir.lastPathComponent), got \(paths.count)") }
    classImages[dir.lastPathComponent] = paths
}
let classNames = classDirs.map { $0.lastPathComponent }
var digestOwner: [String: (label: String, source: URL)] = [:]
var uniqueByClass: [String: [(url: URL, sha: String)]] = [:]
var duplicates: [[String: String]] = []
var sourceBytes: Int64 = 0
for label in classNames {
    for path in classImages[label]! {
        let attrs = try fm.attributesOfItem(atPath: path.path)
        sourceBytes += attrs[.size] as! Int64
        let digest = try shaFile(path)
        if let first = digestOwner[digest] {
            guard first.label == label else { fatalError("exact duplicate has conflicting labels: \(first.source.path), \(path.path)") }
            duplicates.append(["path": path.lastPathComponent, "class": label, "duplicate_of": first.source.lastPathComponent, "sha256": digest])
            continue
        }
        digestOwner[digest] = (label, path)
        uniqueByClass[label, default: []].append((path, digest))
    }
}
let classIDs = Dictionary(uniqueKeysWithValues: classNames.sorted().enumerated().map { ($1, $0) })
var rows: [Row] = []
var outputFiles: [[String: Any]] = []
var splitCounts: [String: Int] = ["train": 0, "val": 0, "test": 0]
var classReport: [String: [String: Int]] = [:]
for label in classNames.sorted() {
    let items = uniqueByClass[label]!.sorted {
        let a = sha(Data("seed=42|\(label)|\($0.sha)".utf8)), b = sha(Data("seed=42|\(label)|\($1.sha)".utf8))
        return a == b ? $0.url.lastPathComponent < $1.url.lastPathComponent : a < b
    }
    let nTrain = Int((Double(items.count) * 0.70).rounded()), nVal = Int((Double(items.count) * 0.15).rounded())
    var local: [String: Int] = ["train": 0, "val": 0, "test": 0]
    let fruit = String(label.dropFirst(label.hasPrefix("Fresh") ? 5 : 6)).lowercased()
    let freshness = label.hasPrefix("Fresh") ? "fresh" : "rotten"
    let canonical = "\(freshness)_\(fruit)"
    for (index, item) in items.enumerated() {
        let split = index < nTrain ? "train" : (index < nTrain + nVal ? "val" : "test")
        let id = String(item.sha.prefix(16))
        let relative = "images/\(split)/\(canonical)/\(id).jpg"
        let target = datasetRoot.appendingPathComponent(relative)
        try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
        guard let src = CGImageSourceCreateWithURL(item.url as CFURL, nil) else { fatalError("cannot read source image \(item.url.path)") }
        let opts: [CFString: Any] = [kCGImageSourceCreateThumbnailFromImageAlways: true, kCGImageSourceCreateThumbnailWithTransform: true, kCGImageSourceThumbnailMaxPixelSize: 512]
        guard let thumb = CGImageSourceCreateThumbnailAtIndex(src, 0, opts as CFDictionary), let dst = CGImageDestinationCreateWithURL(target as CFURL, "public.jpeg" as CFString, 1, nil) else { fatalError("cannot transform \(item.url.path)") }
        CGImageDestinationAddImage(dst, thumb, [kCGImageDestinationLossyCompressionQuality: 0.86] as CFDictionary)
        guard CGImageDestinationFinalize(dst), let check = CGImageSourceCreateWithURL(target as CFURL, nil), let decoded = CGImageSourceCreateImageAtIndex(check, 0, nil) else { fatalError("output write/decode failed: \(relative)") }
        let props = CGImageSourceCopyPropertiesAtIndex(check, 0, nil) as? [String: Any] ?? [:]
        guard props["{GPS}"] == nil && max(decoded.width, decoded.height) <= 512 else { fatalError("metadata/dimensions check failed: \(relative)") }
        let outSHA = try shaFile(target), outSize = try fm.attributesOfItem(atPath: target.path)[.size] as! Int64
        rows.append(Row(image: relative, label: canonical, label_id: classIDs[label]!, fruit: fruit, freshness: freshness, split: split, sample_id: id))
        local[split, default: 0] += 1
        splitCounts[split, default: 0] += 1
        outputFiles.append(["path": "fresh_rotten_fruits/\(relative)", "sha256": outSHA, "size": outSize])
    }
    classReport[canonical] = ["source_images": classImages[label]!.count, "unique_images": items.count, "excluded_exact_duplicates": classImages[label]!.count - items.count, "train": local["train"]!, "val": local["val"]!, "test": local["test"]!]
}
rows.sort { ($0.label_id, $0.split, $0.image) < ($1.label_id, $1.split, $1.image) }
let csv = "image,label,label_id,fruit,freshness,split,sample_id\n" + rows.map { "\($0.image),\($0.label),\($0.label_id),\($0.fruit),\($0.freshness),\($0.split),\($0.sample_id)" }.joined(separator: "\n") + "\n"
try Data(csv.utf8).write(to: datasetRoot.appendingPathComponent("labels.csv"))
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
let metadataLines = try rows.map { row -> String in
    let item: [String: String] = ["file_name": row.image, "label": row.label, "split": row.split]
    return String(data: try JSONSerialization.data(withJSONObject: item, options: [.sortedKeys, .withoutEscapingSlashes]), encoding: .utf8)!
}.joined(separator: "\n") + "\n"
try Data(metadataLines.utf8).write(to: datasetRoot.appendingPathComponent("metadata.jsonl"))
let attribution = "Nusrat Sultana, Musfika Jahan, and Mohammad Shorif Uddin (2022), Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality, Mendeley Data v1, DOI: 10.17632/bdd69gyhv8.1, CC BY 4.0."
let transformations = ["Used only the 3,200 original images; excluded the separate augmented archive.", "Excluded exact duplicate files within each label, retaining the first lexicographic source filename.", "Applied image orientation, resized longest edge to 512 pixels, and re-encoded as JPEG quality 86.", "Removed source metadata by decoding and re-encoding.", "Created deterministic stratified train/validation/test splits (seed 42; 70/15/remaining per class)."]
let classes = classNames.sorted().map { label in let fruit = String(label.dropFirst(label.hasPrefix("Fresh") ? 5 : 6)).lowercased(); return "\(label.hasPrefix("Fresh") ? "fresh" : "rotten")_\(fruit)" }
let metadata: [String: Any] = ["case_id": "fresh_rotten_fruits", "version": "v0.1.0", "dataset_id": "fresh_rotten_fruits", "artifact_version": "0.1.0", "task": "classification", "classes": classes, "class_counts": classReport, "split_counts": splitCounts, "image_count": rows.count, "source_image_count": 3200, "exact_duplicates_excluded": duplicates.count, "image_format": "JPEG RGB, longest edge <=512, quality 86", "transformations": transformations, "source_archive_sha256": sourceArchiveSHA, "source_archive_bytes": 2794170228, "source_image_bytes": sourceBytes, "source_attribution": attribution, "source_url": "https://data.mendeley.com/datasets/bdd69gyhv8/1", "source_version": "1", "visual_review": "64 deterministic representative source images reviewed across all 16 classes; no visible people, logos, or unrelated content identified.", "limitations": ["Labels describe the dataset's visual fresh/rotten categories and are not food-safety or edibility assessments.", "Visual review was representative sampling, not manual review of every image."]]
let jsonData = try JSONSerialization.data(withJSONObject: metadata, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
try jsonData.write(to: datasetRoot.appendingPathComponent("manifest.json"))
let readme = "# Fresh and Rotten Fruits\n\n3,200 original images of eight fruit types, with the source authors' fresh/rotten labels. For classroom work on image classification, food waste, and how visual labels can be evaluated.\n\n- 16 classes: apple, banana, grape, guava, jujube, orange, pomegranate, and strawberry, each labeled fresh or rotten.\n- Images were reported as collected at fruit shops and real fields; class labels were assigned with help from a domain expert at an agricultural institute.\n- This version uses original images only; the separate augmented archive is excluded.\n- Images are orientation-corrected, resized to a 512-pixel maximum edge, re-encoded, and stripped of source metadata. Exact duplicate files are excluded.\n- `labels.csv` gives image path, combined label, label ID, fruit, freshness, split, and stable sample ID.\n- The split is deterministic (seed 42) and stratified by the 16 source classes.\n\n## Important limit\n\nThese labels are visual categories from a research dataset. They cannot determine whether food is safe to eat, edible, fresh in a food-safety sense, or healthy. Do not use model results for food-safety or health decisions.\n\n## Source and license\n\n\(attribution) The source page identifies the dataset as CC BY 4.0. Changes: augmented images excluded, exact duplicates excluded, orientation applied, image dimensions limited to 512 pixels, JPEG re-encoding performed, source metadata removed, and reproducible splits and CSV labels added.\n"
try Data(readme.utf8).write(to: datasetRoot.appendingPathComponent("README.md"))
let license = "# Fresh and Rotten Fruits v1 — attribution and changes\n\n\(attribution)\n\nThe Mendeley Data v1 record identifies the dataset as CC BY 4.0.\n\nChanges: only original images were used; augmented images were excluded. Exact duplicate images within a label were excluded. Remaining images were decoded with orientation applied, resized to a maximum edge of 512 pixels, re-encoded as JPEG at quality 86, and stripped of source metadata. Deterministic stratified train/validation/test splits (seed 42) and `labels.csv` were added.\n\nThe source authors report collection at fruit shops and real fields and fresh/rotten categorization with help from an agricultural institute domain expert. These labels are not food-safety or edibility assessments.\n"
try Data(license.utf8).write(to: datasetRoot.appendingPathComponent("LICENSE.md"))
for name in ["labels.csv", "metadata.jsonl", "manifest.json", "README.md", "LICENSE.md"] {
    let url = datasetRoot.appendingPathComponent(name)
    outputFiles.append(["path": "fresh_rotten_fruits/\(name)", "sha256": try shaFile(url), "size": try fm.attributesOfItem(atPath: url.path)[.size] as! Int64])
}
let fileSetInput = outputFiles.sorted { ($0["path"] as! String) < ($1["path"] as! String) }.map { "\($0["path"]!)\0\($0["size"]!)\0\($0["sha256"]!)\n" }.joined()
let fileSetSHA = sha(Data(fileSetInput.utf8))
let artifact: [String: Any] = ["manifest_version": "1.0.0", "dataset_id": "fresh_rotten_fruits", "artifact_version": "0.1.0", "files": outputFiles.sorted { ($0["path"] as! String) < ($1["path"] as! String) }, "image_count": rows.count, "label_format": "classification_csv_and_jsonl", "transform_version": "fresh_rotten_fruits_original_sanitize_resize_dedupe_split_v1", "license": "CC BY 4.0", "attribution": attribution, "source": ["url": "https://data.mendeley.com/datasets/bdd69gyhv8/1", "version": "1", "sha256": sourceArchiveSHA]]
let artifactData = try JSONSerialization.data(withJSONObject: artifact, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
try artifactData.write(to: artifactManifestURL)
let audit: [String: Any] = ["dataset_id": "fresh_rotten_fruits", "source_url": "https://data.mendeley.com/datasets/bdd69gyhv8/1", "source_version": "1", "license": "CC BY 4.0", "source_archive_sha256": sourceArchiveSHA, "source_archive_bytes": 2794170228, "source_images": 3200, "class_count": 16, "class_counts": classReport, "image_decode_failures": 0, "output_decode_failures": 0, "exact_duplicates_excluded": duplicates, "split_counts": splitCounts, "artifact_image_count": rows.count, "artifact_file_set_sha256": fileSetSHA, "visual_review": "64 deterministic representative source images reviewed across all 16 classes; no visible people, logos, or unrelated content identified.", "rights_review": "Mendeley Data v1 lists CC BY 4.0. Source description says images were collected at fruit shops and real fields; labels assigned with help from an agricultural institute domain expert.", "publication_status": "prepared_pending_rights_review", "limitations": ["No individual model output should be presented as a food-safety or edibility decision.", "Representative visual review does not equal a full manual review."]]
let auditData = try JSONSerialization.data(withJSONObject: audit, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
try auditData.write(to: outputRoot.appendingPathComponent("fresh-rotten-fruits-v1-full-audit.json"))
print("source_archive_sha256=\(sourceArchiveSHA)")
print("image_count=\(rows.count) duplicates_excluded=\(duplicates.count) split_counts=\(splitCounts)")
print("file_set_sha256=\(fileSetSHA)")
let totalArtifactBytes = outputFiles.reduce(Int64(0)) { $0 + (($1["size"] as? NSNumber)?.int64Value ?? 0) }
print("artifact_bytes=\(totalArtifactBytes)")
