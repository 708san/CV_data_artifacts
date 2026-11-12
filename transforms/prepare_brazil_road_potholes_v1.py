"""Prepare the fixed Mendeley v3 pothole masks as a CV_data segmentation case."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path


DATASET_ID = "brazil_road_potholes"
SOURCE_URL = "https://data.mendeley.com/datasets/t576ydh9v8/3"
SOURCE_VERSION = "Mendeley Data v3, DOI 10.17632/t576ydh9v8.3"
SOURCE_SHA256 = "e59bb8d771e18f059ab78d88e640e83869fc8c8fd808697a0c2c48e16eec4f76"
LICENSE = "CC BY 4.0"
ATTRIBUTION = (
    "Bianka T. Passos, Mateus J. Cassaniga, Anita M. R. Fernandes, Kátya B. Medeiros, "
    "and Eros Comunello (2020), Cracks and Potholes in Road Images, Mendeley Data v3, "
    "https://doi.org/10.17632/t576ydh9v8.3, CC BY 4.0. Images were supplied by DNIT. "
    "The pothole mask was retained, and the data was reorganized and split by road segment."
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def road_group(path: Path) -> str:
    parts = path.stem.split("_")
    if len(parts) < 5 or not parts[0].isdigit():
        raise ValueError(f"unexpected source image filename: {path.name}")
    return "_".join(parts[1:4])


def group_splits(counts: dict[str, int], seed: int = 42) -> dict[str, str]:
    """Greedily balance route segments while keeping every segment in one split."""
    names = list(counts)
    random.Random(seed).shuffle(names)
    names.sort(key=lambda name: counts[name], reverse=True)
    total = sum(counts.values())
    targets = {"train": total * .70, "val": total * .15, "test": total * .15}
    assigned = Counter()
    result: dict[str, str] = {}
    for name in names:
        split = max(targets, key=lambda key: (targets[key] - assigned[key], key == "train"))
        result[name] = split
        assigned[split] += counts[name]
    return result


def prepare(source_root: Path, destination: Path, manifest_path: Path) -> dict:
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    source_root = source_root.resolve()
    images = sorted(source_root.glob("*/*_RAW.jpg"))
    if len(images) != 2235:
        raise ValueError(f"expected 2,235 source images, got {len(images)}")
    records = []
    counts: Counter[str] = Counter()
    for image in images:
        stem = image.name[:-8]
        mask = image.with_name(f"{stem}_POTHOLE.png")
        if image.is_symlink() or mask.is_symlink() or not mask.is_file():
            raise ValueError(f"unsafe or missing image/mask pair: {image}")
        group = road_group(image)
        counts[group] += 1
        records.append((image, mask, group))
    splits = group_splits(dict(counts))
    destination.mkdir(parents=True)
    rows = []
    file_rows = []

    def copy(source: Path, relative: Path) -> None:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        file_rows.append({"path": f"{DATASET_ID}/{relative.as_posix()}", "sha256": sha256(target), "size": target.stat().st_size})

    for image, mask, group in records:
        split = splits[group]
        key = image.parent.name
        image_rel = Path("images") / split / "pothole" / f"{key}.jpg"
        mask_rel = Path("masks") / split / "pothole" / f"{key}_mask.png"
        copy(image, image_rel)
        copy(mask, mask_rel)
        rows.append({"image": image_rel.as_posix(), "mask": mask_rel.as_posix(), "class_name": "pothole", "class_id": "0", "split": split})

    (destination / "labels.csv").write_text(
        "image,mask,class_name,class_id,split\n" + "".join(
            f'{r["image"]},{r["mask"]},{r["class_name"]},{r["class_id"]},{r["split"]}\n' for r in rows
        ), encoding="utf-8")
    metadata = [{k: r[k] if k not in {"class_id"} else int(r[k]) for k in ("image", "mask", "class_name", "class_id", "split")} for r in rows]
    (destination / "metadata.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metadata), encoding="utf-8")
    (destination / "classes.json").write_text(json.dumps({"classes": [{"id": 0, "name": "pothole", "name_ja": "道路の穴"}]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "LICENSE.md").write_text(
        "# License and attribution\n\n"
        "This dataset is redistributed under CC BY 4.0. Attribute the authors and source dataset; "
        "link to https://creativecommons.org/licenses/by/4.0/ and indicate that images were reorganized "
        "and the pothole mask was selected. The source says the road images were supplied by DNIT; "
        "their DNIT watermark remains in the unmodified images. No DNIT endorsement is implied.\n\n"
        f"{ATTRIBUTION}\n", encoding="utf-8")
    (destination / "README.md").write_text(
        "# Brazil road potholes\n\n"
        "2,235 original 1024×640 road images paired with the source pothole masks. The images are unchanged. "
        "The archive is reorganized into train/val/test groups by the road-segment key in the source filename "
        "so adjacent frames from one segment do not cross splits. Masks remain the source PNGs; the source "
        "also contains crack and lane masks, which are not included here.\n\n"
        "This dataset can support a classroom prototype that highlights pothole regions in road photos to "
        "help document maintenance requests. Images are Brazilian highways from 2014–2017, not local road "
        "coverage; the model cannot determine road safety or whether a repair is needed.\n\n"
        f"Source: {SOURCE_URL} ({SOURCE_VERSION}), {LICENSE}.\n", encoding="utf-8")
    manifest = {
        "dataset_id": DATASET_ID, "artifact_version": "0.1.0", "image_count": len(rows),
        "task": "image_segmentation", "classes": ["pothole"], "mask_encoding": "grayscale_0_255",
        "class_names_ja": ["道路の穴"],
        "label_format": "paired_image_mask_csv_and_jsonl", "transform_version": "source_pothole_masks_preserved; group_split_by_road_segment_v1",
        "license": LICENSE, "attribution": ATTRIBUTION,
        "source": {"url": SOURCE_URL, "version": SOURCE_VERSION, "sha256": SOURCE_SHA256},
        "split_counts": dict(Counter(r["split"] for r in rows)), "split_group_count": len(counts),
    }
    for name, content in (("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"),):
        (destination / name).write_text(content, encoding="utf-8")
    for name in ("LICENSE.md", "README.md", "labels.csv", "metadata.jsonl", "classes.json", "manifest.json"):
        p = destination / name
        file_rows.append({"path": f"{DATASET_ID}/{name}", "sha256": sha256(p), "size": p.stat().st_size})
    out_manifest = {
        "manifest_version": "1.0.0", "dataset_id": DATASET_ID, "artifact_version": "0.1.0",
        "files": sorted(file_rows, key=lambda row: row["path"]), "image_count": len(rows),
        "label_format": "paired_image_mask_csv_and_jsonl", "transform_version": manifest["transform_version"],
        "license": LICENSE, "attribution": ATTRIBUTION,
        "source": {"url": SOURCE_URL, "version": SOURCE_VERSION, "sha256": SOURCE_SHA256},
        "audit": {"split_group_count": len(counts), "split_groups": splits, "source_images": 2235,
                  "source_mask_types": ["LANE", "CRACK", "POTHOLE"], "included_mask_type": "POTHOLE",
                  "source_image_dimensions": "1024x640", "source_image_watermark": "DNIT"},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = prepare(args.source_root, args.destination, args.manifest)
    print(json.dumps({"image_count": result["image_count"], "splits": result["audit"], "files": len(result["files"])}, ensure_ascii=False))
