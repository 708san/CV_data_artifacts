"""Create Recyclable Waste v0.1.1 by excluding one political-poster image.

Input is the previously prepared, fixed v0.1.0 artifact. Its exact archive hash,
manifest entries, member paths, and file digests are checked before modification.
All retained image bytes remain unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


INPUT_SHA256 = "39c52710ddaeb4e662dbbf3ba7cd95725a8b11cf2b22434d04bc52626b721299"
EXCLUDED_IMAGE = "recyclable_waste/images/train/paper/4c9f3fbe83bd01a5.jpg"
EXCLUDED_SOURCE = "paper/UHW_Paper  (72).jpg"
EXCLUDED_SOURCE_SHA256 = "4c9f3fbe83bd01a5a4e03ded0598699df5278f0262f2e72754e7e4a71e6522e0"
ATTRIBUTION = (
    "João Alves (2026), Recyclable Waste Image Dataset, Mendeley Data v1, "
    "DOI: 10.17632/h5pxbsdz4m.1, CC BY 4.0."
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    names: set[str] = set()
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
            raise ValueError(f"unsafe archive path: {info.filename}")
        if info.filename in names:
            raise ValueError(f"duplicate archive path: {info.filename}")
        names.add(info.filename)
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ValueError(f"symlink in archive: {info.filename}")
    bad = archive.testzip()
    if bad:
        raise ValueError(f"ZIP CRC mismatch: {bad}")
    archive.extractall(destination)


def prepare(input_zip: Path, base_manifest_path: Path, source_manifest_path: Path, output_zip: Path, manifest_path: Path, audit_path: Path) -> dict:
    if digest(input_zip) != INPUT_SHA256:
        raise ValueError("v0.1.0 archive SHA-256 does not match the pinned input")
    base = json.loads(base_manifest_path.read_text(encoding="utf-8"))
    if base.get("dataset_id") != "recyclable_waste" or base.get("artifact_version") != "0.1.0":
        raise ValueError("base manifest is not Recyclable Waste v0.1.0")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_match = [item for item in source_manifest.get("files", []) if item.get("path") == EXCLUDED_SOURCE]
    if source_manifest.get("dataset_id") != "recyclable_waste" or len(source_match) != 1 or source_match[0].get("sha256") != EXCLUDED_SOURCE_SHA256:
        raise ValueError("excluded source file does not match the fixed Mendeley source manifest")
    with tempfile.TemporaryDirectory(prefix="recyclable-waste-v011-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(input_zip) as archive:
            safe_extract(archive, root)
        records = {item["path"]: item for item in base["files"]}
        for relative, item in records.items():
            path = root / relative
            if path.is_symlink() or not path.is_file() or path.stat().st_size != item["size"] or digest(path) != item["sha256"]:
                raise ValueError(f"base manifest mismatch: {relative}")
        image = root / EXCLUDED_IMAGE
        if not image.is_file() or Path(EXCLUDED_IMAGE).stem != EXCLUDED_SOURCE_SHA256[:16] or EXCLUDED_IMAGE not in records:
            raise ValueError("the reviewed political-poster image is not the pinned artifact member")

        metadata_path = root / "recyclable_waste/metadata.jsonl"
        metadata = [json.loads(line) for line in metadata_path.read_text(encoding="utf-8").splitlines()]
        removed = [row for row in metadata if row["image"] == EXCLUDED_IMAGE.removeprefix("recyclable_waste/")]
        if len(removed) != 1:
            raise ValueError(f"expected exactly one metadata row for excluded image; found {len(removed)}")
        image.unlink()
        metadata = [row for row in metadata if row["image"] != EXCLUDED_IMAGE.removeprefix("recyclable_waste/")]
        metadata_path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in metadata), encoding="utf-8")

        labels_path = root / "recyclable_waste/labels.csv"
        with labels_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            labels = [row for row in reader if row["image"] != EXCLUDED_IMAGE.removeprefix("recyclable_waste/")]
        if fields is None or len(labels) != len(metadata):
            raise ValueError("CSV and JSONL rows differ after exclusion")
        with labels_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(labels)

        data_root = root / "recyclable_waste"
        split_counts = {name: 0 for name in ("train", "val", "test")}
        old_internal_manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
        old_class_counts = old_internal_manifest["class_counts"]
        by_class: dict[str, dict[str, int]] = {}
        for row in metadata:
            counts = by_class.setdefault(row["label"], {"unique_images": 0, "excluded_duplicates": old_class_counts[row["label"]]["excluded_duplicates"], "train": 0, "val": 0, "test": 0})
            counts["unique_images"] += 1
            counts[row["split"]] += 1
            split_counts[row["split"]] += 1

        internal_manifest = old_internal_manifest
        internal_manifest["artifact_version"] = "0.1.1"
        internal_manifest["image_count"] = len(metadata)
        internal_manifest["class_counts"] = by_class
        internal_manifest["split_counts"] = split_counts
        internal_manifest["manual_privacy_review"] = (
            "All 977 images were visually screened on contact sheets; one image containing a political campaign poster with a person's portrait was excluded. "
            "No identifiable photographed bystanders were observed in the retained set. Product/brand marks remain incidental in some images."
        )
        internal_manifest["transformations"].append(
            "Excluded one paper-category image containing a political campaign poster and portrait after full-set visual review."
        )
        (data_root / "manifest.json").write_text(json.dumps(internal_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        readme = f"""# Recyclable Waste（教材用データ）

Mendeley Data v1の公開画像989枚から完全一致重複12枚を除き、さらに全977枚の一覧画像を確認して、政治キャンペーンのポスターに人物の肖像が写る1枚を除外しました。残る976枚を5クラスに整理しています。

- 段ボール、ガラス、金属、紙、プラスチックの5クラス
- 画像は長辺512px以下。EXIF/GPS/TIFF等のメタデータを除去
- 分割：train {split_counts['train']}、validation {split_counts['val']}、test {split_counts['test']}
- クラス数には偏りがあります。正解率だけでなく、クラス別再現率やMacro F1も確認してください。
- 一部に商品名・ロゴが写ります。製品の推薦や承認を示すものではありません。

## 出典・ライセンス

{ATTRIBUTION} 公開ページはCC BY 4.0と表示し、第三者データ由来の画像を除き、著者自身が収集した画像のみを公開したと説明しています。出典と変更内容を表示してください。

変更：完全一致重複12枚と、上記の政治キャンペーンポスターが写る1枚を除外。画像を再符号化・縮小し、画像メタデータを除去して分割情報を追加しました。実際の自治体分別を自動決定する用途には使わないでください。
"""
        (data_root / "README.md").write_text(readme, encoding="utf-8")
        license_text = f"""# Recyclable Waste v0.1.1 — attribution and changes

{ATTRIBUTION}

The Mendeley Data v1 page displays CC BY 4.0 and states that its public release contains only author-collected images, excluding images from third-party datasets.

Changes to the public source: 12 exact duplicate files were excluded. All 977 retained source images were visually screened on contact sheets. One paper-category image containing a political campaign poster and a person's portrait was excluded. The remaining 976 images preserve the earlier v0.1.0 processed pixels; one image was deleted, and the CSV/JSONL metadata, counts, manifests, and documentation were updated. No retained image was altered in this revision.

Product and brand marks appear incidentally in some retained photographs and remain subject to their owners' rights. Their presence does not imply endorsement. This dataset is for classroom experiments, not automated real-world waste-sorting decisions.
"""
        (data_root / "LICENSE.md").write_text(license_text, encoding="utf-8")

        # Recreate an exhaustive per-file manifest for the new version.
        files = []
        for path in sorted(p for p in data_root.rglob("*") if p.is_file()):
            rel = path.relative_to(root).as_posix()
            files.append({"path": rel, "size": path.stat().st_size, "sha256": digest(path)})
        out_manifest = {
            "manifest_version": "1.0.0", "dataset_id": "recyclable_waste", "artifact_version": "0.1.1",
            "files": files, "image_count": len(metadata), "label_format": "classification_csv_and_jsonl",
            "transform_version": "recyclable_waste_v1.1.0", "license": "CC BY 4.0", "attribution": ATTRIBUTION,
            "source": {"url": "https://data.mendeley.com/datasets/h5pxbsdz4m/1", "version": "Mendeley Data v1; derived from fixed artifact v0.1.0", "sha256": INPUT_SHA256},
            "excluded_images": [{"source_path": EXCLUDED_SOURCE, "source_sha256": EXCLUDED_SOURCE_SHA256, "reason": "political campaign poster and a person's portrait appear on discarded paper"}],
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        audit = {
            "dataset_id": "recyclable_waste", "source_version": "Mendeley Data v1", "source_url": "https://data.mendeley.com/datasets/h5pxbsdz4m/1",
            "source_license": "CC BY 4.0 displayed on official page; public subset described as author-collected images only",
            "base_artifact": {"version": "0.1.0", "sha256": INPUT_SHA256, "images": 977},
            "revision": {"version": "0.1.1", "image_count": len(metadata), "split_counts": split_counts, "class_counts": by_class,
                         "excluded_source_path": EXCLUDED_SOURCE, "excluded_source_sha256": EXCLUDED_SOURCE_SHA256,
                         "excluded_prepared_path": EXCLUDED_IMAGE, "excluded_prepared_sha256": records[EXCLUDED_IMAGE]["sha256"],
                         "reason": "The image shows a printed political campaign poster with a person's portrait on discarded paper; it is unrelated to classifying recyclable material and was removed after all-image visual review.",
                         "retained_image_bytes_changed": False},
            "visual_review": {"reviewed_images": 977, "method": "All v0.1.0 images were shown on 10 contact sheets at thumbnail scale. The one image with a person's portrait and political messaging was opened at full resolution and excluded.",
                              "remaining_scope": "Brand/product packaging marks remain incidental; no identifiable photographed bystander was observed among the retained images. The review is not a trademark legal opinion."},
            "rights_review": {"status": "approved_for_redistribution_with_attribution_and_change_notice", "license": "CC BY 4.0", "third_party_scope": "source page says public subset excludes third-party dataset images and contains author-collected images; one image with incidental political portrait was removed; remaining product marks are incidental and non-endorsed"},
            "education_review": {"status": "suitable_for_high_school_recycling_classification_activity", "use_case": "compare image model predictions with the five material categories and discuss class imbalance", "limitations": ["class imbalance", "photographs come from Portugal and do not represent Japanese municipal sorting rules", "predictions must not make actual sorting decisions"]},
        }
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(p for p in data_root.rglob("*") if p.is_file()):
                archive.write(path, path.relative_to(root).as_posix())
    return {"image_count": len(metadata), "split_counts": split_counts, "class_counts": by_class, "manifest_file_count": len(files)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_zip", type=Path)
    parser.add_argument("base_manifest", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_zip", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input_zip, args.base_manifest, args.source_manifest, args.output_zip, args.manifest, args.audit), ensure_ascii=False, indent=2))
