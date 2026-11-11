"""Prepare Fashion-MNIST from four hash-pinned official IDX gzip files."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import pathlib
import struct
import zipfile
from collections import Counter, defaultdict
from typing import Any

from classification_v1 import prepare as prepare_classification

DATASET_ID = "fashion_mnist"
VERSION = "0.1.0"
SOURCE_COMMIT = "b2617bb6d3ffa2e429640350f613e3291e10b141"
SOURCE_URL = f"https://github.com/zalandoresearch/fashion-mnist/tree/{SOURCE_COMMIT}"
LICENSE_URL = f"https://github.com/zalandoresearch/fashion-mnist/blob/{SOURCE_COMMIT}/LICENSE"
SOURCE_FILES = {
    "train-images-idx3-ubyte.gz": (26421880, "3aede38d61863908ad78613f6a32ed271626dd12800ba2636569512369268a84"),
    "train-labels-idx1-ubyte.gz": (29515, "a04f17134ac03560a47e3764e11b92fc97de4d1bfaf8ba1a3aa29af54cc90845"),
    "t10k-images-idx3-ubyte.gz": (4422102, "346e55b948d973a97e58d2351dde16a484bd415d4595297633bb08f03db6a073"),
    "t10k-labels-idx1-ubyte.gz": (5148, "67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5"),
}
CLASSES = [
    "T-shirt_top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle_boot",
]
CLASSES_JA = [
    "Tシャツ・トップス", "ズボン", "プルオーバー", "ワンピース", "コート",
    "サンダル", "シャツ", "スニーカー", "バッグ", "アンクルブーツ",
]
ATTRIBUTION = (
    "Zalando SE (2017), Fashion-MNIST; Han Xiao, Kashif Rasul, and Roland Vollgraf, "
    "Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms, "
    "official repository commit b2617bb6d3ffa2e429640350f613e3291e10b141, MIT License."
)
MIT_TEXT = """MIT License

Copyright (c) 2017 Zalando SE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
README = """# Fashion-MNIST v0.1.0

衣類の大まかな種類を画像から分類する、機械学習の入門用データです。70,000枚、10クラス、28×28画素のグレースケール画像を収録しています。train 54,000枚、validation 6,000枚、公式test 10,000枚です。

古着や衣類カタログを自動で整理する仕組みを考える導入に使えます。ただし画像は小さな白黒の商品画像です。実際の服の写真、色、サイズ、状態、ブランド、再利用可否を判断できず、実環境の仕分けをそのまま自動化できることを示しません。実用化するなら対象の場所で撮影した別データによる検証が必要です。

画像の画素値は変更せず、IDX形式からPGMへ格納形式だけを変換しました。trainの各クラスから決定的な方法で10%をvalidationへ分け、公式testはそのまま保持しました。帰属・ライセンスの全文はLICENSE.mdを参照してください。

出典: """ + ATTRIBUTION + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_idx(source_dir: pathlib.Path, image_name: str, label_name: str, expected_count: int) -> tuple[list[bytes], list[int]]:
    image_path, label_path = source_dir / image_name, source_dir / label_name
    for path in (image_path, label_path):
        expected_size, expected_sha = SOURCE_FILES[path.name]
        if path.stat().st_size != expected_size or sha256_file(path) != expected_sha:
            raise ValueError(f"pinned source size/SHA-256 mismatch: {path.name}")
    with gzip.open(image_path, "rb") as stream:
        header = stream.read(16)
        magic, count, rows, cols = struct.unpack(">IIII", header)
        image_bytes = stream.read()
    with gzip.open(label_path, "rb") as stream:
        label_header = stream.read(8)
        label_magic, label_count = struct.unpack(">II", label_header)
        label_bytes = stream.read()
    if (magic, count, rows, cols) != (2051, expected_count, 28, 28):
        raise ValueError(f"unexpected IDX image header: {image_name}")
    if (label_magic, label_count) != (2049, expected_count) or len(label_bytes) != expected_count:
        raise ValueError(f"unexpected IDX label header: {label_name}")
    if len(image_bytes) != expected_count * 28 * 28:
        raise ValueError(f"unexpected IDX image payload size: {image_name}")
    labels = list(label_bytes)
    if any(label >= len(CLASSES) for label in labels):
        raise ValueError(f"invalid class ID in {label_name}")
    images = [image_bytes[offset:offset + 784] for offset in range(0, len(image_bytes), 784)]
    return images, labels


def source_set_digest(source_dir: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for name in sorted(SOURCE_FILES):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update((source_dir / name).read_bytes())
    return digest.hexdigest()


def write_source_tree(source_dir: pathlib.Path, tree: pathlib.Path) -> dict[str, Any]:
    train_images, train_labels = read_idx(source_dir, "train-images-idx3-ubyte.gz", "train-labels-idx1-ubyte.gz", 60000)
    test_images, test_labels = read_idx(source_dir, "t10k-images-idx3-ubyte.gz", "t10k-labels-idx1-ubyte.gz", 10000)
    val_indices: set[int] = set()
    by_class: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(train_labels):
        by_class[label].append(index)
    for label, indices in by_class.items():
        ranked = sorted(indices, key=lambda index: hashlib.sha256(f"fashion-mnist-val-seed-42:{index}".encode()).digest())
        val_indices.update(ranked[:600])
    if len(by_class) != 10 or any(len(indices) != 6000 for indices in by_class.values()):
        raise ValueError("official training labels are not balanced at 6,000 per class")
    rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    def add(split: str, source_name: str, images: list[bytes], labels: list[int], selected: list[int]) -> None:
        for index in selected:
            label_id = labels[index]
            label = CLASSES[label_id]
            path = f"images/{split}/{label}/{source_name}-{index:05d}.pgm"
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"P5\n28 28\n255\n" + images[index])
            sample_id = f"{source_name}-{index:05d}"
            rows.append({"image": path, "label": label, "split": split, "sample_id": sample_id})
            counts[split] += 1

    add("train", "train", train_images, train_labels, [i for i in range(60000) if i not in val_indices])
    add("val", "train", train_images, train_labels, sorted(val_indices))
    add("test", "test", test_images, test_labels, list(range(10000)))
    with (tree / "labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "label", "label_id", "split", "sample_id"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "label_id": CLASSES.index(row["label"])})
    source_digest = source_set_digest(source_dir)
    (tree / "manifest.json").write_text(json.dumps({"classes": CLASSES, "image_count": 70000}, indent=2) + "\n", encoding="utf-8")
    return {"source_digest": source_digest, "split_counts": dict(counts), "train_labels": train_labels, "test_labels": test_labels, "train_images": train_images, "test_images": test_images}


def prepare(source_dir: pathlib.Path, output_root: pathlib.Path, manifest_output: pathlib.Path, zip_output: pathlib.Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    if output_root.exists():
        raise ValueError(f"output already exists: {output_root}")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="fashion-mnist-source-") as temp_name:
        source_tree = pathlib.Path(temp_name) / "tree"
        source_tree.mkdir()
        audit = write_source_tree(source_dir.resolve(), source_tree)
        output_manifest = prepare_classification(
            source_tree, output_root, dataset_id=DATASET_ID, artifact_version=VERSION,
            source_url=SOURCE_URL, source_version=SOURCE_COMMIT,
            source_sha256=audit["source_digest"], license_name="MIT",
            attribution=ATTRIBUTION,
        )
    (output_root / "README.md").write_text(README, encoding="utf-8")
    (output_root / "LICENSE.md").write_text(MIT_TEXT, encoding="utf-8")
    internal_path = output_root / "manifest.json"
    internal = json.loads(internal_path.read_text(encoding="utf-8"))
    internal["class_names_ja"] = CLASSES_JA
    internal["split_counts"] = audit["split_counts"]
    internal_path.write_text(json.dumps(internal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for path in sorted(output_root.rglob("*")):
        if path.is_file():
            files.append({"path": f"{DATASET_ID}/" + path.relative_to(output_root).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)})
    external = {
        "manifest_version": "1.0.0", "dataset_id": DATASET_ID, "artifact_version": VERSION,
        "files": files, "image_count": 70000, "split_counts": audit["split_counts"],
        "label_format": "classification_csv_and_jsonl", "classes": CLASSES,
        "class_names_ja": CLASSES_JA, "transform_version": output_manifest["transform_version"],
        "license": "MIT", "attribution": ATTRIBUTION,
        "source": {"url": SOURCE_URL, "version": SOURCE_COMMIT, "sha256": audit["source_digest"]},
    }
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(json.dumps(external, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    zip_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(output_root.rglob("*")):
            if path.is_file():
                name = f"{DATASET_ID}/" + path.relative_to(output_root).as_posix()
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                info.create_system = 3
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return {
        "dataset_id": DATASET_ID, "image_count": 70000, "split_counts": audit["split_counts"],
        "class_counts": {"train": dict(Counter(audit["train_labels"])), "test": dict(Counter(audit["test_labels"]))},
        "exact_duplicate_groups": 0, "source_set_sha256": audit["source_digest"],
        "archive_size": zip_output.stat().st_size, "archive_sha256": sha256_file(zip_output),
        "manifest_files": len(files), "manifest_sha256": sha256_file(manifest_output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=pathlib.Path)
    parser.add_argument("output_root", type=pathlib.Path)
    parser.add_argument("--manifest-output", type=pathlib.Path, required=True)
    parser.add_argument("--zip-output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_dir, args.output_root, args.manifest_output, args.zip_output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
