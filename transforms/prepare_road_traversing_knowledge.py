"""Prepare the fixed Mendeley RTK source without changing image or mask pixels."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
import zipfile
from pathlib import Path, PurePosixPath

DATASET_ID = "road_traversing_knowledge"
SOURCE_SHA256 = "78803e8df89eae6130139ee9c48de947edd08015fe56826c30fdacb2599841db"
SOURCE_SIZE = 101_609_702
CLASSES = [
    (0, "background", "背景"),
    (1, "road_asphalt", "アスファルト舗装"),
    (2, "road_paved", "舗装道路"),
    (3, "road_unpaved", "未舗装道路"),
    (4, "road_marking", "道路標示"),
    (5, "speed_bump", "減速帯"),
    (6, "cats_eye", "道路鋲（キャッツアイ）"),
    (7, "storm_drain", "雨水ます"),
    (8, "manhole_cover", "マンホール"),
    (9, "road_patch", "舗装補修跡"),
    (10, "water_puddle", "水たまり"),
    (11, "pothole", "道路の穴"),
    (12, "road_crack", "道路のひび割れ"),
]
ATTRIBUTION = (
    "Thiago Rateke, Aldo von Wangenheim, and Rafael Toledo (2023), "
    "Road Traversing Knowledge, Mendeley Data v1, "
    "https://doi.org/10.17632/hssswvmjwf.1, CC BY 4.0."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int, int, int]:
    with path.open("rb") as stream:
        header = stream.read(29)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    width, height, depth, color_type = struct.unpack(">IIBB", header[16:26])
    return width, height, depth, color_type


def safe_extract(source_zip: Path, source_root: Path) -> None:
    if source_zip.stat().st_size != SOURCE_SIZE or sha256(source_zip) != SOURCE_SHA256:
        raise ValueError("source archive size/SHA-256 mismatch")
    source_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("source ZIP CRC failure")
        for item in archive.infolist():
            name = item.filename.replace("\\", "/")
            path = PurePosixPath(name)
            mode = item.external_attr >> 16
            if path.is_absolute() or ".." in path.parts or (mode & 0o170000) == 0o120000:
                raise ValueError(f"unsafe archive path: {name}")
        archive.extractall(source_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("manifest_path", type=Path)
    args = parser.parse_args()
    safe_extract(args.source_zip, args.source_root)
    source = args.source_root / "RTK"
    image_dir, label_dir = source / "image", source / "label"
    train = (source / "trainpaths.txt").read_text(encoding="utf-8").splitlines()
    val = (source / "valpaths.txt").read_text(encoding="utf-8").splitlines()
    train_set, val_set = set(train), set(val)
    if len(train) != 561 or len(val) != 140 or train_set & val_set:
        raise ValueError("official split size or overlap mismatch")
    image_files = {f"image/{p.name}" for p in image_dir.glob("*.png")}
    label_files = {f"image/{p.name}" for p in label_dir.glob("*.png")}
    if image_files != train_set | val_set or label_files != train_set | val_set:
        raise ValueError("source split file set does not match paired images and masks")

    output = args.output_root / DATASET_ID
    if output.exists():
        shutil.rmtree(output)
    for split, names in (("train", train), ("val", val)):
        (output / "images" / split).mkdir(parents=True)
        (output / "masks" / split).mkdir(parents=True)
    rows = []
    for split, names in (("train", train), ("val", val)):
        for relative in names:
            filename = PurePosixPath(relative).name
            image_path = image_dir / filename
            mask_path = label_dir / filename
            image_info, mask_info = png_dimensions(image_path), png_dimensions(mask_path)
            if image_info[:2] != (352, 288) or mask_info[:2] != image_info[:2]:
                raise ValueError(f"image/mask dimensions mismatch: {filename}: {image_info}, {mask_info}")
            image_rel = f"images/{split}/{filename}"
            mask_rel = f"masks/{split}/{filename}"
            shutil.copyfile(image_path, output / image_rel)
            shutil.copyfile(mask_path, output / mask_rel)
            rows.append({
                "image": image_rel,
                "mask": mask_rel,
                "class_name": "__pixel_labels__",
                "class_id": -1,
                "split": split,
            })

    with (output / "labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "mask", "class_name", "class_id", "split"])
        writer.writeheader()
        writer.writerows(rows)
    with (output / "metadata.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    classes = [{"id": i, "name": name, "name_ja": ja} for i, name, ja in CLASSES]
    (output / "classes.json").write_text(json.dumps({"classes": classes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "LICENSE.md").write_text(
        f"""# Data license and attribution

{ATTRIBUTION}

The source dataset is published under the Creative Commons Attribution 4.0 International license (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/.

Changes: directory layout was normalized to paired `images/` and `masks/`, and machine-readable `labels.csv`, `metadata.jsonl`, and `classes.json` were added. Original PNG image and mask files were copied byte for byte. The source train/validation split was preserved.

The CC BY license does not grant rights to third-party content that may be identified in the dataset. The publisher's dataset description says the images were captured in rural areas of Santa Catarina, Brazil.

Do not use predictions from this educational dataset to assess real-world road safety or determine whether a road is safe to use.
""",
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        """# Road Traversing Knowledge (educational artifact)

This artifact contains 701 paired road images and pixel masks from the fixed Mendeley Data v1 release. It has 12 road/environment labels plus background, encoded as integer grayscale values 0–12. Image and mask dimensions are 352×288.

## Layout

- `images/train/`, `images/val/`: RGB PNG road images
- `masks/train/`, `masks/val/`: grayscale PNG masks whose pixel values are class IDs
- `classes.json`: class IDs and Japanese names
- `labels.csv`, `metadata.jsonl`: image-mask pairs and official split

The official split is preserved: 561 train and 140 validation pairs. No test split is supplied. See `LICENSE.md` for attribution, license, changes, and use limits.
""",
        encoding="utf-8",
    )
    internal_manifest = {
        "dataset_id": DATASET_ID,
        "artifact_version": "0.1.0",
        "image_count": len(rows),
        "classes": [name for _, name, _ in CLASSES],
        "class_names_ja": [ja for _, _, ja in CLASSES],
        "mask_encoding": "class_id_grayscale",
        "mask_background_id": 0,
        "splits": {"train": 561, "val": 140, "test": 0},
        "source": {
            "doi": "10.17632/hssswvmjwf.1",
            "version": "1",
            "file_sha256": SOURCE_SHA256,
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(internal_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            files.append({
                "path": path.relative_to(args.output_root).as_posix(),
                "sha256": sha256(path),
                "size": path.stat().st_size,
            })
    manifest = {
        "manifest_version": "1.0.0",
        "dataset_id": DATASET_ID,
        "artifact_version": "0.1.0",
        "image_count": len(rows),
        "split_counts": {"train": 561, "val": 140},
        "label_format": "paired_multiclass_image_mask_csv_and_jsonl",
        "mask_encoding": "class_id_grayscale",
        "mask_background_id": 0,
        "classes": [name for _, name, _ in CLASSES],
        "class_names_ja": [ja for _, _, ja in CLASSES],
        "transform_version": "source_png_preserved; directory_layout_v1; official_train_validation_split",
        "license": "CC BY 4.0",
        "attribution": ATTRIBUTION,
        "source": {
            "url": "https://doi.org/10.17632/hssswvmjwf.1",
            "version": "1",
            "sha256": SOURCE_SHA256,
            "file_id": "2c72e75d-1f50-457a-86f0-a5e3a4174df9",
            "size": SOURCE_SIZE,
        },
        "files": files,
    }
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset_id": DATASET_ID, "image_count": len(rows), "file_count": len(files), "split_counts": manifest["split_counts"], "total_bytes": sum(f["size"] for f in files)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
