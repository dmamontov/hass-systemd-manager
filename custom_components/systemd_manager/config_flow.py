import logging
import platform

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from .core.const import CONF_SERVICES_LIST, SCAN_INTERVAL
from .core.manager import Manager

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register("systemd_manager")
class SystemdManagerConfigFlow(config_entries.ConfigFlow):
    async def async_step_import(self, user_input = None):
        if self._async_current_entries():
            return self.async_abort(reason = "single_instance_allowed")

        return self.async_create_entry(title = platform.node(), data = {})

    async def async_step_user(self, user_input = None):
        if self._async_current_entries():
            return self.async_abort(reason = "single_instance_allowed")

        options = list(Manager().list().keys())
        options = sorted(options)

        schema = vol.Schema({
            vol.Required(CONF_SERVICES_LIST, default=[]): cv.multi_select(options),
        })

        if user_input:
            return self.async_create_entry(title = platform.node(), data = user_input)

        return self.async_show_form(step_id = "user", data_schema = schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input = None):
        return await self.async_step_settings(user_input)

    async def async_step_settings(self, user_input = None):
        options = list(Manager().list().keys())
        options = sorted(options)

        schema = vol.Schema({
            vol.Required(
                CONF_SERVICES_LIST,
                default=self.config_entry.options.get(CONF_SERVICES_LIST, [])
            ): cv.multi_select(options),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
            ): cv.positive_int,
        })

        if user_input:
            return self.async_create_entry(title = platform.node(), data = user_input)

        return self.async_show_form(step_id = "settings", data_schema = schema)