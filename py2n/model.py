"""Models for 2N library."""
from __future__ import annotations

import aiohttp

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass
class Py2NConnectionData:
    """Data for connection with 2N device."""

    host: str
    username: str | None = None
    password: str | None = None
    auth: aiohttp.BasicAuth | None = None
    digest_auth_middleware: Any | None = None
    auth_method: Literal["basic", "digest"] = "basic"
    protocol: str | None = "http"
    ssl_verify: bool = False
    unprivileged: bool | None = False

    def __post_init__(self) -> None:
        """Call after initialization."""
        if self.username is not None:
            if self.password is None:
                raise ValueError("Supply both username and password")

            if self.auth_method == "basic":
                object.__setattr__(
                    self, "auth", aiohttp.BasicAuth(self.username, self.password)
                )
                object.__setattr__(self, "digest_auth_middleware", None)
            elif self.auth_method == "digest":
                object.__setattr__(self, "auth", None)
                if not hasattr(aiohttp, "DigestAuthMiddleware"):
                    raise ValueError("Digest auth requires aiohttp with DigestAuthMiddleware")
                object.__setattr__(
                    self,
                    "digest_auth_middleware",
                    aiohttp.DigestAuthMiddleware(self.username, self.password),
                )
            else:
                raise ValueError("Unsupported auth_method")


@dataclass
class Py2NDeviceSwitch:
    """Representation of 2N device switch."""

    id: int
    enabled: bool
    active: bool
    locked: bool
    mode: str | None #inactive switches do not return a value for "mode"

@dataclass
class Py2NDevicePort:
    """2N Device IO port"""
    id: str
    type: str
    state: bool

@dataclass
class Py2NDeviceData:
    """Data collected from a 2N device."""

    name: str
    model: str
    serial: str
    host: str
    mac: str
    firmware: str
    hardware: str
    uptime: datetime
    switches: list[Py2NDeviceSwitch]
    ports: list[Py2NDevicePort]
    log_caps: list[str]
