"""artifact manifestと展開済み共通形式を標準ライブラリだけで照合する。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


class ArtifactValidationError(ValueError):
    """artifactがmanifestに適合しない場合。"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ArtifactValidationError(f"unsafe artifact path: {value}")
    return path


def validate(manifest_path: Path, extracted_root: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ArtifactValidationError("manifest.files must be a non-empty list")
    expected: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ArtifactValidationError("manifest.files contains a non-object")
        path_text = item.get("path")
        if not isinstance(path_text, str) or path_text in expected:
            raise ArtifactValidationError(f"invalid or duplicate manifest path: {path_text}")
        path = _safe_path(path_text)
        expected.add(path.as_posix())
        target = extracted_root.joinpath(*path.parts)
        if target.is_symlink() or not target.is_file():
            raise ArtifactValidationError(f"missing or symlink file: {path_text}")
        if target.stat().st_size != item.get("size"):
            raise ArtifactValidationError(f"size mismatch: {path_text}")
        if _sha256(target) != item.get("sha256"):
            raise ArtifactValidationError(f"SHA-256 mismatch: {path_text}")

    actual = {
        path.relative_to(extracted_root).as_posix()
        for path in extracted_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if actual != expected:
        raise ArtifactValidationError(f"manifest/file set mismatch: expected {len(expected)}, found {len(actual)}")

    dataset_id = manifest.get("dataset_id")
    prefix = f"{dataset_id}/"
    image_paths = [path for path in expected if path.startswith(prefix + "images/")]
    if len(image_paths) != manifest.get("image_count"):
        raise ArtifactValidationError("image_count does not match manifest files")
    label_format = manifest.get("label_format")
    expected_image_names = {path[len(prefix):] for path in image_paths}
    dataset_root = extracted_root / dataset_id
    if label_format == "classification_csv_and_jsonl":
        labels = dataset_root / "labels.csv"
        with labels.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        image_names = [row.get("image") for row in rows]
        if len(rows) != manifest.get("image_count") or any(not isinstance(name, str) for name in image_names) or len(set(image_names)) != len(image_names):
            raise ArtifactValidationError("labels.csv does not match image_count or contains duplicate paths")
        if set(image_names) != expected_image_names:
            raise ArtifactValidationError("labels.csv does not match image files")
    elif label_format in {
        "paired_image_mask_csv_and_jsonl",
        "paired_multiclass_image_mask_csv_and_jsonl",
    }:
        labels = dataset_root / "labels.csv"
        with labels.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        image_names = [row.get("image") for row in rows]
        mask_names = [row.get("mask") for row in rows]
        if len(rows) != manifest.get("image_count") or len(set(image_names)) != len(image_names) or len(set(mask_names)) != len(mask_names):
            raise ArtifactValidationError("segmentation labels do not match image_count or contain duplicates")
        if set(image_names) != expected_image_names or not all(isinstance(name, str) and name.startswith("masks/") for name in mask_names):
            raise ArtifactValidationError("segmentation labels do not match image/mask files")
        if not all(f"{dataset_id}/{name}" in expected for name in mask_names):
            raise ArtifactValidationError("segmentation mask file is missing from manifest")
        if label_format == "paired_multiclass_image_mask_csv_and_jsonl":
            classes_file = dataset_root / "classes.json"
            classes_data = json.loads(classes_file.read_text(encoding="utf-8"))
            classes = classes_data.get("classes") if isinstance(classes_data, dict) else None
            if (not isinstance(classes, list) or not classes
                    or not all(isinstance(item, dict) for item in classes)
                    or [item.get("id") for item in classes] != list(range(len(classes)))
                    or any(not isinstance(item.get("name"), str) for item in classes)):
                raise ArtifactValidationError("multiclass segmentation class IDs must be contiguous from zero")
    elif label_format == "yolo_normalized_jsonl":
        annotations = dataset_root / "annotations.jsonl"
        records = [json.loads(line) for line in annotations.read_text(encoding="utf-8").splitlines() if line.strip()]
        names = [record.get("file_name") for record in records]
        if len(records) != manifest.get("image_count") or len(set(names)) != len(names) or set(names) != expected_image_names:
            raise ArtifactValidationError("detection annotations do not match image files")
    else:
        raise ArtifactValidationError(f"unsupported label_format: {label_format}")
    return {
        "dataset_id": dataset_id,
        "artifact_version": manifest.get("artifact_version"),
        "image_count": len(image_paths),
        "file_count": len(expected),
        "status": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("extracted_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.manifest, args.extracted_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
