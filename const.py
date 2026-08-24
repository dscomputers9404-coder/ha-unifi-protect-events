DOMAIN = "unifi_protect_events"
CONF_VERIFY_SSL = "verify_ssl"
DEFAULT_VERIFY_SSL = False
PLATFORMS = ["sensor", "event", "camera"]

API_BASE = "/proxy/protect/integration/v1"
CAMERAS_PATH = f"{API_BASE}/cameras"
EVENTS_WS_PATH = f"{API_BASE}/subscribe/events"

DATA_CLIENT = "client"
DATA_STORE = "store"
DATA_TASK = "task"

MAX_EVENTS = 50
RECENT_CAMERA_SLOTS = 8

# Merge generic motion with a smart detection from the same camera
# when Protect sends both events close together.
EVENT_MERGE_WINDOW_SECONDS = 5
SMART_DETECTION_TYPES = {
    "person", "vehicle", "animal", "package", "face", "licensePlate",
}

SUPPORTED_EVENT_TYPES = {
    "person", "vehicle", "animal", "package",
    "face", "licensePlate", "ring", "motion", "smartDetectZone",
}
