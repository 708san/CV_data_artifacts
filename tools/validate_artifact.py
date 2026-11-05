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
    labels = extracted_root / dataset_id / "labels.csv"
    with labels.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != manifest.get("image_count"):
        raise ArtifactValidationError("image_count does not match labels.csv")
    image_names = [row.get("image") for row in rows]
    if any(not isinstance(name, str) for name in image_names) or len(set(image_names)) != len(image_names):
        raise ArtifactValidationError("labels.csv contains duplicate or missing image paths")
    expected_image_names = {path[len(prefix):] for path in image_paths}
    if set(image_names) != expected_image_names:
        raise ArtifactValidationError("labels.csv does not match image files")
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
