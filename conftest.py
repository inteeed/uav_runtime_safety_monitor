"""Pytest bootstrap.

Ensures the repository root is importable so the ``uav_safety_core`` and
``uav_runtime_safety_monitor`` packages resolve without sourcing a ROS2
workspace. This replaces the previous per-test ``sys.path`` manipulation.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
