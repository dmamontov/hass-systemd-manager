import logging

import homeassistant.helpers.device_registry as dr

from homeassistant.core import HomeAssistant, callback
from homeassistant.util import slugify
from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .core.const import DOMAIN, DATA_UPDATED
from .core.service import Service

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities) -> None:
    worker = hass.data[DOMAIN]

    @callback
    def update_services() -> None:
        if len(worker.services.list) == 0:
            return

        new_services = []
        for name in worker.services.list:
            service = worker.services.get(name)
            if service is None or service.is_added:
                continue

            service.add()

            _LOGGER.debug("Systemd Manager update {}".format(name))

            new_services.append(SystemdSwitch(hass, service))

        if len(new_services) > 0:
            async_add_entities(new_services)

    async_dispatcher_connect(
        hass, DATA_UPDATED, update_services
    )

class SystemdSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, service: Service) -> None:
        self.hass = hass
        self.service = service
        self.unsub_update = None

        self._unique_id = "systemd_ " + ENTITY_ID_FORMAT.format(slugify(service.name.lower()))
        self._name = self.service.name
        self._is_available = self.service.is_available
        self._is_on = self.service.is_on
        self._extra = self.service.extra

        self.entity_id = f"{DOMAIN}.{self._unique_id}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def icon(self) -> str:
        return 'mdi:radiobox-marked' if self.is_on else 'mdi:radiobox-blank'

    @property
    def available(self) -> bool:
        return self._is_available

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict:
        return self._extra

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self) -> None:
        self.unsub_update = async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self) -> None:
        self.async_schedule_update_ha_state(True)

    async def will_remove_from_hass(self) -> None:
        if self.unsub_update:
            self.unsub_update()

        self.unsub_update = None

    async def async_update(self) -> None:
        self._is_available = self.service.is_available
        self._is_on = self.service.is_on
        self._extra = self.service.extra

    async def async_turn_on(self, **kwargs) -> None:
        await self.service.update_state('wait-on', True)
        await self.service.start()

    async def async_turn_off(self, **kwargs) -> None:
        await self.service.update_state('wait-off', True)
        await self.service.stop()
