"""クラス別Images/Mask構造を領域分割の共通形式へ変換する。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
TRANSFORM_VERSION = "segmentation_v1.0.0"


class TransformError(RuntimeError):
    """入力が共通形式へ変換できない場合。"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_filename(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value or "\\" in value or path.is_absolute()
        or len(path.parts) != 1 or path.parts[0] in {"", ".", ".."}
        or path.suffix.lower() not in IMAGE_EXTENSIONS
    ):
        raise TransformError(f"unsafe image filename: {value}")
    return path


def _source_pairs(source_root: Path) -> list[tuple[str, Path, Path]]:
    pairs: list[tuple[str, Path, Path]] = []
    for class_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        images_dir = class_dir / "Images"
        masks_dir = class_dir / "Mask"
        if not images_dir.is_dir() or not masks_dir.is_dir():
            raise TransformError(f"Images/Mask directory is missing: {class_dir.name}")
        image_paths = sorted(path for path in images_dir.iterdir() if path.is_file())
        for image_path in image_paths:
            relative = _safe_filename(image_path.name)
            expected_mask = masks_dir / f"{relative.stem}_mask.png"
            if image_path.is_symlink() or expected_mask.is_symlink():
                raise TransformError(f"symlink is not allowed: {class_dir.name}/{relative.name}")
            if not expected_mask.is_file():
                raise TransformError(f"mask is missing: {class_dir.name}/{relative.name}")
            pairs.append((class_dir.name, image_path, expected_mask))
        mask_names = {path.name for path in masks_dir.iterdir() if path.is_file()}
        expected_names = {f"{path.stem}_mask.png" for path in image_paths}
        if mask_names != expected_names:
            raise TransformError(f"image/mask file set mismatch: {class_dir.name}")
    if not pairs:
        raise TransformError("no image/mask pairs found")
    return pairs


def prepare(
    source_root: Path,
    destination_root: Path,
    *,
    dataset_id: str,
    artifact_version: str,
    source_url: str,
    source_version: str,
    source_sha256: str,
    license_name: str,
    attribution: str,
    split: str = "unsplit",
) -> dict[str, Any]:
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if destination_root.exists():
        raise TransformError(f"destination already exists: {destination_root}")
    if not source_url.startswith("https://") or len(source_sha256) != 64:
        raise TransformError("pinned https source URL and SHA-256 are required")
    pairs = _source_pairs(source_root)
    classes = sorted({label for label, _, _ in pairs})
    rows: list[dict[str, str]] = []
    metadata: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for label, image_path, mask_path in pairs:
        image_name = _safe_filename(image_path.name).name
        mask_name = _safe_filename(mask_path.name).name
        image_rel = PurePosixPath("images", split, label, image_name)
        mask_rel = PurePosixPath("masks", split, label, mask_name)
        if image_rel.as_posix() in seen:
            raise TransformError(f"duplicate image path: {image_rel}")
        seen.add(image_rel.as_posix())
        image_target = destination_root.joinpath(*image_rel.parts)
        mask_target = destination_root.joinpath(*mask_rel.parts)
        image_target.parent.mkdir(parents=True, exist_ok=True)
        mask_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image_path, image_target)
        shutil.copyfile(mask_path, mask_target)
        sample_id = image_rel.with_suffix("").as_posix()
        rows.append({"image": image_rel.as_posix(), "mask": mask_rel.as_posix(), "label": label, "split": split, "sample_id": sample_id})
        metadata.append({"file_name": image_rel.as_posix(), "mask_file": mask_rel.as_posix(), "label": label, "split": split, "sample_id": sample_id})
        for rel, target in ((image_rel, image_target), (mask_rel, mask_target)):
            files.append({"path": f"{dataset_id}/{rel.as_posix()}", "sha256": _sha256(target), "size": target.stat().st_size})

    dataset_manifest = {
        "case_id": dataset_id, "version": f"v{artifact_version}", "task": "image_segmentation",
        "image_count": len(rows), "classes": classes, "format": "paired_image_mask",
        "classes_file": "classes.json", "labels": "labels.csv", "metadata": "metadata.jsonl",
        "source": {"url": source_url, "version": source_version, "sha256": source_sha256},
        "license": {"name": license_name}, "attribution": attribution,
        "transform_version": TRANSFORM_VERSION,
    }
    (destination_root / "labels.csv").write_text(
        "image,mask,label,split,sample_id\n" + "".join(
            f'{row["image"]},{row["mask"]},{row["label"]},{row["split"]},{row["sample_id"]}\n' for row in rows
        ), encoding="utf-8"
    )
    (destination_root / "metadata.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metadata), encoding="utf-8"
    )
    (destination_root / "classes.json").write_text(
        json.dumps({"classes": classes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination_root / "manifest.json").write_text(json.dumps(dataset_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination_root / "README.md").write_text("CV_data common segmentation format. See manifest.json for source and license.\n", encoding="utf-8")
    for name in ("manifest.json", "classes.json", "labels.csv", "metadata.jsonl", "README.md"):
        target = destination_root / name
        files.insert(0, {"path": f"{dataset_id}/{name}", "sha256": _sha256(target), "size": target.stat().st_size})
    return {
        "manifest_version": "1.0.0", "dataset_id": dataset_id, "artifact_version": artifact_version,
        "files": files, "image_count": len(rows), "label_format": "paired_image_mask_csv_and_jsonl",
        "transform_version": TRANSFORM_VERSION, "license": license_name, "attribution": attribution,
        "source": {"url": source_url, "version": source_version, "sha256": source_sha256},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--artifact-version", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--license", required=True, dest="license_name")
    parser.add_argument("--attribution", required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.source_root, args.destination_root, dataset_id=args.dataset_id, artifact_version=args.artifact_version,
                       source_url=args.source_url, source_version=args.source_version, source_sha256=args.source_sha256,
                       license_name=args.license_name, attribution=args.attribution)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset_id": args.dataset_id, "image_count": manifest["image_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
