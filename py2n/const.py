"""Constants for 2N library."""
import asyncio
import aiohttp

CONNECT_ERRORS = (aiohttp.ClientError, asyncio.TimeoutError, OSError)

HTTP_CALL_TIMEOUT = 10
CONTENT_TYPE = "application/json"

API_SYSTEM_INFO = "/api/system/info"
API_SYSTEM_STATUS = "/api/system/status"
API_SYSTEM_RESTART = "/api/system/restart"
API_SWITCH_STATUS = "/api/switch/status"
API_SWITCH_CONTROL = "/api/switch/ctrl"
API_AUDIO_TEST = "/api/audio/test"