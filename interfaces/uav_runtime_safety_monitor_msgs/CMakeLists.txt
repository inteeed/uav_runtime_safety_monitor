cmake_minimum_required(VERSION 3.5)
project(uav_runtime_safety_monitor_msgs)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/UAVState.msg"
  "msg/SafetyStatus.msg"
  "msg/SupervisorResponse.msg"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
