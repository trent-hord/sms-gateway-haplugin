"""SMS Gateway platform for notify component."""

from __future__ import annotations

import copy
import logging
from typing import Any
from urllib.parse import urlencode

import requests

from homeassistant.components.notify import (
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_DEFAULT_TARGET,
    CONF_HEADERS,
    CONF_MESSAGE_KEY,
    CONF_METHOD,
    CONF_PAYLOAD,
    CONF_TARGET_KEY,
    CONF_URL,
    DEFAULT_MESSAGE_KEY,
    DEFAULT_METHOD,
    DEFAULT_TARGET_KEY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> SmsGatewayNotificationService | None:
    """Get the SMS Gateway notification service."""
    if discovery_info is None:
        return None

    # Try fetching config from hass.data if discovery_info does not contain it directly
    entry_id = discovery_info.get("entry_id")
    if entry_id and entry_id in hass.data.get(DOMAIN, {}):
        service_config = hass.data[DOMAIN][entry_id]
    else:
        service_config = discovery_info

    return SmsGatewayNotificationService(hass, service_config)


class SmsGatewayNotificationService(BaseNotificationService):
    """Implement the notification service for SMS Gateway."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the service."""
        self._hass = hass
        self._url = config[CONF_URL]
        self._method = config.get(CONF_METHOD, DEFAULT_METHOD)
        self._headers = config.get(CONF_HEADERS, {})
        self._base_payload = config.get(CONF_PAYLOAD, {})
        self._target_key = config.get(CONF_TARGET_KEY, DEFAULT_TARGET_KEY)
        self._message_key = config.get(CONF_MESSAGE_KEY, DEFAULT_MESSAGE_KEY)
        self._default_target = config.get(CONF_DEFAULT_TARGET)

    def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""

        targets = kwargs.get(ATTR_TARGET)
        if not targets and self._default_target:
            targets = [self._default_target]
        elif not targets:
            _LOGGER.error("No targets specified and no default target configured")
            return

        for target in targets:
            payload = copy.deepcopy(self._base_payload)

            def set_nested_value(d: dict, keys: list[str], val: Any) -> None:
                for key in keys[:-1]:
                    d = d.setdefault(key, {})
                # If target key expects an array (like capcom6/android-sms-gateway phoneNumbers),
                # check if it already exists to append, or wrap it in a list.
                # However, for full compatibility we handle lists explicitly if the user configuration provides a list.
                # The easiest way to deal with nested keys is splitting by "."
                d[keys[-1]] = val

            target_keys = self._target_key.split(".")
            message_keys = self._message_key.split(".")

            # Check if the target key refers to an array element or requires array wrapping.
            # Many APIs (including capcom6/android-sms-gateway) use 'phoneNumbers' array.
            # For simplicity, if the user configures target_key="phoneNumbers", we will set it to [target].

            # Since users might define payload template {"phoneNumbers": []},
            # let's be smart: if the current value at target_key is a list, append/set it.
            def get_nested_value(d: dict, keys: list[str]) -> Any:
                for key in keys:
                    if not isinstance(d, dict) or key not in d:
                        return None
                    d = d[key]
                return d

            current_target_val = get_nested_value(payload, target_keys)
            if isinstance(current_target_val, list):
                set_nested_value(payload, target_keys, [target])
            else:
                # If target key is phoneNumbers we will automatically wrap it, as a common heuristic.
                if target_keys[-1] == "phoneNumbers":
                    set_nested_value(payload, target_keys, [target])
                else:
                    set_nested_value(payload, target_keys, target)

            set_nested_value(payload, message_keys, message)

            try:
                if self._method.upper() == "GET":
                    # GET params don't support deeply nested JSON well natively in requests,
                    # but typically GET APIs are flat.
                    response = requests.get(self._url, params=payload, headers=self._headers, timeout=10)
                else:
                    response = requests.post(self._url, json=payload, headers=self._headers, timeout=10)

                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                _LOGGER.error("Error sending SMS via gateway: %s", err)
                raise HomeAssistantError(f"Error communicating with SMS Gateway: {err}") from err
