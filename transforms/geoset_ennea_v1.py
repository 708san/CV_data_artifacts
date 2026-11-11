"""Prepare a leakage-controlled GeoSetEnnea object-detection artifact.

Input files must be fetched from the fixed Mendeley Data v1 file URLs and
verified against manifests/sources/geoset_ennea-v1.json before use.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


DATASET_ID = "geoset_ennea"
SOURCE_URL = "https://data.mendeley.com/datasets/fg97mhsdbr/1"
ATTRIBUTION = (
    "Sakhawat Hossain; Md Sadman Haque; Sadia Islam (2025), "
    "GeoSetEnnea: A Multi-Class Image Dataset for Object Detection of Geometric Tools, "
    "Mendeley Data v1, DOI: 10.17632/fg97mhsdbr.1"
)
RAW_DIR = "GeoSetEnnea/Collected Images/Raw Images/"
META_PATH = "GeoSetEnnea/Generated Dataset/Metadata.csv"
YAML_PATH = "GeoSetEnnea/Generated Dataset/data.yaml"


class PreparationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def source_key_from_generated(filename: str) -> tuple[str, str]:
    match = re.fullmatch(r"(.+?)_(jpg|png)\.rf\.[0-9a-f]+\.jpg", filename, re.IGNORECASE)
    if not match:
        raise PreparationError(f"unsupported generated filename: {filename}")
    return canonical(match.group(1)), match.group(2).lower()


def verify_source_file(root: Path, entry: dict) -> Path:
    relative = PurePosixPath(entry["path"])
    if relative.is_absolute() or ".." in relative.parts or "\\" in entry["path"]:
        raise PreparationError(f"unsafe inventory path: {entry['path']}")
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file():
        raise PreparationError(f"source file missing or symlink: {entry['path']}")
    if path.stat().st_size != entry["size"] or sha256(path) != entry["sha256"]:
        raise PreparationError(f"source pin mismatch: {entry['path']}")
    return path


def parse_classes(yaml_path: Path) -> list[str]:
    names = None
    nc = None
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        if key.strip() == "names":
            import ast
            names = ast.literal_eval(value.strip())
        elif key.strip() == "nc":
            nc = int(value.strip())
    if not isinstance(names, list) or nc != len(names) or len(names) != 9:
        raise PreparationError("unexpected class declaration in fixed data.yaml")
    if len(set(names)) != len(names) or any(not isinstance(name, str) for name in names):
        raise PreparationError("invalid class names")
    return names


def prepare(source_root: Path, inventory_path: Path, group_map_path: Path, destination: Path, manifest_path: Path, report_path: Path) -> dict:
    source_root = source_root.resolve()
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if (inventory.get("dataset_id"), inventory.get("source_version"), inventory.get("source_url")) != (
        DATASET_ID, "1", SOURCE_URL
    ):
        raise PreparationError("source inventory is not pinned to GeoSetEnnea Mendeley v1")
    entries = {entry["path"]: entry for entry in inventory["files"]}
    meta_entry, yaml_entry = entries[META_PATH], entries[YAML_PATH]
    meta_path, yaml_path = verify_source_file(source_root, meta_entry), verify_source_file(source_root, yaml_entry)
    classes = parse_classes(yaml_path)

    all_originals: dict[str, list[dict]] = defaultdict(list)
    for entry in inventory["files"]:
        if entry["path"].startswith(RAW_DIR) and Path(entry["filename"]).suffix.lower() in {".jpg", ".jpeg", ".png"}:
            all_originals[canonical(Path(entry["filename"]).stem)].append(entry)
    screenshot_groups = {
        key for key, items in all_originals.items()
        if any("screenshot" in item["filename"].lower() for item in items)
    }
    originals = {key: items for key, items in all_originals.items() if key not in screenshot_groups}

    candidates: dict[str, list[tuple[dict, dict, str]]] = defaultdict(list)
    non_augmented_candidates = 0
    augmented_images = 0
    matched_original_representations = 0
    excluded_screenshot_representations = 0
    excluded_unmatched_representations = 0
    for entry in inventory["files"]:
        path = entry["path"]
        if not path.startswith("images/") or Path(entry["filename"]).suffix.lower() != ".jpg":
            continue
        # Augmented variants are deliberately omitted: their source photos cross
        # the publisher's train/valid/test boundaries.
        if re.search(r"_aug\d+_(?:jpg|png)\.rf\.", entry["filename"], re.IGNORECASE):
            augmented_images += 1
            continue
        non_augmented_candidates += 1
        key, encoded_ext = source_key_from_generated(entry["filename"])
        if key not in all_originals:
            excluded_unmatched_representations += 1
            continue
        if key in screenshot_groups:
            excluded_screenshot_representations += 1
            continue
        matched_original_representations += 1
        split = path.split("/", 2)[1]
        label_path = f"labels/{split}/{Path(entry['filename']).stem}.txt"
        label = entries.get(label_path)
        if label is None:
            raise PreparationError(f"matching label missing: {label_path}")
        candidates[key].append((entry, label, encoded_ext))

    selected = {}
    for key, options in candidates.items():
        # A source may be represented as both JPG and PNG. Keep one representation
        # per photographed scene; prefer the original JPG when both are listed.
        options.sort(key=lambda item: (item[2] != "jpg", item[0]["path"]))
        selected[key] = options[0]
    if len(selected) != 136:
        raise PreparationError(f"expected 136 camera-photo groups after excluding screenshots, found {len(selected)}")

    with meta_path.open(encoding="utf-8-sig", newline="") as stream:
        metadata_rows = list(csv.DictReader(stream))
    by_image: dict[str, list[dict]] = defaultdict(list)
    for row in metadata_rows:
        by_image[row["Image"]].append(row)

    subset_entries = [meta_entry, yaml_entry]
    per_class_boxes: Counter = Counter()
    for key, (image_entry, label_entry, _) in selected.items():
        subset_entries.extend((image_entry, label_entry))
        if image_entry["filename"] not in by_image:
            raise PreparationError(f"selected image missing from Metadata.csv: {image_entry['filename']}")
        label_path = verify_source_file(source_root, label_entry)
        rows = by_image[image_entry["filename"]]
        label_lines = [line.split() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != len(label_lines) or not rows:
            raise PreparationError(f"annotation count mismatch or empty label: {image_entry['filename']}")
        for row, columns in zip(rows, label_lines):
            if len(columns) != 5:
                raise PreparationError(f"non-bbox annotation: {image_entry['filename']}")
            class_id = int(columns[0])
            if class_id != int(row["Class_ID"]) or classes[class_id] != row["Class_Name"]:
                raise PreparationError(f"class mismatch: {image_entry['filename']}")
            coords = tuple(float(value) for value in columns[1:])
            expected = tuple(float(row[key]) for key in ("X", "Y", "Width", "Height"))
            if any(abs(a - b) > 1e-8 for a, b in zip(coords, expected)):
                raise PreparationError(f"box mismatch: {image_entry['filename']}")
            per_class_boxes[classes[class_id]] += 1

    # This digest pins the selected source file set plus the two official metadata
    # files used to map raw photos, classes and original annotation records.
    lock_lines = "".join(
        f"{entry['path']}\t{entry['size']}\t{entry['sha256']}\n"
        for entry in sorted(subset_entries, key=lambda value: value["path"])
    )
    subset_sha = hashlib.sha256(lock_lines.encode("utf-8")).hexdigest()

    group_document = json.loads(group_map_path.read_text(encoding="utf-8"))
    group_map_sha256 = sha256(group_map_path)
    if group_document.get("dataset_id") != DATASET_ID or group_document.get("threshold_hamming_distance") != 4:
        raise PreparationError("scene-group map is not the reviewed GeoSetEnnea map")
    scene_groups = {}
    for member in group_document.get("members", []):
        if member["path"] in scene_groups:
            raise PreparationError(f"duplicate path in scene-group map: {member['path']}")
        scene_groups[member["path"]] = member
    if len(scene_groups) != group_document.get("image_count"):
        raise PreparationError("scene-group map image count is inconsistent")
    group_ids = set()
    source_scene_group = {}
    for key, (image_entry, _, _) in selected.items():
        member = scene_groups.get(image_entry["path"])
        if member is None or member["sha256"] != image_entry["sha256"]:
            raise PreparationError(f"selected image is not pinned in scene-group map: {image_entry['path']}")
        source_scene_group[key] = member["group_id"]
        group_ids.add(member["group_id"])
    if set(scene_groups) != {item[0]["path"] for item in selected.values()}:
        raise PreparationError("scene-group map and selected images differ")
    groups = sorted(group_ids)
    if len(groups) != group_document.get("group_count"):
        raise PreparationError("scene-group map group count is inconsistent")
    random.Random(42).shuffle(groups)
    train_end = int(len(groups) * 0.70)
    val_end = train_end + int(len(groups) * 0.15)
    assigned_group = {group: "train" for group in groups[:train_end]}
    assigned_group.update({group: "val" for group in groups[train_end:val_end]})
    assigned_group.update({group: "test" for group in groups[val_end:]})
    assigned = {key: assigned_group[group] for key, group in source_scene_group.items()}

    with tempfile.TemporaryDirectory(prefix="geoset-ennea-input-") as temp_dir:
        prepared_source = Path(temp_dir)
        (prepared_source / "classes.json").write_text(
            json.dumps({"classes": classes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        split_counts: Counter = Counter()
        for key, (image_entry, label_entry, _) in selected.items():
            split = assigned[key]
            for entry, folder in ((image_entry, "images"), (label_entry, "labels")):
                source = verify_source_file(source_root, entry)
                target = prepared_source / split / folder / entry["filename"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            split_counts[split] += 1

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from detection_yolo_v1 import prepare as prepare_detection
        artifact = prepare_detection(
            prepared_source, destination, dataset_id=DATASET_ID, artifact_version="0.1.0",
            source_url=SOURCE_URL, source_version="1; selected fixed-file subset",
            source_sha256=subset_sha, license_name="CC BY 4.0", attribution=ATTRIBUTION,
        )

    artifact["transform_version"] = "geoset_ennea_v1.0.0 + detection_yolo_v1.1.0"
    internal_manifest = destination / "manifest.json"
    internal_data = json.loads(internal_manifest.read_text(encoding="utf-8"))
    internal_data["transform_version"] = artifact["transform_version"]
    internal_manifest.write_text(json.dumps(internal_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_record = next(item for item in artifact["files"] if item["path"] == f"{DATASET_ID}/manifest.json")
    manifest_record["sha256"] = sha256(internal_manifest)
    manifest_record["size"] = internal_manifest.stat().st_size

    annotations_by_split: dict[str, Counter] = defaultdict(Counter)
    for line in (destination / "annotations.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        for annotation in record["annotations"]:
            annotations_by_split[record["split"]][classes[annotation["class_id"]]] += 1
    if any(annotations_by_split[split][name] == 0 for split in ("train", "val", "test") for name in classes):
        raise PreparationError("every class must appear in each source-group split")

    # Provide Japanese conditions alongside the common-format artifact.
    readme = destination / "README.md"
    readme.write_text(
        """# GeoSetEnnea（高校生向け教材用）\n\n"""
        "幾何用具9種類の物体検出データです。136枚のカメラ写真を撮影元ごとにtrain/val/testへ分けて収録しています。\n\n"
        "## 出典・ライセンス\n\n"
        f"{ATTRIBUTION}, CC BY 4.0.\n\n"
        "整形内容：Mendeley Data v1の固定file inventoryから元写真に対応する136組を選びました。拡張画像、画面キャプチャ、同じ撮影元の別表現を除き、元写真グループ単位でseed 42の分割に作り直しました。画像は再圧縮せず、YOLO矩形ラベルは共通JSONLとYOLO形式へ記録しました。\n\n"
        "一部の文具に商品名・ロゴが写っています。特定メーカーを推奨・提携するデータではありません。\n\n"
        "課題例：机の上の製図用具を見つけて数える。バングラデシュで撮影された画像なので、日本の教室や文具全体の性能を代表しません。\n",
        encoding="utf-8",
    )
    readme_record = next(item for item in artifact["files"] if item["path"] == f"{DATASET_ID}/README.md")
    readme_record["sha256"] = sha256(readme)
    readme_record["size"] = readme.stat().st_size

    # Add reproducibility details not represented by the common artifact schema.
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "dataset_id": DATASET_ID,
        "source_version": "Mendeley Data v1",
        "source_url": SOURCE_URL,
        "source_inventory": "manifests/sources/geoset_ennea-v1.json",
        "source_subset_sha256": subset_sha,
        "source_subset_files": len(subset_entries),
        "source_subset_size_bytes": sum(entry["size"] for entry in subset_entries),
        "source_full_inventory_files": inventory["file_count"],
        "source_full_inventory_size_bytes": sum(entry["size"] for entry in inventory["files"]),
        "source_images_official_split": inventory["image_count"],
        "selected_unique_original_photo_groups": len(selected),
        "generated_augmented_images_excluded": augmented_images,
        "generated_unmatched_images_excluded": excluded_unmatched_representations,
        "generated_screenshot_images_excluded": excluded_screenshot_representations,
        "generated_duplicate_representations_excluded": matched_original_representations - len(selected),
        "excluded_screenshot_source_groups": len(screenshot_groups),
        "scene_group_map": "reports/geoset_ennea-near-duplicate-groups.json",
        "scene_group_map_sha256": group_map_sha256,
        "scene_group_count": len(groups),
        "scene_group_split_counts": {"train": train_end, "val": val_end - train_end, "test": len(groups) - val_end},
        "split_policy": "seed 42; shuffle scene groups formed by 9x8 grayscale dHash with Hamming distance <=4; 70/15/15; no near-duplicate component crosses splits",
        "split_counts": dict(split_counts),
        "annotations_by_split_and_class": {key: dict(value) for key, value in annotations_by_split.items()},
        "class_names": classes,
        "annotation_rows": sum(per_class_boxes.values()),
        "annotations_by_class": dict(per_class_boxes),
        "metadata_annotation_match": "all selected YOLO rows match fixed Metadata.csv class IDs and normalized boxes",
        "pixel_transform": "none; selected fixed-version generated original photos are copied unchanged",
        "annotation_transform": "normalized YOLO bounding boxes preserved",
        "visual_review": {
            "sample_images": 27,
            "sampled_classes": 9,
            "sampled_splits": ["train", "valid", "test"],
            "findings": "geometric stationery objects match labels; camera-photo sample shows no people; visible product names/logos occur on stationery; screenshot captures were excluded after a visible image-search overlay was found in the source candidate",
        },
        "rights_review": {
            "license": "CC BY 4.0 displayed on official Mendeley Data v1 page",
            "image_origin": "dataset page states authors photographed geometric tools with smartphones in Dhaka stationery shops and libraries",
            "attribution_required": True,
            "modification_notice_required": True,
            "third_party_content": "some sampled stationery displays product branding; included incidentally as part of author-captured scenes and not an endorsement; third-party trademarks remain subject to their owners' rights",
        },
        "all_selected_images_decoded": True,
        "image_decode_method": "macOS sips; 640x640 for all selected images",
        "education_review": {
            "status": "suitable_for_limited_high_school_object_detection_activity",
            "suggested_project": "study-desk geometry-tool inventory or finding misplaced drawing tools",
            "limitations": [
                "photos were collected in Dhaka and are not a representative sample of Japanese stationery or classroom scenes",
                "some augmented variants in the publisher-provided splits cross source-photo groups; all augmented variants are excluded here",
                "small source-photo subset; scores should not be treated as reliable real-world performance",
                "visible product brands are incidental and do not indicate endorsement",
            ],
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("group_map", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = prepare(args.source_root, args.inventory, args.group_map, args.destination, args.manifest, args.report)
    print(json.dumps({key: result[key] for key in ("selected_unique_original_photo_groups", "split_counts", "annotation_rows", "source_subset_sha256")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
