"""Exceptions for 2N library."""
from enum import Enum
from dataclasses import dataclass

# Internal errors
#   Errors not needed to be handled by the caller


class Py2NError(Exception):
    """Base class for 2N errors."""


class NotInitialized(Py2NError):
    """Raised if device is not yet initialized."""


# Expected errors
#   Errors that are expected to happen and should be handled by the caller


class DeviceConnectionError(Py2NError):
    """Raised to indicate connection errors."""


class DeviceUnsupportedError(Py2NError):
    """Raised to indicate unsupported or non-2N device."""


class ApiError(Enum):
    NOT_SUPPORTED = 1
    INVALID_PATH = 2
    INVALID_METHOD = 3
    DISABLED = 4
    INVALID_CONNECTION_TYPE = 7
    INVALID_AUTHENTICATION_METHOD = 8
    AUTHORIZATION_REQUIRED = 9
    INSUFFICIENT_PRIVILEGES = 10
    MISSING_PARAMETER = 11
    INVALID_PARAMETER_VALUE = 12
    PARAMETER_DATA_TOO_BIG = 13
    PROCESSING_ERROR = 14
    NO_DATA_AVAILABLE = 15
    PARAMETER_COLLISION = 17
    REJECTED = 18
    FILE_VERSION_UNSUPPORTED = 19


@dataclass
class DeviceApiError(Py2NError):
    """Raised to indicate api error."""

    error: ApiError
