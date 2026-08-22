"""Config flow for WFD."""

from homeassistant import config_entries

DOMAIN = "wfd"


class WFDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a WFD config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create a WFD config entry."""
        if user_input is not None:
            return self.async_create_entry(
                title="What's For Dinner",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=None,
        )
