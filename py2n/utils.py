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
    API_IO_CAPS,
    API_IO_CONTROL,
    API_IO_STATUS,
    API_AUDIO_TEST,
    API_LOG_CAPS,
    API_LOG_SUBSCRIBE,
    API_LOG_UNSUBSCRIBE,
    API_LOG_PULL,
)

from .model import Py2NConnectionData, Py2NDevicePort

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
            aiohttp_session, options, f"{API_SYSTEM_INFO}"
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
            aiohttp_session, options, f"{API_SYSTEM_STATUS}"
        )
    except DeviceApiError as err:
        raise

    return result

async def get_log_caps(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> List[str]:
    """Get log caps from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"{API_LOG_CAPS}"
        )
    except DeviceApiError as err:
        # some devices don't offer switches
        if err.error == ApiError.NOT_SUPPORTED:
            return []
        raise

    return result["events"]

async def log_subscribe(
    aiohttp_session: aiohttp.ClientSession,
    options: Py2NConnectionData,
    include: str,
    filter: list[str],
    duration: int,
) -> int:
    """Subscribe to log events REST call."""
    filterstring = "" if filter is None else ",".join(filter)
    filterarg = "" if filterstring == "" else f"&filter={filterstring}"
    try:
        result = await api_request(
            aiohttp_session,
            options,
            f"{API_LOG_SUBSCRIBE}?include={include}&duration={duration}{filterarg}",
        )
    except DeviceApiError as err:
        raise
    
    return result["id"]

async def log_unsubscribe(
    aiohttp_session: aiohttp.ClientSession,
    options: Py2NConnectionData,
    id: int,
) -> None:
    """Unubscribe to log events REST call."""
    try:
        await api_request(
            aiohttp_session,
            options,
            f"{API_LOG_UNSUBSCRIBE}?id={id}",
        )
    except DeviceApiError as err:
        raise

async def log_pull(
    aiohttp_session: aiohttp.ClientSession,
    options: Py2NConnectionData,
    id: int,
    timeout: int=0,
) -> list[dict]:
    """Pull log events REST call."""
    try:
        result = await api_request(
            aiohttp_session,
            options,
            f"{API_LOG_PULL}?id={id}&timeout={timeout}",
            timeout+5
        )
    except DeviceApiError as err:
        raise
    
    return result["events"]


async def restart(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Restart device through REST call."""
    try:
        await api_request(
            aiohttp_session, options, f"{API_SYSTEM_RESTART}"
        )
    except DeviceApiError as err:
        raise


async def test_audio(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> None:
    """Test device audio through REST call."""
    try:
        await api_request(
            aiohttp_session, options, f"{API_AUDIO_TEST}"
        )
    except DeviceApiError as err:
        raise


async def get_switches(
    aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
) -> List[Any]:
    """Get switches from device through REST call."""
    try:
        result = await api_request(
            aiohttp_session, options, f"{API_SWITCH_STATUS}"
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
            aiohttp_session, options, f"{API_SWITCH_CAPS}"
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
            f"{API_SWITCH_CONTROL}?switch={switch_id}&action={'on' if on else 'off'}",
        )
    except DeviceApiError as err:
        raise

async def get_port_caps(aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData) ->  list[dict]:
    try:
        result = await api_request(
            aiohttp_session,
            options,
            f"{API_IO_CAPS}"
        )
    except DeviceApiError as err:
        raise

    return result["ports"]

async def get_port_status(aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData) ->  list[dict]:
    try:
        result = await api_request(
            aiohttp_session,
            options,
            f"{API_IO_STATUS}"
        )
    except DeviceApiError as err:
        raise

    return result["ports"]

async def get_ports(aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData) ->  list[Py2NDevicePort]:
    caps = await get_port_caps(aiohttp_session, options)
    statuses = await get_port_status(aiohttp_session, options)
    ports = []
    for cap in caps:
        for status in statuses:
            if status["port"] == cap["port"]:
                ports.append(Py2NDevicePort(cap["port"], cap["type"], status["state"]))
                break
    return ports

async def set_port(aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData, port_id: str, on: bool) -> None:
    try:
        await api_request(
            aiohttp_session,
            options,
            f"{API_IO_CONTROL}?port={port_id}&action={'on' if on else 'off'}",
        )
    except DeviceApiError as err:
        raise

async def api_request(
        aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData, endpoint: str, timeout: int = HTTP_CALL_TIMEOUT
) -> dict[str, Any] | None:
    """Perform REST call to device."""

    url=f"{options.protocol}://{options.host}{endpoint}"
    try:
        response = await aiohttp_session.get(
            url, timeout=timeout, auth=options.auth, ssl=False
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
        _LOGGER.debug("host %s: api unsuccessfull: %r", options.host, result)
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
