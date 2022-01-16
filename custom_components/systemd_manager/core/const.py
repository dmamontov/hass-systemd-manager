DOMAIN = "systemd_manager"

SCAN_INTERVAL = 10
DATA_UPDATED = "systemd_manager_data_updated"

UNIT_INTERFACE = "org.freedesktop.systemd1.Unit"
SERVICE_UNIT_INTERFACE = "org.freedesktop.systemd1.Service"

CONF_SERVICES_LIST = "services"
CONF_MODE = "mode"

ATTR_UNIT_NAME = "unit_name"
ATTR_REAL_STATE = "real_state"
ATTR_TYPE = "type"
ATTR_EXIT_CODE = "exit_code"
ATTR_LAST_ACTIVITY = "last_activity"
ATTR_TRIGGERED_BY = "triggered_by"

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_RESTART = "restart"
SERVICE_ENABLE = "enable"
SERVICE_DISABLE = "disable"