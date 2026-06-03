from glob import glob
from setuptools import find_packages, setup


PACKAGE_NAME = "uav_runtime_safety_monitor"


def package_data_files():
    data_files = [
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        ("share/" + PACKAGE_NAME + "/launch", glob("launch/*.launch.py")),
        ("share/" + PACKAGE_NAME + "/config", glob("config/*.json")),
        (
            "share/" + PACKAGE_NAME + "/gazebo/worlds",
            glob("gazebo_extension/worlds/*.world"),
        ),
        (
            "share/" + PACKAGE_NAME + "/gazebo/models/safety_uav",
            glob("gazebo_extension/models/safety_uav/*"),
        ),
    ]
    return data_files


setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(
        include=[
            PACKAGE_NAME,
            PACKAGE_NAME + ".*",
            "uav_safety_core",
            "uav_safety_core.*",
        ]
    ),
    data_files=package_data_files(),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="inteed",
    maintainer_email="inteed2006@gmail.com",
    description=(
        "Runtime safety monitoring prototype for autonomous UAV missions "
        "with ROS2 and Gazebo integration."
    ),
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "uav_state_publisher = uav_runtime_safety_monitor.uav_state_publisher_node:main",
            "safety_monitor = uav_runtime_safety_monitor.safety_monitor_node:main",
            "mission_supervisor = uav_runtime_safety_monitor.mission_supervisor_node:main",
            "gazebo_state_bridge = uav_runtime_safety_monitor.gazebo_state_bridge_node:main",
            "gazebo_mission_commander = uav_runtime_safety_monitor.gazebo_mission_commander_node:main",
            "px4_state_bridge = uav_runtime_safety_monitor.px4_state_bridge_node:main",
            "px4_command_bridge = uav_runtime_safety_monitor.px4_command_bridge_node:main",
            "px4_environment_check = uav_runtime_safety_monitor.px4_environment_check:main",
            "safety_console = uav_runtime_safety_monitor.safety_console_node:main",
            "live_log = uav_runtime_safety_monitor.live_log_node:main",
            "fault_injection = uav_runtime_safety_monitor.fault_injection_node:main",
            "manual_violation_publisher = uav_runtime_safety_monitor.manual_violation_publisher_node:main",
        ],
    },
)
