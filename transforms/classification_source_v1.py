"""Prepare class-folder images with deterministic stratified train/val/test splits."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

TRANSFORM_VERSION = "classification_source_v1.0.0"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pgm", ".jpg_"}


class SourcePreparationError(ValueError):
    """Invalid class-folder source data."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_counts(count: int) -> tuple[int, int, int]:
    if count < 3:
        raise SourcePreparationError("each class needs at least three unique images")
    train = min(max(round(count * 0.70), 1), count - 2)
    val = min(max(round(count * 0.15), 1), count - train - 1)
    return train, val, count - train - val


def prepare(source_root: Path, destination_root: Path, *, seed: int = 42) -> dict[str, Any]:
    """Copy immediate class-folder images into a stable 70/15/15 stratified split.

    Exact duplicate images within a class are excluded after the first sorted
    source path. Identical bytes in different classes are rejected.
    """
    source_root = Path(source_root)
    if source_root.is_symlink() or not source_root.is_dir():
        raise SourcePreparationError("source_root must be a real directory")
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if destination_root.exists():
        raise SourcePreparationError(f"destination already exists: {destination_root}")

    folders = sorted(p for p in source_root.iterdir() if p.is_dir() and not p.is_symlink())
    if not folders:
        raise SourcePreparationError("source has no class folders")
    folder_labels = {folder.name: " ".join(folder.name.split()) for folder in folders}
    if len(set(folder_labels.values())) != len(folder_labels):
        raise SourcePreparationError("class folder names collide after whitespace normalization")
    classes = sorted(folder_labels.values())
    grouped: dict[str, list[Path]] = {}
    for folder in folders:
        label = folder_labels[folder.name]
        paths = sorted(folder.rglob("*"))
        if any(path.is_symlink() for path in paths):
            raise SourcePreparationError(f"symlink found under class {label}")
        files = [path for path in paths if path.is_file()]
        if not files:
            raise SourcePreparationError(f"class has no files: {label}")
        for path in files:
            relative = path.relative_to(source_root)
            if PurePosixPath(relative.as_posix()).is_absolute() or ".." in relative.parts:
                raise SourcePreparationError(f"unsafe path: {relative}")
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise SourcePreparationError(f"unsupported extension: {relative}")
        grouped[label] = files

    by_digest: dict[str, tuple[str, Path]] = {}
    unique: dict[str, list[Path]] = defaultdict(list)
    exclusions: list[dict[str, str]] = []
    for label in classes:
        for path in grouped[label]:
            digest = _sha256(path)
            prior = by_digest.get(digest)
            if prior:
                prior_label, prior_path = prior
                if prior_label != label:
                    raise SourcePreparationError(
                        f"identical image has conflicting classes: {prior_path} and {path}"
                    )
                exclusions.append({
                    "path": path.relative_to(source_root).as_posix(),
                    "duplicate_of": prior_path.relative_to(source_root).as_posix(),
                    "sha256": digest,
                })
                continue
            by_digest[digest] = (label, path)
            unique[label].append(path)

    destination_root.mkdir(parents=True)
    rows: list[dict[str, str]] = []
    class_report: dict[str, Any] = {}
    output_paths: set[str] = set()
    for class_index, label in enumerate(classes):
        paths = sorted(unique[label], key=lambda p: p.relative_to(source_root).as_posix())
        n_train, n_val, n_test = _split_counts(len(paths))
        shuffled = list(paths)
        random.Random(seed + class_index).shuffle(shuffled)
        split_paths = (
            [("train", p) for p in shuffled[:n_train]]
            + [("val", p) for p in shuffled[n_train:n_train + n_val]]
            + [("test", p) for p in shuffled[n_train + n_val:]]
        )
        split_counts = Counter()
        for split, source_path in split_paths:
            filename = source_path.name[:-1] if source_path.suffix.lower() == ".jpg_" else source_path.name
            relative = PurePosixPath("images", split, label, filename)
            relative_text = relative.as_posix()
            if relative_text in output_paths:
                raise SourcePreparationError(f"output filename collision: {relative_text}")
            output_paths.add(relative_text)
            target = destination_root.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target)
            rows.append({"image": relative_text, "label": label, "split": split})
            split_counts[split] += 1
        class_report[label] = {
            "source_images": len(grouped[label]),
            "unique_images": len(paths),
            "excluded_exact_duplicates": len(grouped[label]) - len(paths),
            "splits": {name: split_counts[name] for name in ("train", "val", "test")},
        }

    with (destination_root / "labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("image", "label", "split"))
        writer.writeheader()
        writer.writerows(rows)
    source_manifest = {
        "transform_version": TRANSFORM_VERSION,
        "image_count": len(rows),
        "classes": classes,
        "split_seed": seed,
        "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
    }
    (destination_root / "manifest.json").write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = {
        **source_manifest,
        "class_counts": class_report,
        "source_class_folders": {label: folder for folder, label in folder_labels.items()},
        "excluded_exact_duplicates": exclusions,
        "renamed_extensions": [{
            "from": ".jpg_",
            "to": ".jpg",
            "count": sum(path.suffix.lower() == ".jpg_" for paths in grouped.values() for path in paths),
        }],
    }
    (destination_root / "source-preparation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    report = prepare(args.source_root, args.destination_root, seed=args.seed)
    print(json.dumps({
        "image_count": report["image_count"],
        "classes": len(report["classes"]),
        "duplicates_excluded": len(report["excluded_exact_duplicates"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
