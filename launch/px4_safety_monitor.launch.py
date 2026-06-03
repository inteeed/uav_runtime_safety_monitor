import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


PACKAGE_NAME = "uav_runtime_safety_monitor"


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory(PACKAGE_NAME)
    safety_limits_path = os.path.join(
        package_share, "config", "px4_live_safety_limits.json"
    )
    local_position_topic = LaunchConfiguration("local_position_topic")
    battery_status_topic = LaunchConfiguration("battery_status_topic")
    publish_period_s = LaunchConfiguration("publish_period_s")
    safety_limits_path_arg = LaunchConfiguration("safety_limits_path")
    raw_state_topic = LaunchConfiguration("raw_state_topic")
    monitor_state_topic = LaunchConfiguration("monitor_state_topic")
    fault_command_topic = LaunchConfiguration("fault_command_topic")
    enable_live_logger = LaunchConfiguration("enable_live_logger")
    live_log_path = LaunchConfiguration("live_log_path")
    live_event_log_path = LaunchConfiguration("live_event_log_path")
    enable_command_bridge = LaunchConfiguration("enable_command_bridge")
    vehicle_command_topic = LaunchConfiguration("vehicle_command_topic")

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
                "raw_state_topic",
                default_value="/uav/raw_state",
                description="Raw PX4-derived UAV state topic before fault injection.",
            ),
            DeclareLaunchArgument(
                "monitor_state_topic",
                default_value="/uav/state",
                description="Safety-monitor UAV state input topic.",
            ),
            DeclareLaunchArgument(
                "fault_command_topic",
                default_value="/uav/fault_injection",
                description="Topic for short live-demo fault injection commands.",
            ),
            DeclareLaunchArgument(
                "safety_limits_path",
                default_value=safety_limits_path,
                description="PX4 live-demo safety limits JSON used by the monitor.",
            ),
            DeclareLaunchArgument(
                "enable_live_logger",
                default_value="true",
                description="Write live PX4 monitor output to CSV logs.",
            ),
            DeclareLaunchArgument(
                "live_log_path",
                default_value="data/px4_live_mission.csv",
                description="CSV file for live state/status/supervisor samples.",
            ),
            DeclareLaunchArgument(
                "live_event_log_path",
                default_value="data/px4_live_events.csv",
                description="CSV file for live safety event transitions.",
            ),
            DeclareLaunchArgument(
                "enable_command_bridge",
                default_value="false",
                description=(
                    "Forward supervisor RTL/Land responses to PX4 as "
                    "VehicleCommands. SITL / test-stand use only."
                ),
            ),
            DeclareLaunchArgument(
                "vehicle_command_topic",
                default_value="/fmu/in/vehicle_command",
                description="PX4 vehicle command input topic.",
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
                        "publish_topic": raw_state_topic,
                        "publish_period_s": publish_period_s,
                    }
                ],
            ),
            Node(
                package=PACKAGE_NAME,
                executable="fault_injection",
                name="fault_injection_node",
                output="screen",
                parameters=[
                    {
                        "input_topic": raw_state_topic,
                        "output_topic": monitor_state_topic,
                        "command_topic": fault_command_topic,
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
            Node(
                package=PACKAGE_NAME,
                executable="safety_console",
                name="safety_console_node",
                output="screen",
                parameters=[
                    {
                        "print_period_s": 1.0,
                        "safety_limits_path": safety_limits_path_arg,
                    }
                ],
            ),
            Node(
                package=PACKAGE_NAME,
                executable="live_log",
                name="live_log_node",
                output="screen",
                condition=IfCondition(enable_live_logger),
                parameters=[
                    {
                        "mission_log_path": live_log_path,
                        "event_log_path": live_event_log_path,
                    }
                ],
            ),
            Node(
                package=PACKAGE_NAME,
                executable="px4_command_bridge",
                name="px4_command_bridge_node",
                output="screen",
                condition=IfCondition(enable_command_bridge),
                parameters=[
                    {
                        "enable_commands": True,
                        "command_topic": vehicle_command_topic,
                        "supervisor_topic": "/uav/supervisor_mode",
                    }
                ],
            ),
        ]
    )
