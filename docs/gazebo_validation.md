# Gazebo Integration Validation

The Gazebo extension is validated as a runtime-monitoring pipeline, not as a flight-dynamics simulator.

The validation checks that:

- Gazebo publishes model states through `gazebo_ros_state`,
- the bridge converts Gazebo `/model_states` into the project `/uav/state` topic,
- the safety monitor detects the expected scenario violation,
- the mission supervisor publishes the expected response mode,
- the Gazebo commander inserts the response trajectory.

The demo runners assign a unique `GAZEBO_MASTER_URI` for each run so validation does not accidentally attach to an already-running Gazebo instance.

For the default `geofence_violation` scenario, the expected sequence is:

```text
GEOFENCE_WARNING
GEOFENCE_VIOLATION
RETURN_TO_HOME
RETURNING_HOME
RESPONSE_RETURN_HOME
RESPONSE_LANDING
RESPONSE_COMPLETE
```

Run the automated headless check:

```bash
./gazebo_extension/run_headless_demo.sh
```

The script now calls:

```bash
python3 analysis/validate_gazebo_logs.py <log_dir> --scenario geofence_violation
```

A passing run prints:

```text
Gazebo integration validation: PASS
```

This gives the repository a repeatable integration test for the Gazebo/ROS2 safety-monitoring path while keeping the full PX4/ArduPilot SITL integration as a later step.
