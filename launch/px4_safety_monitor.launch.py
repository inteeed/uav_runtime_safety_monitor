import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


PACKAGE_NAME = "uav_runtime_safety_monitor"


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory(PACKAGE_NAME)
    safety_limits_path = os.path.join(package_share, "config", "safety_limits.json")
    local_position_topic = LaunchConfiguration("local_position_topic")
    battery_status_topic = LaunchConfiguration("battery_status_topic")
    publish_period_s = LaunchConfiguration("publish_period_s")
    safety_limits_path_arg = LaunchConfiguration("safety_limits_path")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "local_position_topic",
                default_value="/fmu/out/vehicle_local_position",
                description="PX4 vehicle local position output topic.",
            ),
            DeclareLaunchArgument(
                "battery_status_topic",
                default_value="/fmu/out/battery_status",
                description="PX4 battery status output topic.",
            ),
            DeclareLaunchArgument(
                "publish_period_s",
                default_value="0.1",
                description="Minimum interval between published /uav/state samples.",
            ),
            DeclareLaunchArgument(
                "safety_limits_path",
                default_value=safety_limits_path,
                description="Safety limits JSON used by the monitor.",
            ),
            SetEnvironmentVariable("UAV_RUNTIME_MONITOR_ROOT", package_share),
            Node(
                package=PACKAGE_NAME,
                executable="px4_state_bridge",
                name="px4_state_bridge_node",
                output="screen",
                parameters=[
                    {
                        "local_position_topic": local_position_topic,
                        "battery_status_topic": battery_status_topic,
                        "publish_period_s": publish_period_s,
                    }
                ],
            ),
            Node(
                package=PACKAGE_NAME,
                executable="safety_monitor",
                name="safety_monitor_node",
                output="screen",
                parameters=[{"safety_limits_path": safety_limits_path_arg}],
            ),
            Node(
                package=PACKAGE_NAME,
                executable="mission_supervisor",
                name="mission_supervisor_node",
                output="screen",
            ),
        ]
    )
