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
