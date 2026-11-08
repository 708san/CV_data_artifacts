"""Build the reviewed 29-class FruitSeg30 artifact from a verified source inventory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXCLUDED_CLASS = "Guava"
ATTRIBUTION = (
    "F. M. Javed Mehedi Shamrat; Rashiduzzaman Shakil; Mohd Yamani Idna Idris; "
    "Bonna Akter; Xujuan Zhou (2024), “FruitSeg30_Segmentation Dataset & Mask "
    "Annotations,” Mendeley Data v3, DOI: 10.17632/vkht8pfsp3.3, CC BY 4.0."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fixed_source_digest(files: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda row: row["path"]):
        digest.update(item["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item["size"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(item["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def prepare(source_root: Path, source_manifest_path: Path, output_root: Path,
            artifact_manifest_path: Path) -> dict[str, Any]:
    source = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source.get("dataset_id") != "fruitseg30" or source.get("source_version") != "3":
        raise ValueError("expected the fixed FruitSeg30 v3 inventory")
    if output_root.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_root}")
    if artifact_manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite existing manifest: {artifact_manifest_path}")

    # Verify the whole fixed source set, including the excluded class, before copying.
    for item in source["files"]:
        path = source_root / item["path"]
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or symlink source file: {item['path']}")
        if path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
            raise ValueError(f"source size/SHA-256 mismatch: {item['path']}")

    images: dict[tuple[str, str], dict[str, Any]] = {}
    masks: dict[tuple[str, str], dict[str, Any]] = {}
    for item in source["files"]:
        if item["role"] == "image":
            images[(item["class_name"], item["pair_id"])] = item
        elif item["role"] == "mask":
            masks[(item["class_name"], item["pair_id"])] = item
        else:
            raise ValueError(f"unexpected source role: {item['role']}")
    if images.keys() != masks.keys():
        raise ValueError("source image/mask keys do not match")

    output_root.mkdir(parents=True)
    dataset_root = output_root / "fruitseg30"
    (dataset_root / "images").mkdir(parents=True)
    (dataset_root / "masks").mkdir()
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (class_name, _), item in images.items():
        if class_name != EXCLUDED_CLASS:
            by_class[class_name].append(item)
    classes = sorted(by_class)
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    class_counts: dict[str, dict[str, int]] = {}

    for class_id, class_name in enumerate(classes):
        items = sorted(by_class[class_name], key=lambda row: row["pair_id"])
        random.Random(42 + class_id).shuffle(items)
        n_train, n_val = int(len(items) * .70), int(len(items) * .15)
        split_for: dict[str, str] = {}
        for item in items[:n_train]:
            split_for[item["pair_id"]] = "train"
        for item in items[n_train:n_train + n_val]:
            split_for[item["pair_id"]] = "val"
        for item in items[n_train + n_val:]:
            split_for[item["pair_id"]] = "test"
        class_counts[class_name] = {
            "image_count": len(items), "train": n_train, "val": n_val,
            "test": len(items) - n_train - n_val,
        }
        for item in by_class[class_name]:
            pair_id = item["pair_id"]
            split = split_for[pair_id]
            mask = masks[(class_name, pair_id)]
            image_name = f"images/{split}/{class_name}/{item['filename']}"
            mask_name = f"masks/{split}/{class_name}/{mask['filename']}"
            for source_item, relative in ((item, image_name), (mask, mask_name)):
                target = dataset_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_root / source_item["path"], target)
            rows.append({"image": image_name, "mask": mask_name,
                         "class_name": class_name, "class_id": class_id, "split": split})
            counts[split] += 1

    rows.sort(key=lambda row: (row["class_id"], row["split"], row["image"]))
    with (dataset_root / "labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "mask", "class_name", "class_id", "split"])
        writer.writeheader()
        writer.writerows(rows)
    with (dataset_root / "metadata.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    metadata = {
        "dataset_id": "fruitseg30", "artifact_version": "0.1.0", "task": "segmentation",
        "classes": classes, "class_counts": class_counts, "split_counts": dict(counts),
        "image_count": len(rows), "mask_count": len(rows), "image_format": "JPEG",
        "mask_format": "PNG grayscale, 8-bit",
        "mask_pixel_semantics": "Original grayscale mask preserved unchanged. Pixel values range 0–255 with antialiased boundaries; black is background and white is fruit according to reviewed examples. Threshold choice is left to the exercise.",
        "split_method": "Stratified within each class: deterministic random seed 42 plus sorted class index, 70/15/remaining assignment. Exact file-content duplicates are absent from the official inventory; near-duplicate/capture-session grouping was not audited.",
        "excluded_content": {"class": EXCLUDED_CLASS, "source_pairs": 55,
            "reason": "All 55 Guava image/mask files have non-512 dimensions; 52 of 55 same-name pairs have different image and mask dimensions (image/mask orientation and scale mismatch). Excluded the whole class rather than guessing rotations or resampling labels."},
        "source_attribution": ATTRIBUTION,
        "source_url": "https://data.mendeley.com/datasets/vkht8pfsp3/3", "source_version": "3",
    }
    (dataset_root / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dataset_root / "README.md").write_text(
        "# FruitSeg30（教材用29クラス候補）\n\n"
        "果物画像とグレースケールマスクの組です。画像・マスクは画素を変更せず収録し、train/val/testの分割と不整合クラスの除外だけを行いました。\n\n"
        "- 29クラス、1,914画像と1,914マスク\n"
        "- 画像：JPEG、512×512\n"
        "- マスク：8-bit grayscale PNG、512×512。境界は0〜255の濃淡で表現され、2値化していません。\n"
        "- `labels.csv`の`image`と`mask`列で組を対応します。\n"
        "- Guava 55組は除外しました。52組で同名画像とマスクの縦横寸法が異なり、向きや対応を推測して補正しないためです。\n"
        "- 分割はクラスごとにseed 42で行っています。まったく同じファイル内容の重複はありません。撮影系列・似た画像の重複は未検査です。\n\n"
        "## ライセンスと出典\n\n"
        "元データ：FruitSeg30 v3、CC BY 4.0。詳細な帰属表示、変更内容、注意点はartifactに同梱するライセンス記録をご覧ください。\n\n"
        "これは果物領域を画像から切り出す学習用データです。鮮度・品質・食べられるかを判定するデータではありません。\n",
        encoding="utf-8",
    )
    (dataset_root / "LICENSE.md").write_text(
        "# FruitSeg30 v3 — attribution and changes\n\n"
        f"{ATTRIBUTION}\n\n"
        "Mendeley Data v3 displays CC BY 4.0. The related data article is also published under CC BY.\n\n"
        "Changes in this artifact: all 55 Guava image/mask pairs were excluded because their dimensions are nonstandard and 52 same-name pairs have different image and mask dimensions. The remaining 29 classes (1,914 pairs) retain original image and grayscale-mask pixels; only the class-wise train/val/test assignment was added (seed 42).\n\n"
        "The source record says the contributors collected/captured fruit images in Malaysia, Bangladesh, and Australia. Every file in the official v3 inventory was checked against its listed size and SHA-256 before preparation. Independent provenance review of every source image was not performed. Do not use this educational segmentation data to judge freshness, quality, or food safety.\n",
        encoding="utf-8",
    )

    artifact_files = []
    for path in sorted(dataset_root.rglob("*")):
        if path.is_file():
            artifact_files.append({"path": path.relative_to(output_root).as_posix(),
                                   "sha256": sha256(path), "size": path.stat().st_size})
    artifact_manifest = {
        "manifest_version": "1.0.0", "dataset_id": "fruitseg30", "artifact_version": "0.1.0",
        "files": artifact_files, "image_count": len(rows),
        "label_format": "paired_image_mask_csv_and_jsonl",
        "transform_version": "fruitseg30_29class_filter_split_v1", "license": "CC BY 4.0",
        "attribution": ATTRIBUTION,
        "source": {"url": "https://data.mendeley.com/datasets/vkht8pfsp3/3", "version": "3",
                   "sha256": fixed_source_digest(source["files"])},
    }
    artifact_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_manifest_path.write_text(json.dumps(artifact_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"images": len(rows), "classes": len(classes), "splits": dict(counts),
            "files": len(artifact_files), "source_sha256": artifact_manifest["source"]["sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("artifact_manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_root, args.source_manifest, args.output_root,
                             args.artifact_manifest), ensure_ascii=False))


if __name__ == "__main__":
    main()
