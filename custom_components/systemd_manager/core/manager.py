import logging
import datetime
import dbus
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

from typing import Optional
from enum import Enum
from .const import UNIT_INTERFACE, SERVICE_UNIT_INTERFACE

_LOGGER = logging.getLogger(__name__)

class Mode(Enum):
    REPLACE = "replace"
    FAIL = "fail"
    ISOLATE = "isolate"
    IGNORE_DEPENDENCIES = "ignore-dependencies"
    IGNORE_REQUIREMENTS = "ignore-requirements"


class Manager(object):
    def __init__(self):
        self._bus = dbus.SystemBus()

    def list(self) -> dict:
        services = {}

        for unit in self._list_units():
            unit_name = str(unit[0]).strip()

            if not unit_name.endswith('.service') or unit_name in services:
                _LOGGER.debug('Systemd Manager {}'.format(unit_name))

                continue

            services[str(unit[0])] = str(unit[4])

        return services

    def start(self, unit_name: str, mode: Mode = Mode.REPLACE) -> bool:
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.StartUnit(unit_name, mode.value)
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

        return True

    def stop(self, unit_name: str, mode: Mode = Mode.REPLACE) -> bool:
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.StopUnit(unit_name, mode.value)
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

        return True

    def restart(self, unit_name: str, mode: Mode = Mode.REPLACE):
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.RestartUnit(unit_name, mode.value)
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

        return True

    def enable(self, unit_name: str) -> bool:
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.EnableUnitFiles([unit_name], dbus.Boolean(False), dbus.Boolean(True))
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

        return True

    def disable(self, unit_name: str) -> bool:
        interface = self._get_interface()

        if interface is None:
            return False

        try:
            interface.DisableUnitFiles([unit_name], dbus.Boolean(False))
        except dbus.exceptions.DBusException as error:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

        return True

    def _get_state(self, unit_name: str, with_error: bool = True) -> Optional[str]:
        interface = self._get_interface()

        if interface is None:
            return None

        try:
            return interface.GetUnitFileState(unit_name)
        except dbus.exceptions.DBusException as e:
            if with_error:
                _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def _list_units(self):
        interface = self._get_interface()

        if interface is None:
            return None

        try:
            return interface.ListUnits()
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def _get_interface(self):
        try:
            obj = self._bus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")

            return dbus.Interface(obj, "org.freedesktop.systemd1.Manager")
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_active_state(self, unit_name: str):
        properties = self.get_unit_properties(unit_name, UNIT_INTERFACE)

        if properties is None:
            return False

        try:
            return properties["ActiveState"].encode("utf-8")
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return False

    def is_active(self, unit_name: str) -> bool:
        return self.get_active_state(unit_name) == b"active"

    def is_failed(self, unit_name: str) -> bool:
        return self.get_active_state(unit_name) == b"failed"

    def is_available(self, unit_name: str) -> bool:
        return self._get_state(unit_name, False) is not None

    def get_error_code(self, unit_name: str) -> Optional[int]:
        service_properties = self.get_unit_properties(unit_name, SERVICE_UNIT_INTERFACE)

        if service_properties is None:
            return None

        return self.get_exec_status(service_properties)

    def get_exec_status(self, properties: Optional[dict] = None) -> Optional[int]:
        try:
            return int(properties["ExecMainStatus"])
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_type(self, properties: Optional[dict] = None) -> Optional[str]:
        try:
            return str(properties["Type"])
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_last_activity(self, properties: Optional[dict] = None) -> Optional[str]:
        try:
            return datetime.datetime \
                .utcfromtimestamp(int(properties["StateChangeTimestamp"]) / 1000000) \
                .strftime('%Y-%m-%d %H:%M:%S')
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_triggered_by(self, properties: Optional[dict] = None) -> Optional[str]:
        try:
            return ', '.join(list(properties["TriggeredBy"]))
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_result(self, properties: Optional[dict] = None) -> Optional[str]:
        try:
            return properties["Result"].encode("utf-8")
        except KeyError as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None

    def get_unit_properties(self, unit_name: str, unit_interface):
        interface = self._get_interface()

        if interface is None:
            return None

        try:
            unit_path = interface.LoadUnit(unit_name)
            obj = self._bus.get_object("org.freedesktop.systemd1", unit_path)

            properties_interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")

            return properties_interface.GetAll(unit_interface)
        except dbus.exceptions.DBusException as e:
            _LOGGER.error('Systemd Manager (DBus): %r', e)

            return None