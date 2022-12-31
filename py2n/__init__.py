"""Asynchronous python library to control 2N devices."""

from __future__ import annotations

import logging
import aiohttp

from typing import Any
from datetime import datetime, timedelta, timezone
from .const import CONNECT_ERRORS

from .model import Py2NDeviceData, Py2NConnectionData

from .exceptions import (
    NotInitialized,
    Py2NError,
    DeviceConnectionError,
    InvalidAuthError,
)

from .utils import get_info, get_status

_LOGGER = logging.getLogger(__name__)


class Py2NDevice:
    def __init__(self, aiohttp_session, options: Py2NConnectionData):
        """Device init."""
        self.aiohttp_session: aiohttp.ClientSession = aiohttp_session
        self.options = options
        self.data: Py2NDeviceData
        self.initialized: bool = False

        self._info: dict[str, Any] | None = None
        self._status: dict[str, Any] | None = None
        self._initializing: bool = False
        self._last_error: Py2NError | None = None
        

    @classmethod
    async def create(
        cls, aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData
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

        try:
            await self.update()
            self.initialized = True
        finally:
            self._initializing = False

    async def update(self) -> Py2NDeviceData:
        ip = self.options.ip_address

        try:
            self._info = await get_info(self.aiohttp_session, self.options)
            self._status = await get_status(self.aiohttp_session, self.options)

            self._data = Py2NDeviceData(
                name=self._info["deviceName"],
                model=self._info["variant"],
                serial=self._info["serialNumber"],
                firmware=self._info["swVersion"],
                uptime=datetime.now(timezone.utc) - timedelta(seconds=self._status["upTime"])
            )
        except InvalidAuthError as err:
            self._last_error = err
            _LOGGER.debug("host %s: error: %r", ip, self._last_error)
            raise
        except CONNECT_ERRORS as err:
            self._last_error = DeviceConnectionError(err)
            _LOGGER.debug("host %s: error: %r", ip, self._last_error)
            raise DeviceConnectionError(err) from err

        return self._data

    @property
    def ip_address(self) -> str:
        """Device ip address."""
        return self.options.ip_address

    @property
    def data(self) -> str:
        """Get device data."""
        if not self.initialized:
            raise NotInitialized

        return self._data