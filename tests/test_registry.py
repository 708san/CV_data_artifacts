from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_artifact import ArtifactValidationError, validate as validate_artifact
from tools.validate_manifest import validate as validate_manifest
from tools.validate_registry import validate


class RegistryTests(unittest.TestCase):
    def test_empty_registry_is_valid_before_first_approved_artifact(self):
        self.assertEqual(validate(), [])

    def test_artifact_manifest_checks_files_and_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extracted = root / "extracted"
            dataset = extracted / "toy"
            (dataset / "images/train/a").mkdir(parents=True)
            image = dataset / "images/train/a/one.jpg"
            image.write_bytes(b"image")
            (dataset / "labels.csv").write_text(
                "image,label,label_id,split,sample_id\n"
                "images/train/a/one.jpg,a,0,train,images/train/a/one\n",
                encoding="utf-8",
            )
            files = []
            for path in sorted(dataset.rglob("*")):
                if path.is_file():
                    files.append({
                        "path": path.relative_to(extracted).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "size": path.stat().st_size,
                    })
            manifest = {
                "manifest_version": "1.0.0", "dataset_id": "toy", "artifact_version": "1.0.0",
                "files": files, "image_count": 1, "label_format": "classification_csv_and_jsonl",
                "transform_version": "classification_v1.0.0", "license": "CC0 1.0",
                "attribution": "test", "source": {
                    "url": "https://example.com/source.zip", "version": "v1", "sha256": "0" * 64,
                },
            }
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(validate_artifact(manifest_path, extracted)["image_count"], 1)
            image.write_bytes(b"changed")
            with self.assertRaises(ArtifactValidationError):
                validate_artifact(manifest_path, extracted)

    def test_prepared_manifest_has_valid_metadata(self):
        manifest = Path(__file__).resolve().parents[1] / "manifests" / "tomato_leaves-v1.0.0.json"
        if not manifest.is_file():
            self.skipTest("prepared artifact manifest is not present")
        self.assertEqual(validate_manifest(manifest), [])


if __name__ == "__main__":
    unittest.main()
