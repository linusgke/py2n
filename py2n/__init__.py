"""Asynchronous python library to control 2N devices."""

from __future__ import annotations

import aiohttp

from typing import Any, List
from datetime import datetime, timedelta, timezone

from .model import Py2NDeviceData, Py2NDeviceSwitch, Py2NConnectionData

from .exceptions import NotInitialized, Py2NError

from .utils import get_info, get_status, restart, test_audio, get_switches, get_switch_caps , set_switch


class Py2NDevice:
    def __init__(self, aiohttp_session, options: Py2NConnectionData):
        """Device init."""
        self.aiohttp_session: aiohttp.ClientSession = aiohttp_session
        self.options = options
        self.initialized: bool = False

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

    async def update(self) -> None:
        """Update device data."""
        try:
            info: dict[str, Any] = await get_info(self.aiohttp_session, self.options)
            status: dict[str, Any] = await get_status(
                self.aiohttp_session, self.options
            )
            switches: List[Any] = await get_switches(self.aiohttp_session, self.options)
            switch_caps: List[Any] = await get_switch_caps(self.aiohttp_session, self.options)

            pySwitches = []

            for switch in switches:
                for caps in switch_caps:
                    if caps["switch"] == switch["switch"]:
                        enabled = caps["enabled"]
                        mode = caps["mode"] if enabled else None
                        break
                pySwitches.append(
                    Py2NDeviceSwitch(
                        id= switch["switch"],
                        enabled= enabled,
                        active= switch["active"],
                        locked=switch["locked"],
                        mode=mode,
                    )
                )

            self._data = Py2NDeviceData(
                name=info["deviceName"],
                model=info["variant"],
                serial=info["serialNumber"],
                host=self.options.host,
                mac=info["macAddr"],
                firmware=f"{info['swVersion']}-{info['buildType']}",
                hardware=info["hwVersion"],
                uptime=datetime.now(timezone.utc) - timedelta(seconds=status["upTime"]),
                switches=pySwitches,
            )
        except Py2NError as err:
            self._last_error = err
            raise

    async def restart(self) -> None:
        """Restart device."""
        if not self.initialized:
            raise NotInitialized

        try:
            await restart(self.aiohttp_session, self.options)
        except Py2NError as err:
            self._last_error = err
            raise

    async def audio_test(self) -> None:
        """Test audio."""
        if not self.initialized:
            raise NotInitialized

        try:
            await test_audio(self.aiohttp_session, self.options)
        except Py2NError as err:
            self._last_error = err
            raise

    async def set_switch(self, switch_id, on) -> None:
        """Set switch status."""
        if not self.initialized:
            raise NotInitialized

        if not self._data.switches:
            raise Py2NError("no switches configured")

        switch_exists = False
        for switch in self._data.switches:
            if switch_id == switch["switch"]:
                switch_exists = True
                if not switch.enabled:
                    raise Py2NError("switch disabled")
        if not switch_exists:
            raise Py2NError("invalid switch id")

        try:
            await set_switch(self.aiohttp_session, self.options, switch_id, on)
        except Py2NError as err:
            self._last_error = err
            raise

    def get_switch(self, switch_id) -> bool:
        """Get switch status."""
        if not self.initialized:
            raise NotInitialized

        if not self._data.switches:
            raise Py2NError("no switches configured")

        if switch_id not in [switch.id for switch in self._data.switches]:
            raise Py2NError("invalid switch id")

        return self._data.switches[switch_id - 1].active

    async def close(self) -> None:
        """Close http session."""
        if not self.initialized:
            raise NotInitialized

        await self.aiohttp_session.close()

    @property
    def data(self) -> Py2NDeviceData:
        """Get device data."""
        if not self.initialized:
            raise NotInitialized

        return self._data
