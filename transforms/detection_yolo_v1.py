"""YOLO画像/ラベル構造を物体検出の共通形式へ変換する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
TRANSFORM_VERSION = "detection_yolo_v1.0.0"


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
    if not value or "\\" in value or path.is_absolute() or len(path.parts) != 1 or path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise TransformError(f"unsafe image filename: {value}")
    return path


def _read_classes(source_root: Path) -> list[str]:
    path = source_root / "classes.json"
    if not path.is_file():
        raise TransformError("input classes.json is required")
    data = json.loads(path.read_text(encoding="utf-8"))
    classes = data.get("classes") if isinstance(data, dict) else data
    if not isinstance(classes, list) or not classes or any(not isinstance(x, str) or not x for x in classes):
        raise TransformError("classes.json must contain a non-empty string list")
    if len(set(classes)) != len(classes):
        raise TransformError("classes.json contains duplicate class names")
    return classes


def _annotation_rows(label_path: Path, class_count: int) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        columns = line.split()
        if len(columns) != 5:
            raise TransformError(f"YOLO label must have 5 columns: {label_path}:{line_number}")
        try:
            class_id = int(columns[0])
            values = [float(value) for value in columns[1:]]
        except ValueError as exc:
            raise TransformError(f"YOLO label contains a non-number: {label_path}:{line_number}") from exc
        if not 0 <= class_id < class_count or any(not 0 <= value <= 1 for value in values):
            raise TransformError(f"YOLO label is out of range: {label_path}:{line_number}")
        rows.append({"class_id": class_id, "x_center": values[0], "y_center": values[1], "width": values[2], "height": values[3]})
    return rows


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
) -> dict[str, Any]:
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if destination_root.exists():
        raise TransformError(f"destination already exists: {destination_root}")
    if not source_url.startswith("https://") or len(source_sha256) != 64:
        raise TransformError("pinned https source URL and SHA-256 are required")
    classes = _read_classes(source_root)
    rows: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for split_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        images_dir, labels_dir = split_dir / "images", split_dir / "labels"
        if not images_dir.is_dir() or not labels_dir.is_dir():
            continue
        split = split_dir.name
        image_paths = sorted(path for path in images_dir.iterdir() if path.is_file())
        image_names = {_safe_filename(path.name).stem: path for path in image_paths}
        label_paths = sorted(path for path in labels_dir.iterdir() if path.is_file())
        label_names = {path.stem: path for path in label_paths if path.suffix.lower() == ".txt"}
        if set(image_names) != set(label_names):
            raise TransformError(f"image/label file set mismatch in split: {split}")
        for stem, image_path in image_names.items():
            image_name = _safe_filename(image_path.name).name
            label_path = label_names[stem]
            annotations = _annotation_rows(label_path, len(classes))
            image_rel = PurePosixPath("images", split, image_name)
            label_rel = PurePosixPath("labels", split, f"{stem}.txt")
            image_target = destination_root.joinpath(*image_rel.parts)
            label_target = destination_root.joinpath(*label_rel.parts)
            image_target.parent.mkdir(parents=True, exist_ok=True)
            label_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image_path, image_target)
            shutil.copyfile(label_path, label_target)
            rows.append({"file_name": image_rel.as_posix(), "label_file": label_rel.as_posix(), "split": split, "annotations": annotations})
            for rel, target in ((image_rel, image_target), (label_rel, label_target)):
                files.append({"path": f"{dataset_id}/{rel.as_posix()}", "sha256": _sha256(target), "size": target.stat().st_size})
    if not rows:
        raise TransformError("no detection image/label pairs found")

    manifest = {
        "case_id": dataset_id, "version": f"v{artifact_version}", "task": "object_detection",
        "image_count": len(rows), "classes": classes, "format": "yolo_normalized",
        "classes_file": "classes.json", "annotations": "annotations.jsonl", "metadata": "metadata.jsonl",
        "source": {"url": source_url, "version": source_version, "sha256": source_sha256},
        "license": {"name": license_name}, "attribution": attribution, "transform_version": TRANSFORM_VERSION,
    }
    (destination_root / "classes.json").write_text(json.dumps({"classes": classes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination_root / "annotations.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    (destination_root / "metadata.jsonl").write_text(
        "".join(json.dumps({"file_name": row["file_name"], "label_file": row["label_file"], "split": row["split"], "annotation_count": len(row["annotations"])}, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    (destination_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination_root / "README.md").write_text("CV_data common object-detection format. See manifest.json for source and license.\n", encoding="utf-8")
    for name in ("manifest.json", "classes.json", "annotations.jsonl", "metadata.jsonl", "README.md"):
        target = destination_root / name
        files.insert(0, {"path": f"{dataset_id}/{name}", "sha256": _sha256(target), "size": target.stat().st_size})
    return {
        "manifest_version": "1.0.0", "dataset_id": dataset_id, "artifact_version": artifact_version,
        "files": files, "image_count": len(rows), "label_format": "yolo_normalized_jsonl",
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
