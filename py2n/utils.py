"""Utitility functions for communication with 2N devices."""
from __future__ import annotations

import logging
import aiohttp

from typing import Any, List

from .const import (
    CONNECT_ERRORS,
    HTTP_CALL_TIMEOUT,
    API_SYSTEM_INFO,
    API_SYSTEM_STATUS,
    API_SYSTEM_RESTART,
    API_SWITCH_STATUS,
    API_SWITCH_CONTROL,
    API_AUDIO_TEST,
)

from .model import Py2NConnectionData

from .exceptions import Py2NError, DeviceConnectionError, InvalidAuthError

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

    if not result["success"]:
        raise Py2NError("request unsucessful")

    return result["result"]


async def get_status(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> dict[str, Any]:
    """Get status from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_STATUS}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth,
        ) as response:
            if response.status == 401:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err
    except InvalidAuthError as err:
        _LOGGER.debug("host %s: error: %r", options, error)
        raise

    if not result["success"]:
        raise Py2NError("request unsucessful")

    return result["result"]


async def restart(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Restart device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_RESTART}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth,
        ) as response:
            if response.status == 401:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err
    except InvalidAuthError as err:
        _LOGGER.debug("host %s: error: %r", options, error)
        raise

    if not result["success"]:
        raise Py2NError("request unsucessful")


async def get_switches(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> List[Any]:
    """Get switches from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SWITCH_STATUS}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth,
        ) as response:
            if response.status == 401:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err
    except InvalidAuthError as err:
        _LOGGER.debug("host %s: error: %r", options, error)
        raise

    if not result["success"]:
        raise Py2NError("request unsucessful")

    return result["result"]["switches"]


async def test_audio(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Test device audio through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_AUDIO_TEST}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth,
        ) as response:
            if response.status == 401:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err
    except InvalidAuthError as err:
        _LOGGER.debug("host %s: error: %r", options, error)
        raise

    if not result["success"]:
        raise Py2NError("request unsucessful")


async def set_switch(
    aiohttp_session: aiohttp.ClientSession,
    options: Py2NConnectionData,
    switch_id: int,
    on: bool,
) -> List[Any]:
    """Set switch value of device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SWITCH_CONTROL}?switch={switch_id}&action={'on' if on else 'off'}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth,
        ) as response:
            if response.status == 401:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err
    except InvalidAuthError as err:
        _LOGGER.debug("host %s: error: %r", options, error)
        raise

    if not result["success"]:
        raise Py2NError("request unsucessful")
