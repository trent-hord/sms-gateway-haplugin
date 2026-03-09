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
    CONF_USERNAME,
    CONF_PASSWORD,
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
        self._username = config.get(CONF_USERNAME)
        self._password = config.get(CONF_PASSWORD)

    def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""

        targets = kwargs.get(ATTR_TARGET)
        if not targets and self._default_target:
            targets = [self._default_target]
        elif not targets:
            _LOGGER.error("No targets specified and no default target configured")
            return

        payload = copy.deepcopy(self._base_payload)

        def set_nested_value(d: dict, keys: list[str], val: Any) -> None:
            for key in keys[:-1]:
                d = d.setdefault(key, {})
            d[keys[-1]] = val

        target_keys = self._target_key.split(".")
        message_keys = self._message_key.split(".")

        def get_nested_value(d: dict, keys: list[str]) -> Any:
            for key in keys:
                if not isinstance(d, dict) or key not in d:
                    return None
                d = d[key]
            return d

        current_target_val = get_nested_value(payload, target_keys)
        # Many APIs (including capcom6/android-sms-gateway) use 'phoneNumbers' array.
        # Support batching multiple targets into a single request
        if isinstance(current_target_val, list) or target_keys[-1] == "phoneNumbers":
            set_nested_value(payload, target_keys, targets)
            set_nested_value(payload, message_keys, message)
            self._send_payload(payload)
        else:
            for target in targets:
                p = copy.deepcopy(payload)
                set_nested_value(p, target_keys, target)
                set_nested_value(p, message_keys, message)
                self._send_payload(p)

    def _send_payload(self, payload: dict) -> None:
        auth = None
        if self._username and self._password:
            auth = (self._username, self._password)

        try:
            if self._method.upper() == "GET":
                response = requests.get(self._url, params=payload, headers=self._headers, auth=auth, timeout=10)
            else:
                response = requests.post(self._url, json=payload, headers=self._headers, auth=auth, timeout=10)

            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error sending SMS via gateway: %s", err)
            raise HomeAssistantError(f"Error communicating with SMS Gateway: {err}") from err

