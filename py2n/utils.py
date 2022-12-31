"""Utitility functions for communication with 2N devices."""
from __future__ import annotations

import logging
import aiohttp

from typing import Any

from .const import CONNECT_ERRORS, HTTP_CALL_TIMEOUT, API_SYSTEM_INFO, API_SYSTEM_STATUS

from .model import Py2NConnectionData

from .exceptions import DeviceConnectionError, InvalidAuthError

_LOGGER = logging.getLogger(__name__)


async def get_info(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> dict[str, Any]:
    """Get info from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_INFO}",
            raise_for_status=True,
            timeout=HTTP_CALL_TIMEOUT,
        ) as response:
            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err

    return result["result"]


async def get_status(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> dict[str, Any]:
    """Get status from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_STATUS}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth if options.username is not None else None,
        ) as response:
            if response.status != 200:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err

    return result["result"]
