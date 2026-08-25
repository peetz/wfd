"""Config flow for WFD."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "wfd"
DEFAULT_MEALS_REQUIRED = 1
DEFAULT_DEADLINE_MINUTES = 1440


class WFDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a WFD config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create a WFD config entry with voting defaults."""
        if user_input is not None:
            return self.async_create_entry(
                title="What's For Dinner",
                data={
                    "default_meals_required": user_input["default_meals_required"],
                    "default_deadline_minutes": user_input["default_deadline_minutes"],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(
                    "default_meals_required",
                    default=DEFAULT_MEALS_REQUIRED,
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    "default_deadline_minutes",
                    default=DEFAULT_DEADLINE_MINUTES,
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }),
        )
