from __future__ import annotations

import unittest

from tools.validate_registry import validate


class RegistryTests(unittest.TestCase):
    def test_empty_registry_is_valid_before_first_approved_artifact(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
