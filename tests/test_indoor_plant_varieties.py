import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from transforms.indoor_plant_varieties_v1 import CLASS_MAP, PreparationError, prepare


class IndoorPlantPreparationTests(unittest.TestCase):
    def make_source_zip(self, path, *, unsafe=False):
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            duplicate_bytes = None
            for source_class_index, source_class in enumerate(CLASS_MAP):
                for index in range(10):
                    image = Image.new("RGB", (640, 480), (source_class_index * 30, index * 10, 90))
                    exif = Image.Exif()
                    exif[270] = "private image description"
                    stream = io.BytesIO()
                    image.save(stream, format="JPEG", exif=exif)
                    image_bytes = stream.getvalue()
                    archive.writestr(f"Orginal Data/{source_class}/img_{index:02}.jpg", image_bytes)
                    if source_class == "Aglaonema" and index == 0:
                        duplicate_bytes = image_bytes
            archive.writestr("Orginal Data/Aglaonema/img_duplicate.jpg", duplicate_bytes)
            if unsafe:
                archive.writestr("../escape.jpg", b"bad")

    def prepare_fixture(self, archive, destination):
        return prepare(
            archive,
            destination,
            expected_size=archive.stat().st_size,
            expected_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        )

    def test_prepares_split_metadata_and_strips_exif(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.zip"
            output = root / "output"
            self.make_source_zip(source)
            report = self.prepare_fixture(source, output)
            self.assertEqual(report["image_count"], 70)
            self.assertEqual(len(report["excluded_exact_duplicates"]), 1)
            self.assertEqual(report["output_split_counts"], {"train": 49, "val": 14, "test": 7})
            with (output / "labels.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 70)
            sample = output / rows[0]["image"]
            with Image.open(sample) as image:
                self.assertLessEqual(max(image.size), 512)
                self.assertEqual(image.getexif(), {})
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["classes"], sorted(CLASS_MAP.values()))

    def test_rejects_unsafe_zip_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "unsafe.zip"
            self.make_source_zip(source, unsafe=True)
            with self.assertRaises(PreparationError):
                self.prepare_fixture(source, root / "output")

    def test_rejects_wrong_source_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.zip"
            self.make_source_zip(source)
            with self.assertRaises(PreparationError):
                prepare(source, root / "output", expected_size=source.stat().st_size, expected_sha256="0" * 64)


if __name__ == "__main__":
    unittest.main()
