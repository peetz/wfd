"""WFD update notifications."""

try:
    from homeassistant.helpers.dispatcher import async_dispatcher_send
except ModuleNotFoundError:
    def async_dispatcher_send(*args, **kwargs):
        """Test fallback when Home Assistant is unavailable."""
        return None


SIGNAL_WFD_UPDATED = "wfd_updated"


def async_signal_update(hass):
    """Notify WFD entities that data changed."""
    async_dispatcher_send(hass, SIGNAL_WFD_UPDATED)
