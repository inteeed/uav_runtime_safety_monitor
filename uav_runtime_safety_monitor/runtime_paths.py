from pathlib import Path
import os
from typing import Iterable, Optional


PACKAGE_NAME = "uav_runtime_safety_monitor"

# Marker that exists both in the repository root and in the installed
# ``share/<package>`` directory, so the same lookup works in source checkouts
# and in a colcon install.
ROOT_MARKER = ("config", "safety_limits.json")

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
        if root.joinpath(*ROOT_MARKER).exists():
            return root

    raise RuntimeError(
        "Could not locate UAV runtime safety monitor data files. "
        "Set UAV_RUNTIME_MONITOR_ROOT to the repository root or install the "
        "ROS2 package data files."
    )


def runtime_file(*parts: str) -> Path:
    return find_runtime_root().joinpath(*parts)


def optional_runtime_file(*parts: str) -> Optional[Path]:
    path = runtime_file(*parts)
    if path.exists():
        return path
    return None
