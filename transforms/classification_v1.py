"""分類データをCV_dataの共通形式へ変換する標準ライブラリ用スクリプト。

入力は、固定Releaseを安全に展開したデータセットディレクトリを想定する。
元画像の内容は変更せず、画像をコピーしてlabels.csv・metadata.jsonl・manifest.jsonを
標準化する。ネットワークアクセスや元リポジトリへの書き込みは行わない。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pgm"}
TRANSFORM_VERSION = "classification_v1.0.0"


class TransformError(RuntimeError):
    """共通形式への変換条件を満たさない場合。"""


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.parts[0] != "images"
        or path.suffix.lower() not in IMAGE_EXTENSIONS
    ):
        raise TransformError(f"画像パスが共通形式に適合しません: {value}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_input(source_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest_path = source_root / "manifest.json"
    labels_path = source_root / "labels.csv"
    if not manifest_path.is_file() or not labels_path.is_file():
        raise TransformError("入力にmanifest.jsonまたはlabels.csvがありません。")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TransformError(f"manifest.jsonを読めません: {exc}") from exc
    with labels_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"image", "label", "split"}
        if not required.issubset(set(reader.fieldnames or ())):
            raise TransformError("labels.csvにはimage,label,split列が必要です。")
        rows = list(reader)
    expected = manifest.get("image_count")
    if not isinstance(expected, int) or expected != len(rows):
        raise TransformError("manifestの画像数とlabels.csvの行数が一致しません。")
    return manifest, rows


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
    """分類データをコピーし、artifact manifestを返す。"""
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    source_manifest, rows = _read_input(source_root)
    if destination_root.exists():
        raise TransformError(f"出力先は既に存在します: {destination_root}")
    if not dataset_id or not source_url.startswith("https://"):
        raise TransformError("dataset_idとhttpsのsource_urlが必要です。")
    if len(source_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_sha256):
        raise TransformError("source_sha256は小文字64桁のSHA-256で指定してください。")

    classes = tuple(source_manifest.get("classes", ()))
    if not classes or len(set(classes)) != len(classes):
        raise TransformError("manifestのclassesが空、または重複しています。")
    class_to_id = {label: index for index, label in enumerate(classes)}
    seen: set[str] = set()
    output_rows: list[dict[str, str]] = []
    metadata_rows: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []

    for row in rows:
        relative = _relative(row["image"])
        label = row["label"]
        split = row["split"]
        if label not in class_to_id or split not in {"train", "val", "test"}:
            raise TransformError(f"ラベルまたはsplitが不正です: {row}")
        relative_text = relative.as_posix()
        if relative_text in seen:
            raise TransformError(f"画像パスが重複しています: {relative_text}")
        seen.add(relative_text)
        if relative.parts[:3] != ("images", split, label):
            raise TransformError(f"画像パスとラベルが一致しません: {relative_text}")
        source_path = source_root.joinpath(*relative.parts)
        if source_path.is_symlink() or not source_path.is_file():
            raise TransformError(f"画像が通常ファイルではありません: {relative_text}")
        target_path = destination_root.joinpath(*relative.parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
        digest = _sha256(target_path)
        size = target_path.stat().st_size
        sample_id = relative.with_suffix("").as_posix()
        output_rows.append({
            "image": relative_text,
            "label": label,
            "label_id": str(class_to_id[label]),
            "split": split,
            "sample_id": sample_id,
        })
        metadata_rows.append({
            "file_name": relative_text,
            "label": label,
            "label_id": class_to_id[label],
            "split": split,
            "sample_id": sample_id,
        })
        files.append({"path": f"{dataset_id}/" + relative_text, "sha256": digest, "size": size})

    dataset_root = destination_root
    (dataset_root / "labels.csv").write_text(
        "image,label,label_id,split,sample_id\n"
        + "".join(
            f'{row["image"]},{row["label"]},{row["label_id"]},{row["split"]},{row["sample_id"]}\n'
            for row in output_rows
        ),
        encoding="utf-8",
    )
    (dataset_root / "metadata.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metadata_rows),
        encoding="utf-8",
    )
    normalized_manifest = {
        "case_id": dataset_id,
        "version": f"v{artifact_version}",
        "task": "image_classification",
        "image_count": len(rows),
        "classes": list(classes),
        "format": "imagefolder",
        "labels": "labels.csv",
        "metadata": "metadata.jsonl",
        "source": {
            "url": source_url,
            "version": source_version,
            "sha256": source_sha256,
        },
        "license": {"name": license_name},
        "attribution": attribution,
        "transform_version": TRANSFORM_VERSION,
    }
    (dataset_root / "manifest.json").write_text(
        json.dumps(normalized_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (dataset_root / "README.md").write_text(
        "CV_data common classification format. See manifest.json for source, license, and transform details.\n",
        encoding="utf-8",
    )
    fixed_files = [
        {"path": f"{dataset_id}/manifest.json", "sha256": _sha256(dataset_root / "manifest.json"), "size": (dataset_root / "manifest.json").stat().st_size},
        {"path": f"{dataset_id}/labels.csv", "sha256": _sha256(dataset_root / "labels.csv"), "size": (dataset_root / "labels.csv").stat().st_size},
        {"path": f"{dataset_id}/metadata.jsonl", "sha256": _sha256(dataset_root / "metadata.jsonl"), "size": (dataset_root / "metadata.jsonl").stat().st_size},
        {"path": f"{dataset_id}/README.md", "sha256": _sha256(dataset_root / "README.md"), "size": (dataset_root / "README.md").stat().st_size},
    ]
    artifact_manifest = {
        "manifest_version": "1.0.0",
        "dataset_id": dataset_id,
        "artifact_version": artifact_version,
        "files": fixed_files + files,
        "image_count": len(rows),
        "label_format": "classification_csv_and_jsonl",
        "transform_version": TRANSFORM_VERSION,
        "license": license_name,
        "attribution": attribution,
        "source": {"url": source_url, "version": source_version, "sha256": source_sha256},
    }
    return artifact_manifest


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
    artifact_manifest = prepare(
        args.source_root,
        args.destination_root,
        dataset_id=args.dataset_id,
        artifact_version=args.artifact_version,
        source_url=args.source_url,
        source_version=args.source_version,
        source_sha256=args.source_sha256,
        license_name=args.license_name,
        attribution=args.attribution,
    )
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(artifact_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"dataset_id": args.dataset_id, "image_count": artifact_manifest["image_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
