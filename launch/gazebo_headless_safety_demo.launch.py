import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


PACKAGE_NAME = "uav_runtime_safety_monitor"


def _gazebo_master_uri() -> str:
    if os.environ.get("GAZEBO_MASTER_URI"):
        return os.environ["GAZEBO_MASTER_URI"]
    return "http://127.0.0.1:{}".format(12000 + os.getpid() % 1000)


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory(PACKAGE_NAME)
    world_path = os.path.join(
        package_share, "gazebo", "worlds", "uav_safety_demo.world"
    )
    model_path = os.path.join(package_share, "gazebo", "models")
    existing_model_path = os.environ.get("GAZEBO_MODEL_PATH", "")
    gazebo_model_path = model_path
    if existing_model_path:
        gazebo_model_path = model_path + os.pathsep + existing_model_path
    safety_limits_path = os.path.join(package_share, "config", "safety_limits.json")
    scenario = LaunchConfiguration("scenario")
    model_name = LaunchConfiguration("model_name")
    command_period_s = LaunchConfiguration("command_period_s")

    return LaunchDescription(
        [
            DeclareLaunchArgument("scenario", default_value="geofence_violation"),
            DeclareLaunchArgument("model_name", default_value="safety_uav"),
            DeclareLaunchArgument("command_period_s", default_value="0.5"),
            SetEnvironmentVariable("GAZEBO_MODEL_PATH", gazebo_model_path),
            SetEnvironmentVariable("GAZEBO_MASTER_URI", _gazebo_master_uri()),
            SetEnvironmentVariable("UAV_RUNTIME_MONITOR_ROOT", package_share),
            ExecuteProcess(
                cmd=["gzserver", "--verbose", world_path],
                output="screen",
            ),
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package=PACKAGE_NAME,
                        executable="gazebo_state_bridge",
                        name="gazebo_state_bridge_node",
                        output="screen",
                        parameters=[{"model_name": model_name}],
                    ),
                    Node(
                        package=PACKAGE_NAME,
                        executable="safety_monitor",
                        name="safety_monitor_node",
                        output="screen",
                        parameters=[{"safety_limits_path": safety_limits_path}],
                    ),
                    Node(
                        package=PACKAGE_NAME,
                        executable="mission_supervisor",
                        name="mission_supervisor_node",
                        output="screen",
                    ),
                ],
            ),
            TimerAction(
                period=8.0,
                actions=[
                    Node(
                        package=PACKAGE_NAME,
                        executable="gazebo_mission_commander",
                        name="gazebo_mission_commander_node",
                        output="screen",
                        parameters=[
                            {
                                "model_name": model_name,
                                "scenario": scenario,
                                "command_period_s": command_period_s,
                            }
                        ],
                    )
                ],
            ),
        ]
    )
