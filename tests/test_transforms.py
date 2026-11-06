from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.validate_artifact import validate as validate_artifact
from transforms.segmentation_v1 import TransformError, prepare


class SegmentationTransformTests(unittest.TestCase):
    def test_pairs_are_normalized_and_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            for label in ("Apple", "Banana"):
                (source / label / "Images").mkdir(parents=True)
                (source / label / "Mask").mkdir(parents=True)
                (source / label / "Images" / "1.jpg").write_bytes(b"image-" + label.encode())
                (source / label / "Mask" / "1_mask.png").write_bytes(b"mask-" + label.encode())
            extracted = root / "package"
            dataset = extracted / "fruitseg30"
            manifest_path = root / "artifact-manifest.json"
            manifest = prepare(
                source, dataset, dataset_id="fruitseg30", artifact_version="0.1.0",
                source_url="https://example.com/fruitseg.zip", source_version="v3", source_sha256="0" * 64,
                license_name="CC BY 4.0", attribution="test",
            )
            manifest_path.write_text(__import__("json").dumps(manifest), encoding="utf-8")
            result = validate_artifact(manifest_path, extracted)
            self.assertEqual(result["image_count"], 2)
            self.assertEqual((dataset / "labels.csv").read_text(encoding="utf-8").count("\n"), 3)

    def test_missing_mask_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source" / "Apple"
            (source / "Images").mkdir(parents=True)
            (source / "Mask").mkdir()
            (source / "Images" / "1.jpg").write_bytes(b"image")
            with self.assertRaises(TransformError):
                prepare(
                    source.parent.parent, Path(tmp) / "out", dataset_id="toy", artifact_version="1.0.0",
                    source_url="https://example.com/source.zip", source_version="v1", source_sha256="0" * 64,
                    license_name="CC0 1.0", attribution="test",
                )


if __name__ == "__main__":
    unittest.main()
