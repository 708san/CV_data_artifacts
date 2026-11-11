"""Prepare the fixed Mendeley v2 cafeteria-food subset as a safe YOLO artifact."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import shutil
import stat
import tempfile
import zipfile
from collections import Counter
from typing import Any

from detection_yolo_v1 import prepare as prepare_detection

DATASET_ID = "pust_cafeteria_food"
SOURCE_URL = "https://data.mendeley.com/datasets/fn6yhzjz83/2"
PROCESSED_SHA256 = "f2f85952807a2d64d50b958c9355829cb5cad8636d611b2b9d7357e7267250a1"
PROCESSED_SIZE = 278596946
PROCESSED_FILE_ID = "9e24b022-b800-45bb-b5fb-1f6d0169db9f"
METADATA_SHA256 = "5e93b20b4e2e2d2844028d9e0dcc200ecaddecbbad0d943a6f4dedf930f6a73e"
METADATA_SIZE = 73738
METADATA_FILE_ID = "f17ac06f-e635-43bd-b063-072f309cf51b"
ATTRIBUTION = (
    "Marufa Yeasmin; Md. Razu Ahmed; Protiva Rani Kundu; Jannatul Mauya; "
    "Md. Shamim Reza (2026), PUST Cafeteria Food Image Dataset, Mendeley Data v2, "
    "DOI 10.17632/fn6yhzjz83.2, CC BY 4.0."
)
README = """# 食堂の料理画像 v0.1.0\n\n- 画像: 691枚、16クラス、2,510注釈\n- 分割: train 483 / val 103 / test 105\n- 課題: 食堂料理の画像検出\n\n料理カテゴリや位置を見える化する試作に使えます。画像はバングラデシュの一大学食堂で撮影され、日本の食堂を代表しません。価格、栄養、アレルギー、衛生、食べ残し量の情報は含みません。これらの判断には使わないでください。食器ロゴや部分的な手が写る画像があります。詳細はLICENSE.mdを参照してください。\n\n出典: """ + ATTRIBUTION + "\n"
LICENSE = """# 利用条件・帰属表示\n\n""" + ATTRIBUTION + " [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n\n変更内容: Mendeley v2の加工済みYOLOデータから、対応表でaugmentation_status=originalの画像を選択しました。拡張画像を除き、ファイル名にremovebgを含む29画像を除外。元画像の画素は変更していません。元画像単位のtrain/validation/test分割と16クラスを保持しました。polygon 2,510件を軸平行bboxへ変換し、画像境界外の座標904個（561注釈）を0〜1にクリップしました。polygonの輪郭形状は失われています。\n\n食器・包装のロゴ等の第三者権利は別途許諾済みと表明しません。ロゴは権利者の推奨を意味しません。画像・注釈は栄養、アレルギー、衛生、価格、日本国内の献立、食べ残し量の判断を支えません。\n"""


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_selected(archive: pathlib.Path, destination: pathlib.Path, wanted_prefixes: tuple[str, ...], wanted_files: set[str], expected_size: int, expected_sha: str) -> None:
    if archive.stat().st_size != expected_size or sha256(archive) != expected_sha:
        raise ValueError(f"pinned source archive checksum mismatch: {archive}")
    with zipfile.ZipFile(archive) as zf:
        if zf.testzip() is not None:
            raise ValueError(f"ZIP CRC failure: {archive}")
        for item in zf.infolist():
            path = pathlib.PurePosixPath(item.filename)
            mode = (item.external_attr >> 16) & 0xFFFF
            if path.is_absolute() or ".." in path.parts or "\\" in item.filename or stat.S_ISLNK(mode):
                raise ValueError(f"unsafe ZIP member: {item.filename}")
            keep = any(item.filename.startswith(prefix) for prefix in wanted_prefixes) or item.filename in wanted_files
            if not keep or item.is_dir():
                continue
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(item) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def prepare(processed_zip: pathlib.Path, metadata_zip: pathlib.Path, output_root: pathlib.Path, manifest_output: pathlib.Path, zip_output: pathlib.Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    if output_root.exists():
        raise ValueError(f"output exists: {output_root}")
    with tempfile.TemporaryDirectory(prefix="pust-food-") as temp_name:
        temp = pathlib.Path(temp_name)
        processed = temp / "processed"
        metadata = temp / "metadata"
        processed.mkdir(); metadata.mkdir()
        extract_selected(processed_zip, processed, ("yolo_detect/",), set(), PROCESSED_SIZE, PROCESSED_SHA256)
        extract_selected(metadata_zip, metadata, (), {"image_source_mapping _final.csv", "class_names.csv"}, METADATA_SIZE, METADATA_SHA256)
        mapping_path = metadata / "image_source_mapping _final.csv"
        classes_path = metadata / "class_names.csv"
        rows = list(csv.DictReader(mapping_path.open(encoding="utf-8-sig", newline="")))
        originals = [row for row in rows if row["augmentation_status"].strip().lower() == "original"]
        if len(originals) != 720:
            raise ValueError(f"expected 720 original-status records, got {len(originals)}")
        counts = Counter(row["split"] for row in originals)
        if counts != {"train": 504, "valid": 108, "test": 108}:
            raise ValueError(f"unexpected source split: {counts}")
        class_rows = [row for row in csv.DictReader(classes_path.open(encoding="utf-8-sig", newline="")) if row.get("class_id", "").isdigit()]
        classes = [row["machine_readable_label"] for row in sorted(class_rows, key=lambda row: int(row["class_id"]))]
        source_root = temp / "selected"
        source_root.mkdir()
        (source_root / "classes.json").write_text(json.dumps({"classes": classes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        selected = [row for row in originals if "removebg" not in row["image_filename"].lower()]
        split_counts = Counter()
        clipped_instances = clipped_coordinates = annotation_count = 0
        for row in selected:
            split = "val" if row["split"] == "valid" else row["split"]
            split_counts[split] += 1
            name = pathlib.PurePosixPath(row["image_filename"])
            label_name = pathlib.PurePosixPath(row["label_filename"])
            if len(name.parts) != 1 or len(label_name.parts) != 1:
                raise ValueError("unsafe source filename")
            src_base = processed / "yolo_detect" / row["split"]
            image_src, label_src = src_base / "images" / name.name, src_base / "labels" / label_name.name
            if not image_src.is_file() or not label_src.is_file() or image_src.is_symlink() or label_src.is_symlink():
                raise ValueError(f"missing or unsafe pair: {name.name}")
            image_dst = source_root / split / "images" / name.name
            label_dst = source_root / split / "labels" / label_name.name
            image_dst.parent.mkdir(parents=True, exist_ok=True); label_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image_src, image_dst)
            out_lines = []
            for line in label_src.read_text(encoding="utf-8").splitlines():
                values = line.split()
                class_id = int(values[0]); coords = [float(value) for value in values[1:]]
                if not 0 <= class_id < len(classes) or len(coords) < 6 or len(coords) % 2 or any(not math.isfinite(value) for value in coords):
                    raise ValueError(f"invalid polygon annotation: {label_name.name}")
                clipped = [min(1.0, max(0.0, value)) for value in coords]
                changed = sum(a != b for a, b in zip(coords, clipped))
                clipped_coordinates += changed
                clipped_instances += bool(changed)
                annotation_count += 1
                out_lines.append(str(class_id) + " " + " ".join(format(value, ".17g") for value in clipped))
            label_dst.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
        if sum(split_counts.values()) != 691 or clipped_coordinates != 904 or clipped_instances != 561 or annotation_count != 2510:
            raise ValueError("selected-image or annotation audit counts do not match the reviewed source")
        report = prepare_detection(source_root, output_root, dataset_id=DATASET_ID, artifact_version="0.1.0", source_url=SOURCE_URL, source_version="2", source_sha256=PROCESSED_SHA256, license_name="CC BY 4.0", attribution=ATTRIBUTION)

    (output_root / "README.md").write_text(README, encoding="utf-8")
    (output_root / "LICENSE.md").write_text(LICENSE, encoding="utf-8")
    internal = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))
    internal["source"].update({"file_id": PROCESSED_FILE_ID, "size": PROCESSED_SIZE})
    (output_root / "manifest.json").write_text(json.dumps(internal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = []
    for path in sorted(output_root.rglob("*")):
        if path.is_file():
            files.append({"path": f"{DATASET_ID}/" + path.relative_to(output_root).as_posix(), "size": path.stat().st_size, "sha256": sha256(path)})
    external = {"manifest_version": "1.0.0", "dataset_id": DATASET_ID, "artifact_version": "0.1.0", "files": files, "image_count": 691, "split_counts": dict(sorted(split_counts.items())), "label_format": "yolo_normalized_jsonl", "classes": classes, "transform_version": report["transform_version"], "license": "CC BY 4.0", "attribution": ATTRIBUTION, "source": {"url": SOURCE_URL, "version": "2", "sha256": PROCESSED_SHA256, "file_id": PROCESSED_FILE_ID, "size": PROCESSED_SIZE}, "annotation_conversion": report["annotation_conversion"]}
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(json.dumps(external, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(zip_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(output_root.rglob("*")):
            if path.is_file():
                archive.write(path, f"{DATASET_ID}/" + path.relative_to(output_root).as_posix())
    return {"image_count": 691, "split_counts": dict(sorted(split_counts.items())), "classes": len(classes), "annotation_count": annotation_count, "clipped_instances": clipped_instances, "clipped_coordinates": clipped_coordinates, "archive_size": zip_output.stat().st_size, "archive_sha256": sha256(zip_output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("processed_zip", type=pathlib.Path)
    parser.add_argument("metadata_zip", type=pathlib.Path)
    parser.add_argument("output_root", type=pathlib.Path)
    parser.add_argument("--manifest-output", type=pathlib.Path, required=True)
    parser.add_argument("--zip-output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.processed_zip, args.metadata_zip, args.output_root, args.manifest_output, args.zip_output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
