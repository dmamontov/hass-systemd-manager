import logging

from typing import Optional
from .manager import Manager, Mode
from .const import (
    UNIT_INTERFACE,
    SERVICE_UNIT_INTERFACE,
    ATTR_UNIT_NAME,
    ATTR_REAL_STATE,
    ATTR_TYPE,
    ATTR_EXIT_CODE,
    ATTR_LAST_ACTIVITY,
    ATTR_TRIGGERED_BY,
)

_LOGGER = logging.getLogger(__name__)

class Service(object):
    def __init__(self, name: str, state: str, manager: Manager) -> None:
        self._name: str = name
        self._state: str = state
        self._manager: Manager = manager

        self._is_added: bool = False
        self._is_available: bool = True
        self._is_block: bool = False

        self._extra: dict = self.parse_extra()

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_added(self) -> bool:
        return self._is_added

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def is_on(self) -> bool:
        return self._state in ['running', 'start', 'wait-on']

    @property
    def extra(self) -> dict:
        return {
           ATTR_UNIT_NAME: self.name,
           ATTR_REAL_STATE: self._state
        } | self._extra

    def parse_extra(self) -> dict:
        extra: dict = {}

        service_properties = self._manager.get_unit_properties(self.name, SERVICE_UNIT_INTERFACE)
        if service_properties is not None:
            extra |= {
                ATTR_TYPE: self._manager.get_type(service_properties),
                ATTR_EXIT_CODE: self._manager.get_exec_status(service_properties)
            }

        unit_properties = self._manager.get_unit_properties(self.name, UNIT_INTERFACE)
        if unit_properties is not None:
            extra |= {
                ATTR_LAST_ACTIVITY: self._manager.get_last_activity(unit_properties),
                ATTR_TRIGGERED_BY: self._manager.get_triggered_by(unit_properties)
            }

        return extra

    def add(self) -> None:
        self._is_added = True

    async def stop(self, mode: Mode = Mode.REPLACE) -> bool:
        return self._manager.stop(self.name, mode)

    async def start(self, mode: Mode = Mode.REPLACE) -> bool:
        return self._manager.start(self.name, mode)

    async def update_state(self, state: str, is_block: bool = False) -> None:
        if self._is_block and not is_block:
            self._is_block = False

            return

        if state != self._state:
            self._extra = self.parse_extra()

        self._state = state
        self._is_available = True

        if is_block:
            self._is_block = True

    async def deactivate(self) -> None:
        self._is_available = False

class Services(object):
    def __init__(self) -> None:
        self._services = {}

    @property
    def list(self) -> dict:
        return self._services

    async def async_append(self, service: Service) -> None:
        if service.name not in self._services:
            self._services[service.name] = service

    def get(self, name: str) -> Optional[Service]:
        return self._services[name] if name in self._services else None

    def has(self, name: str) -> bool:
        return name in self._services