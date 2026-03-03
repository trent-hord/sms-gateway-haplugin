"""Constants for SMS Gateway."""

from typing import Final

DOMAIN: Final = "sms_gateway"
DATA_HASS_CONFIG: Final = "sms_gateway_hass_config"
DEFAULT_NAME: Final = "SMS Gateway"

CONF_URL: Final = "url"
CONF_METHOD: Final = "method"
CONF_HEADERS: Final = "headers"
CONF_PAYLOAD: Final = "payload"
CONF_TARGET_KEY: Final = "target_key"
CONF_MESSAGE_KEY: Final = "message_key"
CONF_DEFAULT_TARGET: Final = "default_target"

DEFAULT_METHOD: Final = "POST"
DEFAULT_TARGET_KEY: Final = "to"
DEFAULT_MESSAGE_KEY: Final = "message"
