import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import DOMAIN, DATA_UPDATED, SCAN_INTERVAL, CONF_SERVICES_LIST
from .manager import Manager
from .service import Service, Services

_LOGGER = logging.getLogger(__name__)

class Worker(object):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self.config_entry = config_entry
        self.unsub_timer = None
        self._is_block = False

        self._manager = Manager()
        self._services = Services()

    @property
    def manager(self) -> Manager:
        return self._manager

    @property
    def scan_interval(self) -> int:
        return self.config_entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    @property
    def services(self) -> list:
        return self._services

    async def async_update(self) -> None:
        if self._is_block:
            return

        self._is_block = True

        selected = self.config_entry.options.get(CONF_SERVICES_LIST, [])

        current_services = []
        services = self._manager.list()
        for service_name in services:
            if service_name not in selected:
                if self.services.has(service_name):
                    await self.services.get(service_name).deactivate()

                continue

            current_services.append(service_name)

            if self.services.has(service_name):
                await self.services.get(service_name).update_state(services[service_name])

                continue

            await self.services.async_append(Service(service_name, services[service_name], self.manager))

        for service in self.services.list:
            if service not in current_services:
                await self.services.list[service].deactivate()

        async_dispatcher_send(self.hass, DATA_UPDATED)

        self._is_block = False

    async def async_setup(self) -> bool:
        _LOGGER.debug("Systemd Manager async setup")

        self.set_scan_interval()
        self.config_entry.add_update_listener(self.async_options_updated)

        for domain in ['switch']:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(self.config_entry, domain)
            )

        return True

    def set_scan_interval(self) -> None:
        async def refresh(event_time):
            await self.async_update()

        if self.unsub_timer is not None:
            self.unsub_timer()

        self.unsub_timer = async_track_time_interval(
            self.hass, refresh, timedelta(seconds = self.scan_interval)
        )

    @staticmethod
    async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
        hass.data[DOMAIN].set_scan_interval()