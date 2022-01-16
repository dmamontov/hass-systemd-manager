import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry

from .core.const import (
    DOMAIN,
    CONF_MODE,
    SERVICE_START,
    SERVICE_STOP,
    SERVICE_RESTART,
    SERVICE_ENABLE,
    SERVICE_DISABLE,
    ATTR_UNIT_NAME
)
from .core.worker import Worker
from .core.manager import Mode

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    await async_init_services(hass)

    if DOMAIN not in config:
        return True

    if DOMAIN in hass.data:
        return False

    hass.data.setdefault(DOMAIN, {})

    hass.async_create_task(hass.config_entries.flow.async_init(
        DOMAIN, context = {'source': SOURCE_IMPORT}, data = config
    ))

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    if config_entry.data:
        hass.config_entries.async_update_entry(config_entry, data = {} , options = config_entry.data)

    worker = Worker(hass, config_entry)

    hass.data.setdefault(DOMAIN, worker)

    if not await worker.async_setup():
        return False

    return True

async def async_init_services(hass: HomeAssistant) -> None:
    async def service_start(service_call: ServiceCall) -> None:
        await async_call_action(hass, SERVICE_START, dict(service_call.data))

    async def service_stop(service_call: ServiceCall) -> None:
        await async_call_action(hass, SERVICE_STOP, dict(service_call.data))

    async def service_restart(service_call: ServiceCall) -> None:
        await async_call_action(hass, SERVICE_RESTART, dict(service_call.data))

    async def service_enable(service_call: ServiceCall) -> None:
        await async_call_action(hass, SERVICE_ENABLE, dict(service_call.data))

    async def service_disable(service_call: ServiceCall) -> None:
        await async_call_action(hass, SERVICE_DISABLE, dict(service_call.data))

    hass.services.async_register(DOMAIN, SERVICE_START, service_start)
    hass.services.async_register(DOMAIN, SERVICE_STOP, service_stop)
    hass.services.async_register(DOMAIN, SERVICE_RESTART, service_restart)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE, service_enable)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE, service_disable)

async def async_call_action(hass: HomeAssistant, action: str, data: dict) -> None:
    entities = data.pop('entity_id', None)

    if not entities:
        return

    mode = data.pop(CONF_MODE, None)
    if mode:
        mode = Mode[mode]

    manager = hass.data[DOMAIN].manager

    for entity_id in entities:
        state = hass.states.get(entity_id)
        if not state:
            continue

        unit_name = state.attributes[ATTR_UNIT_NAME]

        if action == SERVICE_START:
            manager.start(unit_name, mode)
            return

        if action == SERVICE_STOP:
            manager.stop(unit_name, mode)
            return

        if action == SERVICE_RESTART:
            manager.restart(unit_name, mode)
            return

        if action == SERVICE_ENABLE:
            manager.enable(unit_name)
            return

        if action == SERVICE_DISABLE:
            manager.disable(unit_name)
            return