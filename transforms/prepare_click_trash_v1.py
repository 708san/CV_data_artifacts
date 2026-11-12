"""Prepare the fixed CLICK Trash v2 single-class object-detection artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from detection_yolo_v1 import prepare as prepare_yolo


DATASET_ID = "click_trash"
VERSION = "0.1.0"
SOURCE_URL = "https://data.mendeley.com/datasets/htcvvz6fm2/2"
SOURCE_VERSION = "Mendeley Data v2; DOI 10.17632/htcvvz6fm2.2"
SOURCE_ARCHIVE_SHA256 = "902fd9665e3ca84222540ed5071d6a6d114ec09e785c2f174509b28fbd2e2d42"
SOURCE_ARCHIVE_SIZE = 5_571_902_652
SOURCE_FILE_ID = "811798c3-3f08-4101-ad81-1d2564c91446"
ATTRIBUTION = (
    "Manjit Baishya (2026), CLICK Trash Dataset, Mendeley Data v2, "
    "https://doi.org/10.17632/htcvvz6fm2.2, CC BY 4.0."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(source_root: Path, source_archive: Path, destination: Path, manifest_path: Path) -> dict:
    if destination.exists() or manifest_path.exists():
        raise FileExistsError("destination and manifest must not exist")
    source_root = source_root.resolve()
    source_archive = source_archive.resolve()
    if source_archive.stat().st_size != SOURCE_ARCHIVE_SIZE or sha256(source_archive) != SOURCE_ARCHIVE_SHA256:
        raise ValueError("source archive size or SHA-256 does not match the pinned Mendeley v2 file")

    labels_root = source_root / "single class" / "labels"
    classes = (source_root / "single class" / "classes.txt").read_text(encoding="utf-8").splitlines()
    if classes != ["trash"]:
        raise ValueError(f"expected the single-class label space, got {classes!r}")
    for split in ("train", "val", "test"):
        image_dir = source_root / "images" / split
        label_dir = labels_root / split
        if not image_dir.is_dir() or not label_dir.is_dir():
            raise ValueError(f"missing source split: {split}")
        image_stems = {path.stem for path in image_dir.glob("*.jpg") if not path.is_symlink()}
        label_stems = {path.stem for path in label_dir.glob("*.txt") if not path.is_symlink()}
        if image_stems != label_stems or any(path.is_symlink() for path in (*image_dir.iterdir(), *label_dir.iterdir())):
            raise ValueError(f"image/label mismatch or symlink in {split}")

    helper = Path(__file__).with_name("click_trash_resize_strip_metadata.swift")
    with tempfile.TemporaryDirectory(prefix="click-trash-prepare-") as temporary:
        work = Path(temporary)
        resized = work / "resized"
        cli_input = work / "input"
        cache = work / "swift-module-cache"
        cache.mkdir()
        subprocess.run(
            ["swift", "-module-cache-path", str(cache), str(helper), str(source_root / "images"), str(resized)],
            check=True,
        )
        for source_split, output_split in (("train", "train"), ("val", "valid"), ("test", "test")):
            images_out = cli_input / output_split / "images"
            labels_out = cli_input / output_split / "labels"
            images_out.mkdir(parents=True)
            labels_out.mkdir(parents=True)
            for source in (resized / source_split).glob("*.jpg"):
                shutil.copyfile(source, images_out / source.name)
            for source in (labels_root / source_split).glob("*.txt"):
                shutil.copyfile(source, labels_out / source.name)
        (cli_input / "classes.json").write_text('{"classes":["trash"]}\n', encoding="utf-8")
        manifest = prepare_yolo(
            cli_input,
            destination,
            dataset_id=DATASET_ID,
            artifact_version=VERSION,
            source_url=SOURCE_URL,
            source_version=SOURCE_VERSION,
            source_sha256=SOURCE_ARCHIVE_SHA256,
            license_name="CC BY 4.0",
            attribution=ATTRIBUTION,
        )

    manifest.update({
        "transform_version": "click_trash_v0.1.0; resize max-side 1024; JPEG quality 0.88; strip source EXIF/GPS; preserve normalized boxes",
        "split_counts": {"train": 901, "valid": 113, "test": 112},
        "source": {
            **manifest["source"],
            "file_id": SOURCE_FILE_ID,
            "size": SOURCE_ARCHIVE_SIZE,
        },
    })
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="the safely extracted, hash-verified Mendeley v2 archive")
    parser.add_argument("source_archive", type=Path, help="the original archive, checked against its pinned SHA-256")
    parser.add_argument("destination", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = prepare(args.source_root, args.source_archive, args.destination, args.manifest)
    print(json.dumps({"dataset_id": DATASET_ID, "image_count": result["image_count"], "split_counts": result["split_counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
