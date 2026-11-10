"""Create a compact, privacy-clean classification artifact from the pinned source ZIP."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import stat
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, ImageOps

DATASET_ID = "indoor_plant_varieties"
ARTIFACT_VERSION = "0.1.0"
TRANSFORM_VERSION = "indoor_plant_varieties_v1.0.0"
SOURCE_URL = "https://data.mendeley.com/datasets/ct79299k27/1"
SOURCE_SHA256 = "c6e3839666e344ca4bb72fa9b09f36605fe8f972c088f0bba72c5dbe06bde2df"
SOURCE_SIZE = 765_167_460
SOURCE_FILE_ID = "be73f0a3-d478-4df1-b9d5-513e5879a8ef"
SOURCE_DOWNLOAD_URL = (
    "https://data.mendeley.com/public-files/datasets/ct79299k27/files/"
    f"{SOURCE_FILE_ID}/file_downloaded"
)
LICENSE = "CC BY 4.0"
ATTRIBUTION = (
    "Mamun, Sajib Bin; Nirob, Md Asraful Sharker; Ahad, Md Taimur; Akter, Mashreka; "
    "Saha, Pranta; Assaduzzaman, Md (2024), Indoor Plant Varieties for Computer Vision "
    "Applications: A Diverse Image Dataset, Mendeley Data v1, "
    "https://doi.org/10.17632/ct79299k27.1."
)
MAX_SIDE = 512
CLASS_MAP = {
    "Aglaonema": "Aglaonema",
    "Cryptanthus": "Cryptanthus",
    "Devil_s Ivy": "Devil's Ivy",
    "Heartleaf philodendron": "Heartleaf philodendron",
    "N-Joy Pothos": "N-Joy Pothos",
    "Rhaphidophora": "Rhaphidophora",
    "Zz plant": "Zz plant",
}


class PreparationError(ValueError):
    """The pinned archive does not match the audited source or cannot be prepared safely."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_counts(count: int) -> tuple[int, int, int]:
    if count < 3:
        raise PreparationError("every class must contain at least three unique images")
    train = min(max(round(count * 0.70), 1), count - 2)
    val = min(max(round(count * 0.15), 1), count - train - 1)
    return train, val, count - train - val


def _safe_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    seen: set[str] = set()
    for entry in entries:
        name = entry.filename
        path = PurePosixPath(name)
        mode = entry.external_attr >> 16
        is_directory = name.endswith("/")
        if (
            not name or "\\" in name or "\x00" in name or path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
            or stat.S_ISLNK(mode) or name in seen
        ):
            raise PreparationError(f"unsafe or duplicate ZIP member: {name}")
        seen.add(name)
        if not is_directory and (len(path.parts) != 3 or path.parts[0] != "Orginal Data"):
            raise PreparationError(f"unexpected source path: {name}")
        if not is_directory and path.suffix.lower() not in {".jpg", ".jpeg"}:
            raise PreparationError(f"unexpected source file type: {name}")
    return entries


def prepare(
    source_zip: Path,
    destination: Path,
    *,
    seed: int = 42,
    expected_size: int = SOURCE_SIZE,
    expected_sha256: str = SOURCE_SHA256,
) -> dict[str, Any]:
    source_zip = Path(source_zip)
    destination = Path(destination)
    if source_zip.is_symlink() or not source_zip.is_file():
        raise PreparationError("source ZIP must be a regular file")
    if source_zip.stat().st_size != expected_size or sha256_file(source_zip) != expected_sha256:
        raise PreparationError("source ZIP size or SHA-256 does not match Mendeley Data v1")
    if destination.exists():
        raise PreparationError(f"destination already exists: {destination}")

    destination.mkdir(parents=True)
    class_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_inventory: list[dict[str, Any]] = []
    excluded_duplicates: list[dict[str, str]] = []
    digest_to_source: dict[str, tuple[str, str]] = {}
    gps_count = 0
    input_dimensions: Counter[str] = Counter()
    image_count = 0

    with zipfile.ZipFile(source_zip) as archive:
        entries = _safe_entries(archive)
        failed = archive.testzip()
        if failed:
            raise PreparationError(f"ZIP CRC failed: {failed}")
        for entry in entries:
            if entry.is_dir():
                continue
            source_name = entry.filename
            parts = PurePosixPath(source_name).parts
            source_class = parts[1]
            if source_class not in CLASS_MAP:
                raise PreparationError(f"unknown class folder: {source_class}")
            raw = archive.read(entry)
            source_digest = sha256_bytes(raw)
            canonical_class = CLASS_MAP[source_class]
            source_inventory.append({
                "path": source_name,
                "file_id": SOURCE_FILE_ID,
                "filename": PurePosixPath(source_name).name,
                "size": len(raw),
                "sha256": source_digest,
                "download_url": SOURCE_DOWNLOAD_URL,
            })
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    image.load()
                    input_dimensions[f"{image.width}x{image.height}"] += 1
                    if image.getexif().get(34853) is not None:
                        gps_count += 1
                    prior = digest_to_source.get(source_digest)
                    if prior:
                        prior_class, prior_path = prior
                        if prior_class != canonical_class:
                            raise PreparationError(
                                f"duplicate image has conflicting classes: {prior_path} / {source_name}"
                            )
                        excluded_duplicates.append({
                            "path": source_name, "duplicate_of": prior_path, "sha256": source_digest,
                        })
                        continue
                    digest_to_source[source_digest] = (canonical_class, source_name)
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=86, optimize=True, exif=b"")
                    encoded = buffer.getvalue()
            except Exception as exc:
                raise PreparationError(f"image decode failed: {source_name}: {type(exc).__name__}") from exc
            class_records[canonical_class].append({
                "source_path": source_name,
                "source_sha256": source_digest,
                "source_size": len(raw),
                "width": image.width,
                "height": image.height,
                "encoded": encoded,
            })
            image_count += 1

    classes = sorted(class_records)
    if set(classes) != set(CLASS_MAP.values()):
        raise PreparationError("source classes differ from the audited seven classes")
    output_rows: list[dict[str, Any]] = []
    split_totals: Counter[str] = Counter()
    class_report: dict[str, Any] = {}
    output_files: list[dict[str, Any]] = []
    for class_index, label in enumerate(classes):
        records = sorted(class_records[label], key=lambda item: item["source_path"])
        n_train, n_val, n_test = split_counts(len(records))
        random.Random(seed + class_index).shuffle(records)
        split_values = (
            [("train", item) for item in records[:n_train]]
            + [("val", item) for item in records[n_train:n_train + n_val]]
            + [("test", item) for item in records[n_train + n_val:]]
        )
        per_split: Counter[str] = Counter()
        for split, item in split_values:
            filename = PurePosixPath(item["source_path"]).name
            relative = PurePosixPath("images", split, label, filename).with_suffix(".jpg").as_posix()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise PreparationError(f"output path collision: {relative}")
            target.write_bytes(item["encoded"])
            output_rows.append({
                "image": relative, "label": label, "label_id": classes.index(label),
                "split": split, "sample_id": PurePosixPath(relative).with_suffix("").as_posix(),
            })
            split_totals[split] += 1
            per_split[split] += 1
            output_files.append({"path": f"{DATASET_ID}/{relative}", "sha256": sha256_file(target), "size": target.stat().st_size})
        class_report[label] = {
            "source_images": sum(1 for row in source_inventory if PurePosixPath(row["path"]).parts[1] == next(k for k, v in CLASS_MAP.items() if v == label)),
            "unique_images": len(records),
            "excluded_exact_duplicates": sum(1 for row in excluded_duplicates if row["path"].split("/")[1] == next(k for k, v in CLASS_MAP.items() if v == label)),
            "splits": {key: per_split[key] for key in ("train", "val", "test")},
        }

    attribution = ATTRIBUTION
    readme = (
        "# Indoor Plant Varieties v0.1.0\n\n"
        "共通形式の画像分類データです。元データから完全一致重複10枚を除き、"
        "長辺512pxに縮小し、EXIF/GPS等の画像メタデータを外しました。"
        "元画像の画素を除く派生処理を行っています。クラス内でseed 42により"
        "train/val/testへ70/15/15に分割しました。\n\n"
        f"出典：{attribution}\n\n"
        "ライセンス：CC BY 4.0。作者・出典・変更内容を表示してください。"
        "植物名の予測は有毒性、食用、ペットや人の安全、育て方を判断する用途には使えません。\n"
    )
    license_text = (
        "# License and attribution\n\n"
        "Source dataset: Indoor Plant Varieties for Computer Vision Applications: A Diverse Image Dataset, Mendeley Data v1.\n\n"
        f"{attribution}\n\n"
        "The source dataset is marked CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.\n\n"
        "Changes: exact duplicate images removed; images resized to a 512-pixel maximum side; EXIF and GPS metadata removed; deterministic train/validation/test splits added.\n"
    )
    with (destination / "labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("image", "label", "label_id", "split", "sample_id"))
        writer.writeheader()
        writer.writerows(output_rows)
    (destination / "metadata.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8"
    )
    (destination / "README.md").write_text(readme, encoding="utf-8")
    (destination / "LICENSE.md").write_text(license_text, encoding="utf-8")
    internal_manifest = {
        "case_id": DATASET_ID, "version": f"v{ARTIFACT_VERSION}", "task": "image_classification",
        "image_count": len(output_rows), "classes": classes, "format": "imagefolder",
        "labels": "labels.csv", "metadata": "metadata.jsonl", "source": {
            "url": SOURCE_URL, "version": "1", "sha256": SOURCE_SHA256,
        }, "license": {"name": LICENSE}, "attribution": attribution,
        "transform_version": TRANSFORM_VERSION,
    }
    (destination / "manifest.json").write_text(json.dumps(internal_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for filename in ("LICENSE.md", "README.md", "labels.csv", "manifest.json", "metadata.jsonl"):
        path = destination / filename
        output_files.append({"path": f"{DATASET_ID}/{filename}", "sha256": sha256_file(path), "size": path.stat().st_size})
    artifact_manifest = {
        "manifest_version": "1.0.0", "dataset_id": DATASET_ID, "artifact_version": ARTIFACT_VERSION,
        "files": sorted(output_files, key=lambda item: item["path"]), "image_count": len(output_rows),
        "label_format": "classification_csv_and_jsonl", "transform_version": TRANSFORM_VERSION,
        "license": LICENSE, "attribution": attribution,
        "source": {"url": SOURCE_URL, "version": "1", "sha256": SOURCE_SHA256},
    }
    report = {
        "dataset_id": DATASET_ID, "source_version": "1", "source_url": SOURCE_URL,
        "source_archive": {"filename": "Orginal Data.zip", "file_id": SOURCE_FILE_ID,
                           "size": SOURCE_SIZE, "sha256": SOURCE_SHA256},
        "source_file_count": len(source_inventory), "source_image_count": len(source_inventory),
        "source_dimensions": dict(input_dimensions), "source_gps_metadata_images": gps_count,
        "source_class_counts": dict(Counter(CLASS_MAP[PurePosixPath(row["path"]).parts[1]] for row in source_inventory)),
        "image_count": len(output_rows), "classes": class_report, "excluded_exact_duplicates": excluded_duplicates,
        "transform": {"version": TRANSFORM_VERSION, "max_side": MAX_SIDE, "resize": "Pillow LANCZOS",
                      "jpeg_quality": 86, "exif_removed": True, "split_seed": seed,
                      "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15}},
        "output_split_counts": {key: split_totals[key] for key in ("train", "val", "test")},
        "output_image_bytes": sum(item["size"] for item in output_files if "/images/" in item["path"]),
        "source_inventory": source_inventory,
        "artifact_manifest": artifact_manifest,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.source_zip, args.destination)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    source_inventory = report.pop("source_inventory")
    artifact_manifest = report.pop("artifact_manifest")
    source_archive = {
        "manifest_type": "source_file_inventory", "manifest_version": "1.0.0",
        "dataset_id": DATASET_ID, "provider": "Mendeley Data", "source_url": SOURCE_URL,
        "source_version": "1", "license_claim": LICENSE, "file_count": 1,
        "archive_count": 1, "image_count": len(source_inventory),
        "files": [{
            "path": "Orginal Data.zip", "role": "source_archive", "file_id": SOURCE_FILE_ID,
            "filename": "Orginal Data.zip", "size": SOURCE_SIZE, "sha256": SOURCE_SHA256,
            "download_url": SOURCE_DOWNLOAD_URL,
        }],
    }
    file_inventory = {
        "manifest_type": "source_archive_contents", "dataset_id": DATASET_ID,
        "source_version": "1", "source_sha256": SOURCE_SHA256,
        "file_count": len(source_inventory), "files": source_inventory,
    }
    source_manifest_path = Path("manifests/sources/indoor_plant_varieties-v1.json")
    file_inventory_path = Path("manifests/source-file-inventories/indoor_plant_varieties-v1.json")
    artifact_manifest_path = Path("manifests/indoor_plant_varieties-v0.1.0.json")
    for path, value in (
        (source_manifest_path, source_archive),
        (file_inventory_path, file_inventory),
        (artifact_manifest_path, artifact_manifest),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["source_file_inventory"] = file_inventory_path.as_posix()
    report["artifact_manifest"] = artifact_manifest_path.as_posix()
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {key: report[key] for key in ("source_image_count", "image_count", "output_split_counts", "output_image_bytes")}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
