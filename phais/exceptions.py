"""Exceptions for phais."""


class ProxmoxException(Exception):
    """Base Proxmox Exception."""


class AuthenticationError(ProxmoxException):
    """Authentication issue."""
