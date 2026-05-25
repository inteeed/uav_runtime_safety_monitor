from pathlib import Path
import os
import sys
from typing import Iterable, Optional


PACKAGE_NAME = "uav_runtime_safety_monitor"

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:  # Allows pure Python tests without sourcing ROS2.
    get_package_share_directory = None


def _candidate_roots() -> Iterable[Path]:
    env_root = os.environ.get("UAV_RUNTIME_MONITOR_ROOT")
    if env_root:
        yield Path(env_root).expanduser().resolve()

    for parent in Path(__file__).resolve().parents:
        yield parent

    if get_package_share_directory is not None:
        try:
            yield Path(get_package_share_directory(PACKAGE_NAME)).resolve()
        except Exception:
            return


def find_runtime_root() -> Path:
    for root in _candidate_roots():
        if (root / "src" / "mission_simulator.py").exists():
            return root

    raise RuntimeError(
        "Could not locate UAV runtime safety monitor source files. "
        "Set UAV_RUNTIME_MONITOR_ROOT to the repository root or install the "
        "ROS2 package data files."
    )


def add_runtime_paths() -> Path:
    root = find_runtime_root()
    for relative_path in ("src", "ros2_extension"):
        path = root / relative_path
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    return root


def runtime_file(*parts: str) -> Path:
    return find_runtime_root().joinpath(*parts)


def optional_runtime_file(*parts: str) -> Optional[Path]:
    path = runtime_file(*parts)
    if path.exists():
        return path
    return None
