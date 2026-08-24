"""WFD update notifications."""

from homeassistant.helpers.dispatcher import async_dispatcher_send

SIGNAL_WFD_UPDATED = "wfd_updated"


def async_signal_update(hass):
    """Notify WFD entities that data changed."""
    async_dispatcher_send(hass, SIGNAL_WFD_UPDATED)
