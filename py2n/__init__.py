"""Asynchronous python library to control 2N devices."""

from __future__ import annotations

import aiohttp

from typing import Any, List
from datetime import datetime, timedelta, timezone

from .model import Py2NDeviceData, Py2NDeviceSwitch, Py2NConnectionData

from .exceptions import NotInitialized, Py2NError

from .utils import (
    get_info,
    get_status,
    restart,
    test_audio,
    get_switches,
    get_switch_caps,
    set_switch,
    get_ports,
    get_port_status,
    set_port
    )


class Py2NDevice:
    def __init__(self, aiohttp_session: aiohttp.ClientSession, options: Py2NConnectionData):
        """Device init."""
        self.aiohttp_session = aiohttp_session
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

            ports = await get_ports(self.aiohttp_session, self.options)

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
                ports=ports,
            )
        except Py2NError as err:
            self._last_error = err
            raise

    async def update_switch_status(self) -> None:
        statuses = await get_switches(self.aiohttp_session, self.options)
        for switch_status in statuses:
            for switch in self._data.switches:
                if switch.id == switch_status["switch"]:
                    switch.active = switch_status["active"]
                    switch.locked = switch_status["locked"]
                    break

    async def update_port_status(self) -> None:
        statuses = await get_port_status(self.aiohttp_session, self.options)
        for port_status in statuses:
            for port in self._data.ports:
                if port.id == port_status["port"]:
                    port.state = port_status["state"]
                    break

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

    async def set_switch(self, switch_id: int, on: bool) -> None:
        """Set switch status."""
        if not self.initialized:
            raise NotInitialized

        switch = self._find_switch(switch_id)
        if not switch.enabled:
            raise Py2NError("switch disabled")

        try:
            await set_switch(self.aiohttp_session, self.options, switch_id, on)
        except Py2NError as err:
            self._last_error = err
            raise

    async def set_port(self, port_id: str, on: bool) -> None:
        """Set output port status"""
        if not self.initialized:
            raise NotInitialized

        for port in self._data.ports:
            if port.id == port_id:
                if port.type == "output":
                    await set_port(self.aiohttp_session, self.options, port_id, on)
                    return
                raise Py2NError("invalid operation: unable to set state on input port")
        raise Py2NError("unknown port id")


    def get_switch(self, switch_id: int) -> bool:
        """Get switch status."""
        if not self.initialized:
            raise NotInitialized

        switch = self._find_switch(switch_id)
        return switch.active

    def _find_switch(self, switch_id: int) -> Py2NDeviceSwitch:
        if not self._data.switches or len(self._data.switches) == 0:
            raise Py2NError("no switches configured")

        for switch in self._data.switches:
            if switch.id == switch_id:
                return switch
        raise Py2NError("invalid switch id")

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
