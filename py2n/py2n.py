from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from typing import Any

import aiohttp

from .const import (
    CONNECT_ERRORS,
    HTTP_CALL_TIMEOUT,
    API_SYSTEM_INFO,
    API_SYSTEM_STATUS
)

from .exceptions import Py2NError, DeviceConnectionError, InvalidAuthError, NotInitialized

_LOGGER = logging.getLogger(__name__)

@dataclass
class ConnectionOptions:
    """Options for 2N device connection."""

    ip_address: str
    username: str | None = None
    password: str | None = None
    auth: aiohttp.BasicAuth | None = None

    def __post_init__(self) -> None:
        """Call after initialization."""
        if self.username is not None:
            if self.password is None:
                raise ValueError("Supply both username and password")
            
            object.__setattr__(self, "auth", aiohttp.BasicAuth(self.username, self.password))

class Py2NDevice:
    def __init__(
        self,
        aiohttp_session,
        options: ConnectionOptions
    ):
        """Device init."""
        self.aiohttp_session: aiohttp.ClientSession = aiohttp_session
        self.options = options
        self._info: dict[str, Any] | None = None
        self._status: dict[str, Any] | None = None
        self._initializing: bool = False
        self._last_error: Py2NError | None = None
        self.initialized: bool = False
    
    @classmethod
    async def create(
        cls,
        aiohttp_session: aiohttp.ClientSession,
        options: ConnectionOptions
    ) -> Py2NDevice:
        """Device creation."""
        instance = cls(aiohttp_session, options)
        await instance.initialize()
        return instance

    async def initialize(self) -> None:
        """Device initialization."""
        if self._initializing:
            raise RuntimeError("Already initializing")
        
        self._initializing = True
        self.initialized = False
        ip = self.options.ip_address

        try:
            self._info = await get_info(self.aiohttp_session, self.options)
            self._status = await get_status(self.aiohttp_session, self.options)
        except InvalidAuthError as err:
            self._last_error = err
            _LOGGER.debug("host %s: error: %r", ip, self._last_error)
            raise
        except CONNECT_ERRORS as err:
            self._last_error = DeviceConnectionError(err)
            _LOGGER.debug("host %s: error: %r", ip, self._last_error)
            raise DeviceConnectionError(err) from err
        finally:
            self.initialized = True
            self._initializing = False

    @property
    def ip_address(self) -> str:
        """Device ip address."""
        return self.options.ip_address
    
    @property
    def info(self) -> str:
        """Get device info."""
        if not self.initialized:
            raise NotInitialized

        return self._info

    @property
    def status(self) -> str:
        """Get device status."""
        if not self.initialized:
            raise NotInitialized

        if self._status is None:
            raise InvalidAuthError

        return self._status

async def get_info(
    aiohttp_session: aiohttp.ClientSession, options: ConnectionOptions
) -> dict[str, Any]:
    """Get info from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_INFO}",
            raise_for_status=True,
            timeout=HTTP_CALL_TIMEOUT
        ) as response:
            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err

    return result['result']

async def get_status(
    aiohttp_session: aiohttp.ClientSession, options: ConnectionOptions
) -> dict[str, Any]:
    """Get status from device through REST call."""
    try:
        async with aiohttp_session.get(
            f"http://{options.ip_address}{API_SYSTEM_STATUS}",
            timeout=HTTP_CALL_TIMEOUT,
            auth=options.auth if options.username is not None else None
        ) as response:
            if response.status != 200:
                raise InvalidAuthError("auth missing and required")

            result: dict[str, Any] = await response.json()
    except CONNECT_ERRORS as err:
        error = DeviceConnectionError(err)
        _LOGGER.debug("host %s: error: %r", options.ip_address, error)
        raise error from err

    return result['result']