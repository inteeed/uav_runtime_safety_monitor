import unittest
from pathlib import Path

from uav_runtime_safety_monitor.runtime_paths import (
    find_runtime_root,
    optional_runtime_file,
    runtime_file,
)


class RuntimePathsTest(unittest.TestCase):
    def test_finds_repository_runtime_root(self) -> None:
        root = find_runtime_root()

        self.assertIsInstance(root, Path)
        self.assertTrue((root / "config" / "safety_limits.json").exists())

    def test_runtime_file_resolves_config(self) -> None:
        path = runtime_file("config", "safety_limits.json")

        self.assertEqual(path.name, "safety_limits.json")
        self.assertTrue(path.exists())

    def test_optional_runtime_file_returns_none_when_missing(self) -> None:
        self.assertIsNone(optional_runtime_file("config", "does_not_exist.json"))


if __name__ == "__main__":
    unittest.main()
