"""Prepare the pinned Mendeley obstacle dataset as a common detection artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from detection_yolo_v1 import prepare as prepare_yolo


DATASET_ID = "obstacles_assistance"
VERSION = "0.1.0"
SOURCE_PAGE = "https://data.mendeley.com/datasets/xwhnp82rhk/1"
SOURCE_ARCHIVE_URL = "https://data.mendeley.com/public-api/zip/xwhnp82rhk/download/1"
SOURCE_VERSION = "Mendeley Data v1; DOI 10.17632/xwhnp82rhk.1"
SOURCE_SHA256 = "cc68e314ef6e8aaab3a7b37fe7897528ec7850ca06f0761206dcd4ddf202515a"
SOURCE_SIZE = 84_945_675
ATTRIBUTION = (
    "Yi Xian Wang (2025), Obstacles Avoidance Assistance for Visually Impaired, "
    "Mendeley Data v1, https://doi.org/10.17632/xwhnp82rhk.1, CC BY 4.0."
)
CLASSES = ["bump", "fence", "hole", "pole"]
CLASS_NAMES_JA = ["段差", "柵", "穴", "ポール"]
SPLIT_COUNTS = {"train": 1000, "valid": 250}
BOX_COUNTS = {"train": 1306, "valid": 321}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_verified(archive: Path, destination: Path) -> Path:
    if archive.stat().st_size != SOURCE_SIZE or sha256(archive) != SOURCE_SHA256:
        raise ValueError("source archive size or SHA-256 does not match pinned Mendeley v1")
    with zipfile.ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) != 2501 or sum(item.file_size for item in entries) > 100_000_000:
            raise ValueError("unexpected archive entry count or uncompressed size")
        seen = set()
        for item in entries:
            name = item.filename
            path = PurePosixPath(name)
            mode = (item.external_attr >> 16) & 0xFFFF
            if ("\\" in name or path.is_absolute() or ".." in path.parts
                    or any(part in {"", "."} for part in path.parts)
                    or stat.S_ISLNK(mode) or name in seen):
                raise ValueError(f"unsafe or duplicate ZIP member: {name!r}")
            seen.add(name)
        if zf.testzip() is not None:
            raise ValueError("source ZIP CRC check failed")
        zf.extractall(destination)
    roots = [p for p in destination.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise ValueError(f"expected one source root, found {len(roots)}")
    source_root = roots[0]
    classes_line = next((line.partition(":")[2].strip() for line in (source_root / "data.yaml").read_text(encoding="utf-8").splitlines() if line.startswith("names:")), "")
    if classes_line != "['bump', 'fence', 'hole', 'pole']":
        raise ValueError(f"unexpected class names: {classes_line}")
    return source_root


def prepare(archive: Path, destination: Path, manifest_path: Path) -> dict:
    if destination.exists() or manifest_path.exists():
        raise FileExistsError("destination and manifest must not exist")
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with tempfile.TemporaryDirectory(prefix="obstacles-assistance-prepare-") as temp:
        extracted = Path(temp) / "source"
        extracted.mkdir()
        source_root = extract_verified(archive, extracted)
        result = prepare_yolo(
            source_root,
            destination,
            dataset_id=DATASET_ID,
            artifact_version=VERSION,
            source_url=SOURCE_PAGE,
            source_version=SOURCE_VERSION,
            source_sha256=SOURCE_SHA256,
            license_name="CC BY 4.0",
            attribution=ATTRIBUTION,
        )
    if result["image_count"] != sum(SPLIT_COUNTS.values()):
        raise ValueError("unexpected image count")
    for split, expected in BOX_COUNTS.items():
        actual = sum(1 for row in (destination / "annotations.jsonl").read_text(encoding="utf-8").splitlines()
                     if json.loads(row)["split"] == split for _ in json.loads(row)["annotations"])
        if actual != expected:
            raise ValueError(f"unexpected {split} annotation count: {actual}")
    shutil.copyfile(Path(__file__).resolve().parents[1] / "datasets" / DATASET_ID / "README.md", destination / "README.md")
    shutil.copyfile(Path(__file__).resolve().parents[1] / "datasets" / DATASET_ID / "LICENSE.md", destination / "LICENSE.md")
    inner = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    inner.update({
        "class_names_ja": CLASS_NAMES_JA,
        "split_counts": SPLIT_COUNTS,
        "annotation_counts_by_split": BOX_COUNTS,
        "source": {**inner["source"], "size": SOURCE_SIZE, "download_url": SOURCE_ARCHIVE_URL},
        "preprocessing": {
            "image_pixels": "preserved byte-for-byte",
            "bbox_coordinates": "preserved normalized YOLO xywh values",
            "source_splits": "train and valid retained; no test split exists in the source",
            "license_provenance": "Mendeley page declares CC BY 4.0; the page does not itemize upstream Roboflow source IDs/licenses",
        },
    })
    (destination / "manifest.json").write_text(json.dumps(inner, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for path in sorted(destination.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink in artifact: {path}")
        if path.is_file():
            files.append({"path": f"{DATASET_ID}/{path.relative_to(destination).as_posix()}",
                          "sha256": sha256(path), "size": path.stat().st_size})
    manifest = {
        "manifest_version": "1.0.0", "dataset_id": DATASET_ID, "artifact_version": VERSION,
        "files": files, "image_count": sum(SPLIT_COUNTS.values()), "split_counts": SPLIT_COUNTS,
        "annotation_counts_by_split": BOX_COUNTS, "classes": CLASSES, "class_names_ja": CLASS_NAMES_JA,
        "label_format": "yolo_normalized_jsonl", "transform_version": "obstacles_assistance_v1.0.0 + detection_yolo_v1.1.0",
        "license": "CC BY 4.0", "attribution": ATTRIBUTION,
        "source": {"url": SOURCE_PAGE, "download_url": SOURCE_ARCHIVE_URL, "version": SOURCE_VERSION,
                   "size": SOURCE_SIZE, "sha256": SOURCE_SHA256},
        "preprocessing": inner["preprocessing"],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_archive", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = prepare(args.source_archive, args.destination, args.manifest)
    print(json.dumps({"dataset_id": DATASET_ID, "image_count": result["image_count"],
                      "split_counts": result["split_counts"], "annotation_counts_by_split": result["annotation_counts_by_split"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
