"""Exceptions for aioproxmox."""


class ProxmoxError(Exception):
    """Base exception for all aioproxmox client errors."""


class ProxmoxAuthError(ProxmoxError):
    """Authentication or token verification failed."""


class ProxmoxAPIError(ProxmoxError):
    """PVE API returned a non-200 HTTP status code."""

    def __init__(self, status: int, message: str, endpoint: str) -> None:
        """Format error string."""
        super().__init__(f"PVE API Error {status} at {endpoint}: {message}")
        self.status = status
        self.endpoint = endpoint


class ResourceNotFoundError(ProxmoxError):
    """Target VMID, LXC, Node, or Storage could not be found."""
