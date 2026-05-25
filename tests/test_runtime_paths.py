import unittest
from pathlib import Path

from uav_runtime_safety_monitor.runtime_paths import (
    add_runtime_paths,
    find_runtime_root,
    runtime_file,
)


class RuntimePathsTest(unittest.TestCase):
    def test_finds_repository_runtime_root(self) -> None:
        root = find_runtime_root()

        self.assertTrue((root / "src" / "mission_simulator.py").exists())
        self.assertTrue((root / "config" / "safety_limits.json").exists())

    def test_runtime_file_resolves_config(self) -> None:
        path = runtime_file("config", "safety_limits.json")

        self.assertEqual(path.name, "safety_limits.json")
        self.assertTrue(path.exists())

    def test_add_runtime_paths_returns_root(self) -> None:
        root = add_runtime_paths()

        self.assertIsInstance(root, Path)
        self.assertTrue((root / "ros2_extension" / "ros2_json.py").exists())


if __name__ == "__main__":
    unittest.main()
