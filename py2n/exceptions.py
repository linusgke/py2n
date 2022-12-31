"""Exceptions for 2N library."""

# Internal errors
#   Errors not needed to be handled by the caller


class Py2NError(Exception):
    """Base class for 2N errors."""


class NotInitialized(Py2NError):
    """Raised if device is not initialized."""


# Expected errors
#   Errors that are expected to happen and should be handled by the caller


class DeviceConnectionError(Py2NError):
    """Exception indicates device connection errors."""


class InvalidAuthError(Py2NError):
    """Raised to indicate invalid or missing authentication error."""
