# Project Plan

## Goal

Build a small runtime safety-monitoring prototype for autonomous UAV missions. The first version should be simple, runnable, and directly relevant to safe UAV autonomy work.

## Phase 1: Basic Python Simulation

Deliverables:

- waypoint-based mission simulator
- normal mission scenario
- unsafe geofence scenario
- CSV output

## Phase 2: Runtime Safety Monitoring

Deliverables:

- altitude-limit check
- geofence check
- low-battery check
- mission-timeout check
- safety status and recommended action

## Phase 3: Log Analysis

Deliverables:

- mission summary script
- trajectory plot with geofence boundary
- altitude plot
- battery plot
- safety-status plot

## Phase 4: Documentation

Deliverables:

- README
- safety requirements
- architecture diagram
- results images

## Phase 5: ROS2/PX4 Extension

Deliverables:

- ROS2 node skeleton
- `/uav/state` subscriber
- `/uav/safety_status` publisher
- future PX4/Gazebo integration notes

