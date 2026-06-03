"""Shared vocabulary for the runtime safety monitor.

These constants are the single source of truth for the status, action,
severity and supervisor-mode strings used across the Python core, the ROS2
nodes and the CSV evidence. The string *values* intentionally match the
literals used historically so logs, plots and message payloads are unchanged;
referencing the constants instead of bare strings just removes the risk of
silent typos.
"""


class SafetyStatus:
    SAFE = "SAFE"
    ALTITUDE_WARNING = "ALTITUDE_WARNING"
    ALTITUDE_LIMIT_VIOLATION = "ALTITUDE_LIMIT_VIOLATION"
    GEOFENCE_WARNING = "GEOFENCE_WARNING"
    GEOFENCE_VIOLATION = "GEOFENCE_VIOLATION"
    VELOCITY_LIMIT_VIOLATION = "VELOCITY_LIMIT_VIOLATION"
    PATH_DEVIATION_WARNING = "PATH_DEVIATION_WARNING"
    PATH_DEVIATION_VIOLATION = "PATH_DEVIATION_VIOLATION"
    LOW_BATTERY = "LOW_BATTERY"
    MISSION_TIMEOUT = "MISSION_TIMEOUT"
    STATE_TIMEOUT = "STATE_TIMEOUT"


class RecommendedAction:
    CONTINUE = "CONTINUE"
    WARNING = "WARNING"
    RETURN_TO_HOME = "RETURN_TO_HOME"
    LAND = "LAND"
    ABORT_MISSION = "ABORT_MISSION"


class Severity:
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ActiveResponse:
    NONE = "NONE"
    MONITOR = "MONITOR"
    RETURN_TO_HOME = "RETURN_TO_HOME"
    LAND = "LAND"
    ABORT_MISSION = "ABORT_MISSION"


class SupervisorMode:
    CONTINUE_MISSION = "CONTINUE_MISSION"
    WARNING_ACTIVE = "WARNING_ACTIVE"
    RETURNING_HOME = "RETURNING_HOME"
    LANDING = "LANDING"
    MISSION_ABORTED = "MISSION_ABORTED"
    RESPONSE_COMPLETE = "RESPONSE_COMPLETE"


class CheckPriority:
    """Relative priority of each rule when several trigger at once.

    The most safety-critical and immediate hazard wins. Hard limit violations
    outrank soft warnings; an altitude limit (risk of fly-away / airspace
    breach) outranks a geofence breach, which outranks slower-developing
    issues such as low battery or mission timeout.
    """

    ALTITUDE_LIMIT = 100
    STATE_TIMEOUT = 95
    GEOFENCE_VIOLATION = 90
    VELOCITY_LIMIT = 88
    LOW_BATTERY = 85
    MISSION_TIMEOUT = 80
    PATH_DEVIATION_VIOLATION = 70
    ALTITUDE_WARNING = 45
    GEOFENCE_WARNING = 40
    PATH_DEVIATION_WARNING = 35
