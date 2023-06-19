"""Utitility functions for communication with 2N devices."""
from __future__ import annotations

import logging
import aiohttp
import asyncio

from typing import Any, List

from .const import (
    HTTP_CALL_TIMEOUT,
    CONTENT_TYPE,
    API_SYSTEM_INFO,
    API_SYSTEM_STATUS,
    API_SYSTEM_RESTART,
    API_SWITCH_CAPS,
    API_SWITCH_STATUS,
    API_SWITCH_CONTROL,
    API_AUDIO_TEST,
)

from .model import Py2NConnectionData

from .exceptions import (
    DeviceConnectionError,
    DeviceUnsupportedError,
    ApiError,
    DeviceApiError,
)

_LOGGER = logging.getLogger(__name__)


async def get_info(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> dict[str, Any]:
    """Get info from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"http://{options.host}{API_SYSTEM_INFO}"
        )
    except DeviceApiError as err:
        raise

    return result


async def get_status(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> dict[str, Any]:
    """Get status from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"http://{options.host}{API_SYSTEM_STATUS}"
        )
    except DeviceApiError as err:
        raise

    return result


async def restart(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Restart device through REST call."""
    try:
        await api_request(
            aiohttp_session, options, f"http://{options.host}{API_SYSTEM_RESTART}"
        )
    except DeviceApiError as err:
        raise


async def test_audio(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Test device audio through REST call."""
    try:
        await api_request(
            aiohttp_session, options, f"http://{options.host}{API_AUDIO_TEST}"
        )
    except DeviceApiError as err:
        raise


async def get_switches(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> List[Any]:
    """Get switches from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"http://{options.host}{API_SWITCH_STATUS}"
        )
    except DeviceApiError as err:
        # some devices don't offer switches
        if err.error == ApiError.NOT_SUPPORTED:
            return []
        raise

    return result["switches"]

async def get_switch_caps(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> List[Any]:
    """Get switch caps from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"http://{options.host}{API_SWITCH_CAPS}"
        )
    except DeviceApiError as err:
        # some devices don't offer switches
        if err.error == ApiError.NOT_SUPPORTED:
            return []
        raise

    return result["switches"]


async def set_switch(
    aiohttp_session: aiohttp.ClientSession,
    options: Py2NConnectionData,
    switch_id: int,
    on: bool,
) -> None:
    """Set switch value of device via REST call."""
    try:
        await api_request(
            aiohttp_session,
            options,
            f"http://{options.host}{API_SWITCH_CONTROL}?switch={switch_id}&action={'on' if on else 'off'}",
        )
    except DeviceApiError as err:
        raise


async def api_request(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData, url: str
) -> dict[str, Any] | None:
    """Perform REST call to device."""
    try:
        response = await aiohttp_session.get(
            url, timeout=HTTP_CALL_TIMEOUT, auth=options.auth
        )
        if response.content_type != CONTENT_TYPE:
            raise DeviceUnsupportedError("invalid content type")

        result: dict[str, Any] = await response.json()
    except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectionError) as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: connect error: %r", options.host, error)
        raise error from err

    if "success" not in result:
        error = DeviceUnsupportedError("response malformed")
        _LOGGER.debug("host %s: api error: %r", options.host, error)
        raise error

    if not result["success"]:
        code = result["error"]["code"]
        try:
            error = ApiError(code)
            if error == ApiError.INSUFFICIENT_PRIVILEGES and not options.auth:
                error = ApiError.AUTHORIZATION_REQUIRED

            err = DeviceApiError(error)
        except ValueError:
            err = DeviceUnsupportedError("invalid error code")

        _LOGGER.debug("host %s: api error: %r", options.host, err)
        raise err

    if "result" in result:
        return result["result"]
