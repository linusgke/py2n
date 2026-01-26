"""Asynchronous python library to control 2N devices."""

from __future__ import annotations

import logging
import aiohttp

from typing import Any, List
from datetime import datetime, timedelta, timezone, UTC

from .model import Py2NDeviceData, Py2NDeviceSwitch, Py2NConnectionData

from .const import HTTP_CALL_TIMEOUT

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
    set_port,
    get_log_caps,
    log_subscribe,
    log_unsubscribe,
    log_pull,
    get_dir_template,
    query_dir,
    update_dir,
    api_request
    )

_LOGGER = logging.getLogger(__name__)

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
            log_caps: List[Any] = await get_log_caps(self.aiohttp_session, self.options)
            pySwitches = []

            if(self.options.unprivileged):
                ports = []
                uptime = None
            else:
                ports = await get_ports(self.aiohttp_session, self.options)
                uptime = await self._get_uptime()
                switch_caps: List[Any] = await get_switch_caps(self.aiohttp_session, self.options)
                switches: List[Any] = await get_switches(self.aiohttp_session, self.options)
                for switch in switches:
                    if switch['active']:
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
                uptime=uptime,
                switches=pySwitches,
                log_caps=log_caps,
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

    async def _get_uptime(self) -> datetime:
        status = await get_status(self.aiohttp_session, self.options)
        new_uptime = datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=status["upTime"])
        return new_uptime

    async def update_system_status(self) -> None:
        new_uptime = await self._get_uptime()
        delta = new_uptime - self._data.uptime
        if abs(delta.total_seconds()) > 5:
            self._data.uptime=new_uptime

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

    async def log_subscribe(self, include: str="new", filter: list[str]=[], duration: int=90) -> int:
        """subscribe to Log channel."""
        if not self.initialized:
            raise NotInitialized

        channel_id = await log_subscribe(self.aiohttp_session, self.options, include, filter, duration)
        return channel_id

    async def log_unsubscribe(self, id: int) -> None:
        """unsubscribe from Log channel."""
        if not self.initialized:
            raise NotInitialized

        await log_unsubscribe(self.aiohttp_session, self.options, id)

    async def log_pull(self, id: int, timeout: int=0) -> None:
        """pull from Log channel."""
        if not self.initialized:
            raise NotInitialized

        messages = await log_pull(self.aiohttp_session, self.options, id, timeout)
        return messages

    def get_switch(self, switch_id: int) -> bool:
        """Get switch status."""
        if not self.initialized:
            raise NotInitialized

        switch = self._find_switch(switch_id)
        return switch.active

    async def get_dir_template(self) -> str:
        if not self.initialized:
            raise NotInitialized

        result = await get_dir_template(self.aiohttp_session, self.options)
        return result

    async def query_dir(self, query: dict = {}) -> str:
        if not self.initialized:
            raise NotInitialized

        result = await query_dir(self.aiohttp_session, self.options, query)
        return result

    async def update_dir(self, users: list = []) -> str:
        if not self.initialized:
            raise NotInitialized

        result = await update_dir(self.aiohttp_session, self.options, users)
        return result

    def _find_switch(self, switch_id: int) -> Py2NDeviceSwitch:
        if not self._data.switches or len(self._data.switches) == 0:
            raise Py2NError("no switches configured")

        for switch in self._data.switches:
            if switch.id == switch_id:
                return switch
        raise Py2NError("invalid switch id")

    async def api_request(self, endpoint: str, timeout: int = HTTP_CALL_TIMEOUT, method: str = "GET", data = None, json = None) -> dict[str, Any] | None:
        if not self.initialized:
            raise NotInitialized

        result = await api_request(self.aiohttp_session, self.options, endpoint=endpoint, timeout=timeout, method=method, data=data,json=json)
        return result

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
