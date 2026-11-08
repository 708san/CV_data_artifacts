from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_artifact import validate as validate_artifact
from transforms.detection_yolo_v1 import TransformError, prepare


class DetectionTransformTests(unittest.TestCase):
    def test_yolo_pairs_are_normalized_and_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            (source / "train/images").mkdir(parents=True)
            (source / "train/labels").mkdir(parents=True)
            (source / "classes.json").write_text(json.dumps({"classes": ["pen", "book"]}), encoding="utf-8")
            (source / "train/images/one.jpg").write_bytes(b"image")
            (source / "train/labels/one.txt").write_text("0 0.5 0.5 0.2 0.3\n", encoding="utf-8")
            extracted = root / "package"
            manifest_path = root / "artifact-manifest.json"
            manifest = prepare(
                source, extracted / "geoset", dataset_id="geoset", artifact_version="0.1.0",
                source_url="https://example.com/source.zip", source_version="v1", source_sha256="0" * 64,
                license_name="CC BY 4.0", attribution="test",
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(validate_artifact(manifest_path, extracted)["image_count"], 1)

    def test_mixed_boxes_and_polygons_convert_to_normalized_boxes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            (source / "train/images").mkdir(parents=True)
            (source / "train/labels").mkdir(parents=True)
            (source / "classes.json").write_text(json.dumps({"classes": ["device"]}), encoding="utf-8")
            (source / "train/images/one.jpg").write_bytes(b"image")
            (source / "train/labels/one.txt").write_text(
                "0 0.5 0.5 0.2 0.3\n0 0.1 0.2 0.5 0.2 0.4 0.8\n", encoding="utf-8"
            )
            extracted = root / "package"
            manifest = prepare(
                source, extracted / "ewaste", dataset_id="ewaste", artifact_version="0.1.0",
                source_url="https://example.com/source.zip", source_version="v1", source_sha256="0" * 64,
                license_name="CC BY 4.0", attribution="test",
            )
            record = json.loads((extracted / "ewaste/annotations.jsonl").read_text(encoding="utf-8"))
            normalized = (extracted / "ewaste/labels/train/one.txt").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(normalized), 2)
            self.assertEqual(len(normalized[0].split()), 5)
            self.assertEqual(len(normalized[1].split()), 5)
            self.assertEqual(record["annotations"][0]["source_annotation_format"], "bbox")
            self.assertEqual(record["annotations"][0]["width"], 0.2)
            self.assertEqual(record["annotations"][1]["source_annotation_format"], "polygon")
            self.assertEqual(record["annotations"][1]["x_center"], 0.3)
            self.assertEqual(record["annotations"][1]["y_center"], 0.5)
            self.assertEqual(manifest["annotation_conversion"]["source_bbox_rows_preserved"], 1)
            self.assertEqual(manifest["annotation_conversion"]["source_polygon_rows_converted_to_bbox"], 1)

    def test_degenerate_polygon_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            (source / "train/images").mkdir(parents=True)
            (source / "train/labels").mkdir(parents=True)
            (source / "classes.json").write_text(json.dumps(["device"]), encoding="utf-8")
            (source / "train/images/one.jpg").write_bytes(b"image")
            (source / "train/labels/one.txt").write_text("0 0.2 0.2 0.2 0.2 0.2 0.2\n", encoding="utf-8")
            with self.assertRaises(TransformError):
                prepare(source, root / "out", dataset_id="toy", artifact_version="1.0.0",
                        source_url="https://example.com/source.zip", source_version="v1", source_sha256="0" * 64,
                        license_name="CC BY 4.0", attribution="test")

    def test_data_yaml_class_list_is_read_without_yaml_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "data.yaml").write_text(
                "train: ../train/images\nval: ../valid/images\nnc: 2\nnames: ['battery', 'phone']\n",
                encoding="utf-8",
            )
            from transforms.detection_yolo_v1 import _read_classes
            self.assertEqual(_read_classes(source), ["battery", "phone"])

    def test_out_of_range_box_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            (source / "train/images").mkdir(parents=True)
            (source / "train/labels").mkdir(parents=True)
            (source / "classes.json").write_text(json.dumps(["pen"]), encoding="utf-8")
            (source / "train/images/one.jpg").write_bytes(b"image")
            (source / "train/labels/one.txt").write_text("0 1.2 0.5 0.2 0.3\n", encoding="utf-8")
            with self.assertRaises(TransformError):
                prepare(source, root / "out", dataset_id="toy", artifact_version="1.0.0",
                        source_url="https://example.com/source.zip", source_version="v1", source_sha256="0" * 64,
                        license_name="CC BY 4.0", attribution="test")


if __name__ == "__main__":
    unittest.main()
