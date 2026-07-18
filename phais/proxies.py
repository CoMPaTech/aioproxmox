"""Helper Proxies for compatibility."""

import logging
from typing import Any, cast

from .helpers import pve_find_node_in_cache, pve_reconcile_status_cache
from .model.pve import ClusterResourcesCollection, LXCStatus, NodeStatus, QemuStatus

_LOGGER = logging.getLogger(__name__)


class QemuStatusProxy:
    """Sub-proxy for handling Qemu nested status endpoints."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Sub-proxy initialisation."""
        self._client = client
        self._node = node
        self._vmid = vmid

    def __await__(self) -> Any:
        """Allow for awaiting generic status."""
        return self.status().__await__()

    async def status(self) -> None:
        """Return generic Qemu info."""
        raise NotImplementedError

    async def current(self) -> QemuStatus:
        """Fetch deep sensoric metrics for a QEMU VM, dynamically inferring its host node."""
        node = pve_find_node_in_cache(self._client.cluster_resources, self._vmid)

        if not node:
            _LOGGER.debug(
                "VMID %d not found in internal cache. Executing single fallback cluster fetch.",
                self._vmid,
            )
            try:
                await self._client.cluster.resources()
                node = pve_find_node_in_cache(
                    self._client.cluster_resources, self._vmid
                )
            except Exception as err:
                raise RuntimeError(
                    f"Failed to fetch resource map while tracking VMID {self._vmid}"
                ) from err

            if not node:
                raise KeyError(
                    f"Target QEMU VMID {self._vmid} could not be located anywhere in the cluster."
                )

        raw_data = await self._client.request(
            "GET", f"nodes/{node}/qemu/{self._vmid}/status/current"
        )
        if not isinstance(raw_data, dict):
            raise TypeError(
                f"Expected dict response from qemu VM status, got {type(raw_data)}"
            )
        return QemuStatus.from_dict(raw_data)


class QemuProxy:
    """Proxy for Qemu VM endpoint."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Qemu Proxy initialisation."""
        self._client = client
        self._node = node
        self._vmid = vmid
        self.status = QemuStatusProxy(client, node, vmid)


class LXCStatusProxy:
    """Sub-proxy for handling nested status endpoints."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Sub-proxy initialisation."""
        self._client = client
        self._node = node
        self._vmid = vmid

    def __await__(self) -> Any:
        """Allow for awaiting generic status."""
        return self.status().__await__()

    async def status(self) -> None:
        """Return generic LXC info."""
        raise NotImplementedError

    async def current(self) -> LXCStatus:
        """Fetch deep sensoric metrics for a container, dynamically inferring its host node."""
        node = pve_find_node_in_cache(self._client.cluster_resources, self._vmid)

        if not node:
            _LOGGER.debug(
                "VMID %d not found in internal cache. Executing single fallback cluster fetch.",
                self._vmid,
            )
            try:
                await self._client.cluster.resources()
                node = pve_find_node_in_cache(
                    self._client.cluster_resources, self._vmid
                )
            except Exception as err:
                raise RuntimeError(
                    f"Failed to fetch resource map while tracking VMID {self._vmid}"
                ) from err

            if not node:
                raise KeyError(
                    f"Target container VMID {self._vmid} could not be located anywhere in the cluster."
                )

        raw_data = await self._client.request(
            "GET", f"nodes/{node}/lxc/{self._vmid}/status/current"
        )
        if not isinstance(raw_data, dict):
            raise TypeError(
                f"Expected dict response from LCX status, got {type(raw_data)}"
            )
        return LXCStatus.from_dict(raw_data)


class LXCProxy:
    """Proxy for LXC Container endpoint."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Container Proxy initialisation."""
        self._client = client
        self._node = node
        self._vmid = vmid
        self.status = LXCStatusProxy(client, node, vmid)


class NodeProxy:
    """Proxy for Node endpoint."""

    def __init__(self, client: Any, node: str) -> None:
        """Node proxy."""
        self._client = client
        self._node = node

    def qemu(self, vmid: int) -> QemuProxy:
        """Add Qemu proxy."""
        return QemuProxy(self._client, self._node, vmid)

    def lxc(self, vmid: int) -> LXCProxy:
        """Add LXC proxy."""
        return LXCProxy(self._client, self._node, vmid)

    async def status(self) -> NodeStatus:
        """Fetch deep operational status for this physical node."""
        raw_data = await self._client.request("GET", f"nodes/{self._node}/status")
        if not isinstance(raw_data, dict):
            raise TypeError(
                f"Expected dict response from node status, got {type(raw_data)}"
            )
        return NodeStatus.from_dict(raw_data)


class ClusterProxy:
    """Proxy for Cluster endpoint."""

    def __init__(self, client: Any) -> None:
        """Cluster proxy."""
        self._client = client

    async def resources(self) -> ClusterResourcesCollection:
        """A direct, optimized call returning the complete cluster resources block."""
        raw_data = await self._client.request("GET", "cluster/resources")
        self._client.cluster_resources = ClusterResourcesCollection.from_dict(
            {"resources": raw_data}
        )

        # Update status_cache for rogue entries
        self._client.status_cache = pve_reconcile_status_cache(
            self._client.cluster_resources, self._client.status_cache
        )

        return cast(ClusterResourcesCollection, self._client.cluster_resources)
