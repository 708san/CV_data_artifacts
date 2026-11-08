import Foundation
import ImageIO
import CoreGraphics
import CryptoKit
struct SourceFile: Codable { let path: String; let role: String; let category: String; let size: Int64; let sha256: String }
struct SourceManifest: Codable { let dataset_id: String; let source_version: String; let files: [SourceFile] }
struct Row: Codable { let image: String; let label: String; let label_id: Int; let split: String; let sample_id: String }
func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func shaFile(_ url: URL) throws -> String { try sha(Data(contentsOf: url, options: .mappedIfSafe)) }
let fm=FileManager.default
let args=CommandLine.arguments
guard args.count == 5 else { fatalError("usage: prepare_recyclable.swift SOURCE_ROOT SOURCE_MANIFEST OUTPUT_ROOT ARTIFACT_MANIFEST") }
let sourceRoot=URL(fileURLWithPath:args[1],isDirectory:true)
let sourceManifestURL=URL(fileURLWithPath:args[2])
let outputRoot=URL(fileURLWithPath:args[3],isDirectory:true)
let artifactManifestURL=URL(fileURLWithPath:args[4])
guard !fm.fileExists(atPath:outputRoot.path), !fm.fileExists(atPath:artifactManifestURL.path) else { fatalError("refusing to overwrite existing output") }
let source=try JSONDecoder().decode(SourceManifest.self,from:Data(contentsOf:sourceManifestURL))
guard source.dataset_id=="recyclable_waste", source.source_version=="1", source.files.count==989 else { fatalError("unexpected fixed source manifest") }
var totalSourceBytes:Int64=0
for item in source.files { let url=sourceRoot.appendingPathComponent(item.path); let attrs=try fm.attributesOfItem(atPath:url.path); let size=attrs[.size] as! Int64; let digest=try shaFile(url); guard size==item.size && digest==item.sha256 else { fatalError("source size/SHA mismatch: \(item.path)") }; totalSourceBytes += size }
let sourceDigestInput=source.files.sorted{$0.path<$1.path}.map{"\($0.path)\0\($0.size)\0\($0.sha256)\n"}.joined()
let sourceFileSetSHA=sha(Data(sourceDigestInput.utf8))
var byDigest:[String:SourceFile]=[:], duplicates:[[String:String]]=[], uniqueByClass:[String:[SourceFile]]=[:]
for item in source.files.sorted(by:{$0.path<$1.path}) { if let first=byDigest[item.sha256] { guard first.category==item.category else { fatalError("duplicate crosses classes") }; duplicates.append(["path":item.path,"duplicate_of":first.path,"sha256":item.sha256]) } else { byDigest[item.sha256]=item; uniqueByClass[item.category,default:[]].append(item) } }
let classes=uniqueByClass.keys.sorted(); let datasetRoot=outputRoot.appendingPathComponent("recyclable_waste",isDirectory:true)
let imagesRoot=datasetRoot.appendingPathComponent("images",isDirectory:true); try fm.createDirectory(at:imagesRoot,withIntermediateDirectories:true)
var rows:[Row]=[], classCounts:[String:[String:Int]]=[:], splitCounts:[String:Int] = ["train":0,"val":0,"test":0], outputFiles:[[String:Any]]=[]
for (classID,label) in classes.enumerated() {
 let items=uniqueByClass[label]!.sorted { a,b in let x=sha(Data("seed=42|\(label)|\(a.sha256)".utf8)), y=sha(Data("seed=42|\(label)|\(b.sha256)".utf8)); return x==y ? a.path<b.path : x<y }
 let nTrain=Int((Double(items.count)*0.70).rounded()), nVal=Int((Double(items.count)*0.15).rounded()); var local:[String:Int] = ["train":0,"val":0,"test":0]
 for (index,item) in items.enumerated() {
  let split=index<nTrain ? "train" : (index<nTrain+nVal ? "val" : "test"), fileID=String(item.sha256.prefix(16)), relative="images/\(split)/\(label)/\(fileID).jpg", target=datasetRoot.appendingPathComponent(relative)
  try fm.createDirectory(at:target.deletingLastPathComponent(),withIntermediateDirectories:true)
  guard let src=CGImageSourceCreateWithURL(sourceRoot.appendingPathComponent(item.path) as CFURL,nil) else { fatalError("cannot open \(item.path)") }
  let opts:[CFString:Any]=[kCGImageSourceCreateThumbnailFromImageAlways:true,kCGImageSourceCreateThumbnailWithTransform:true,kCGImageSourceThumbnailMaxPixelSize:512]
  guard let thumbnail=CGImageSourceCreateThumbnailAtIndex(src,0,opts as CFDictionary), let dst=CGImageDestinationCreateWithURL(target as CFURL,"public.jpeg" as CFString,1,nil) else { fatalError("cannot transform \(item.path)") }
  CGImageDestinationAddImage(dst,thumbnail,[kCGImageDestinationLossyCompressionQuality:0.86] as CFDictionary); guard CGImageDestinationFinalize(dst) else { fatalError("write failed") }
  guard let check=CGImageSourceCreateWithURL(target as CFURL,nil), let decoded=CGImageSourceCreateImageAtIndex(check,0,nil) else { fatalError("output decode failed") }
  let props=CGImageSourceCopyPropertiesAtIndex(check,0,nil) as? [String:Any] ?? [:]
  guard props["{GPS}"]==nil && max(decoded.width,decoded.height)<=512 else { fatalError("metadata or dimensions remain in \(relative)") }
  let outSHA=try shaFile(target), outSize=try fm.attributesOfItem(atPath:target.path)[.size] as! Int64
  rows.append(Row(image:relative,label:label,label_id:classID,split:split,sample_id:fileID)); local[split,default:0]+=1; splitCounts[split,default:0]+=1
  outputFiles.append(["path":"recyclable_waste/\(relative)","sha256":outSHA,"size":outSize])
 }
 classCounts[label]=["unique_images":items.count,"excluded_duplicates":source.files.filter{$0.category==label}.count-items.count,"train":local["train"]!,"val":local["val"]!,"test":local["test"]!]
}
rows.sort{($0.label_id,$0.split,$0.image)<($1.label_id,$1.split,$1.image)}
let csv="image,label,label_id,split,sample_id\n"+rows.map{"\($0.image),\($0.label),\($0.label_id),\($0.split),\($0.sample_id)"}.joined(separator:"\n")+"\n"
try Data(csv.utf8).write(to:datasetRoot.appendingPathComponent("labels.csv"))
let jsonlEncoder=JSONEncoder(); jsonlEncoder.outputFormatting=[.sortedKeys,.withoutEscapingSlashes]
let jsonl=rows.map{row in String(data:try! jsonlEncoder.encode(row),encoding:.utf8)!}.joined(separator:"\n")+"\n"; try Data(jsonl.utf8).write(to:datasetRoot.appendingPathComponent("metadata.jsonl"))
let attribution="João Alves (2026), Recyclable Waste Image Dataset, Mendeley Data v1, DOI: 10.17632/h5pxbsdz4m.1, CC BY 4.0."
let metadata:[String:Any]=["dataset_id":"recyclable_waste","artifact_version":"0.1.0","task":"classification","classes":classes,"class_counts":classCounts,"split_counts":splitCounts,"image_count":rows.count,"image_format":"JPEG RGB, maximum dimension 512, quality 86","transformations":["Removed EXIF, GPS, TIFF, and other source metadata by decoding and re-encoding.","Applied EXIF orientation before resizing; preserved aspect ratio; longest edge capped at 512 pixels.","Excluded 12 exact duplicate files, retaining one image per SHA-256 group.","Deterministic stratified train/validation/test split (seed 42, 70/15/remaining per class)."],"source_file_set_sha256":sourceFileSetSHA,"source_attribution":attribution,"source_url":"https://data.mendeley.com/datasets/h5pxbsdz4m/1","source_version":"1","manual_privacy_review":"Five representative images visually inspected; full manual image review remains incomplete."]
let jsonData=try JSONSerialization.data(withJSONObject:metadata,options:[.prettyPrinted,.sortedKeys,.withoutEscapingSlashes]); try jsonData.write(to:datasetRoot.appendingPathComponent("manifest.json"))
let readme="# Recyclable Waste（教材用候補）\n\nMendeley Data v1の公開分989枚のうち、完全一致重複12枚を除いた977枚を整備しました。\n\n- 5クラス：段ボール533、ガラス49、金属90、紙96、プラスチック209（完全一致重複を除外後）\n- 長辺512px以下のJPEGへ変換し、EXIF/GPS/TIFF等のメタデータを除去しています。\n- `labels.csv`に画像、クラス名、クラスID、分割、sample IDを記録しています。\n- クラス数に大きな偏りがあります。正解率だけで比較せず、クラス別再現率やMacro F1を確認する題材にできます。\n- 画像にブランド・包装の文字が写ることがあります。実際の分別判断を自動決定する用途には使いません。\n- 全画像の人手によるプライバシー確認は未完了です。\n\n## 出典と利用条件\n\n元データ：\(attribution) 元の公開ページはCC BY 4.0と表示し、公開分は著者自身が収集した画像のみと説明しています。変更点は画素サイズ・JPEG再符号化・メタデータ除去・完全一致重複の除外・分割追加です。\n"
try Data(readme.utf8).write(to:datasetRoot.appendingPathComponent("README.md"))
let license="# Recyclable Waste v1 — attribution and changes\n\n\(attribution)\n\nThe Mendeley Data v1 page displays CC BY 4.0 and states that the public release contains only images collected by the author; third-party dataset images were excluded.\n\nChanges: 12 exact duplicate files were excluded; the remaining 977 images were decoded, EXIF orientation was applied, the longest dimension was limited to 512 pixels, and JPEG quality 86 was used. EXIF, GPS, TIFF, and other source metadata were removed. A deterministic stratified train/validation/test assignment (seed 42) was added.\n\nA full manual privacy review has not been completed. Five representative images were visually reviewed. Some images contain visible product or brand marks. This dataset is for classroom experiments and must not be used to automate real-world waste-sorting decisions.\n"
try Data(license.utf8).write(to:datasetRoot.appendingPathComponent("LICENSE.md"))
for name in ["labels.csv","metadata.jsonl","manifest.json","README.md","LICENSE.md"] { let url=datasetRoot.appendingPathComponent(name); outputFiles.append(["path":"recyclable_waste/\(name)","sha256":try shaFile(url),"size":try fm.attributesOfItem(atPath:url.path)[.size] as! Int64]) }
let artifact:[String:Any]=["manifest_version":"1.0.0","dataset_id":"recyclable_waste","artifact_version":"0.1.0","files":outputFiles.sorted{($0["path"] as! String)<($1["path"] as! String)},"image_count":rows.count,"label_format":"classification_csv_and_jsonl","transform_version":"recyclable_waste_sanitize_resize_dedupe_split_v1","license":"CC BY 4.0","attribution":attribution,"source":["url":"https://data.mendeley.com/datasets/h5pxbsdz4m/1","version":"1","file_count":source.files.count,"total_bytes":totalSourceBytes,"file_set_sha256":sourceFileSetSHA,"sha256":sourceFileSetSHA]]
let artifactData=try JSONSerialization.data(withJSONObject:artifact,options:[.prettyPrinted,.sortedKeys,.withoutEscapingSlashes]); try artifactData.write(to:artifactManifestURL)
print(String(data:jsonData,encoding:.utf8)!); print("artifact_files=\(outputFiles.count) source_file_set_sha256=\(sourceFileSetSHA)")
