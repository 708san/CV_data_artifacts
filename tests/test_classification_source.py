import tempfile
import unittest
from pathlib import Path

from transforms.classification_source_v1 import SourcePreparationError, prepare


class ClassificationSourceTests(unittest.TestCase):
    def make_source(self, root):
        for label in ("alpha", "beta"):
            folder = root / label
            folder.mkdir(parents=True)
            for index in range(6):
                (folder / f"{label}_{index}.jpg").write_bytes(f"{label}-{index}".encode())

    def test_split_is_stratified_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            self.make_source(source)
            first = prepare(source, root / "first", seed=42)
            second = prepare(source, root / "second", seed=42)
            self.assertEqual(first["class_counts"], second["class_counts"])
            self.assertEqual(
                (root / "first" / "labels.csv").read_bytes(),
                (root / "second" / "labels.csv").read_bytes(),
            )
            self.assertEqual(first["image_count"], 12)
            for counts in first["class_counts"].values():
                self.assertEqual(counts["splits"], {"train": 4, "val": 1, "test": 1})

    def test_exact_duplicates_are_excluded_and_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            (source / "fish").mkdir(parents=True)
            for name, data in (("a.jpg", b"one"), ("b.jpg", b"two"), ("c.jpg", b"three"), ("d.jpg", b"one")):
                (source / "fish" / name).write_bytes(data)
            report = prepare(source, root / "out")
            self.assertEqual(report["image_count"], 3)
            self.assertEqual(report["excluded_exact_duplicates"][0]["path"], "fish/d.jpg")

    def test_duplicate_bytes_with_conflicting_classes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source" / "alpha").mkdir(parents=True)
            (root / "source" / "beta").mkdir()
            for index in range(3):
                (root / "source" / "alpha" / f"a{index}.jpg").write_bytes(f"alpha-{index}".encode())
                (root / "source" / "beta" / f"b{index}.jpg").write_bytes(f"beta-{index}".encode())
            (root / "source" / "beta" / "b0.jpg").write_bytes(
                (root / "source" / "alpha" / "a0.jpg").read_bytes()
            )
            with self.assertRaises(SourcePreparationError):
                prepare(root / "source", root / "out")

    def test_non_image_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source" / "alpha").mkdir(parents=True)
            (root / "source" / "alpha" / "notes.txt").write_text("not an image")
            with self.assertRaises(SourcePreparationError):
                prepare(root / "source", root / "out")


if __name__ == "__main__":
    unittest.main()
