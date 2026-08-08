"""Helper endpoints for compatibility."""

import logging
from typing import Any, cast

from .exceptions import ProxmoxAPIError, ProxmoxError, ResourceNotFoundError
from .helpers import pve_cluster_cache, pve_find_node_in_cache
from .model import PVEPermissions
from .model.pve import (
    ClusterResourcesCollection,
    ContainerResource,
    LXCStatus,
    NodeStatus,
    QemuResource,
    QemuStatus,
)

_LOGGER = logging.getLogger(__name__)


class PostAction:
    """A generic executor that fires a POST request to its configured path when called."""

    def __init__(self, client: Any, path: str) -> None:
        """Initialize POST action."""
        self.client = client
        self.path = path

    def __call__(self, **kwargs: Any) -> Any:
        """Execute action."""
        return self.client.request("POST", self.path, json_data=kwargs)


class NodeActionProperty:
    """Descriptor to dynamically bind a node action endpoint to a PostAction route."""

    def __init__(self, endpoint: str) -> None:
        """Initialize property."""
        self.endpoint = endpoint

    def __get__(self, instance: Any, owner: Any = None) -> PostAction:
        """Call action."""
        if instance is None:
            return self  # type: ignore[return-value]
        return PostAction(instance.client, f"nodes/{instance.node}/{self.endpoint}")


class QemuActionProperty:
    """Descriptor to dynamically bind a QEMU action endpoint to a PostAction route."""

    def __init__(self, endpoint: str) -> None:
        """Initialize property."""
        self.endpoint = endpoint

    def __get__(self, instance: Any, owner: Any = None) -> PostAction:
        """Call action."""
        if instance is None:
            return self  # type: ignore[return-value]
        return PostAction(
            instance.client,
            f"nodes/{instance.node}/qemu/{instance.vmid}/status/{self.endpoint}",
        )


class LXCActionProperty:
    """Descriptor to dynamically bind an LXC action endpoint to a PostAction route."""

    def __init__(self, endpoint: str) -> None:
        """Initialize property."""
        self.endpoint = endpoint

    def __get__(self, instance: Any, owner: Any = None) -> PostAction:
        """Call action."""
        if instance is None:
            return self  # type: ignore[return-value]
        return PostAction(
            instance.client,
            f"nodes/{instance.node}/lxc/{instance.vmid}/status/{self.endpoint}",
        )


def node_action(endpoint: str) -> NodeActionProperty:
    """Factory helper to declare a Node PostAction endpoint."""
    return NodeActionProperty(endpoint)


def qemu_action(endpoint: str) -> QemuActionProperty:
    """Factory helper to declare a QEMU PostAction endpoint."""
    return QemuActionProperty(endpoint)


def lxc_action(endpoint: str) -> LXCActionProperty:
    """Factory helper to declare an LXC PostAction endpoint."""
    return LXCActionProperty(endpoint)


class QemuAgentEndpoint:
    """Agent endpoint."""

    def __init__(
        self,
        client: Any,
        node: str,
        vmid: int,
    ) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node
        self.vmid = vmid

    async def status(self) -> None:
        """Return generic agent info."""
        raise NotImplementedError

    async def ping(self) -> bool:
        """Ping agent for reply on alive."""
        try:
            await self.client.request(
                "POST", f"nodes/{self.node}/qemu/{self.vmid}/agent/ping"
            )
        except ProxmoxAPIError:
            return False
        return True


class QemuStatusEndpoint:
    """Qemu nested status endpoint."""

    def __init__(
        self,
        client: Any,
        node: str,
        vmid: int,
        *,
        snapshot_name: str | None = None,
        snapshot_description: str | None = None,
        snapshot_state: bool = True,
    ) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node
        self.vmid = vmid
        self.snapshot_name = snapshot_name
        self.snapshot_description = snapshot_description
        self.snapshot_state = snapshot_state

    async def status(self) -> None:
        """Return generic Qemu info."""
        raise NotImplementedError

    async def current(self) -> QemuStatus:
        """Fetch deep sensoric metrics for a QEMU VM, dynamically inferring its host node."""
        node = pve_find_node_in_cache(self.client.cluster_resources, self.vmid)

        if not node:
            _LOGGER.debug(
                "VMID %d not found in internal cache. Executing single fallback cluster fetch.",
                self.vmid,
            )
            try:
                await self.client.cluster.resources()
                node = pve_find_node_in_cache(self.client.cluster_resources, self.vmid)
            except Exception as err:
                raise ResourceNotFoundError(
                    f"Failed to fetch resource map while tracking VMID {self.vmid}"
                ) from err

            if not node:
                raise ResourceNotFoundError(
                    f"Target QEMU VMID {self.vmid} could not be located anywhere in the cluster."
                )

        raw_data = await self.client.request(
            "GET", f"nodes/{node}/qemu/{self.vmid}/status/current"
        )
        if not isinstance(raw_data, dict):
            raise ProxmoxError(
                f"Expected dict response from qemu VM status, got {type(raw_data)}"
            )
        return QemuStatus.from_dict(raw_data)

    async def snapshot(self) -> str:
        """Create a new Snapshot for a VM."""
        payload = {
            "snapname": self.snapshot_name,
            "vmstate": int(self.snapshot_state),  # Note, convert bool back to int
        }
        if self.snapshot_description:
            payload["description"] = self.snapshot_description

        return str(
            await self.client.post(
                f"nodes/{self.node}/qemu/{self.vmid}/snapshot", data=payload
            )
        )

    start = qemu_action("start")
    stop = qemu_action("stop")
    restart = qemu_action("restart")
    suspend = qemu_action("suspend")
    resume = qemu_action("resume")
    reset = qemu_action("reset")
    shutdown = qemu_action("shutdown")


class QemuEndpoint:
    """Endpoint for Qemu (VM)."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node
        self.vmid = vmid
        self.status = QemuStatusEndpoint(client, node, vmid)
        self.agent = QemuAgentEndpoint(client, node, vmid)


class LXCStatusEndpoint:
    """LXC nested status endpoint."""

    def __init__(
        self,
        client: Any,
        node: str,
        vmid: int,
        *,
        snapshot_name: str | None = None,
        snapshot_description: str | None = None,
        snapshot_state: bool = True,
    ) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node
        self.vmid = vmid
        self.snapshot_name = snapshot_name
        self.snapshot_description = snapshot_description
        self.snapshot_state = snapshot_state

    async def status(self) -> None:
        """Return generic LXC info."""
        raise NotImplementedError

    async def current(self) -> LXCStatus:
        """Fetch deep sensoric metrics for a container, dynamically inferring its host node."""
        node = pve_find_node_in_cache(self.client.cluster_resources, self.vmid)

        if not node:
            _LOGGER.debug(
                "VMID %d not found in internal cache. Executing single fallback cluster fetch.",
                self.vmid,
            )
            try:
                await self.client.cluster.resources()
                node = pve_find_node_in_cache(self.client.cluster_resources, self.vmid)
            except Exception as err:
                raise ResourceNotFoundError(
                    f"Failed to fetch resource map while tracking VMID {self.vmid}"
                ) from err

            if not node:
                raise ResourceNotFoundError(
                    f"Target container VMID {self.vmid} could not be located anywhere in the cluster."
                )

        raw_data = await self.client.request(
            "GET", f"nodes/{node}/lxc/{self.vmid}/status/current"
        )
        if not isinstance(raw_data, dict):
            raise ProxmoxError(
                f"Expected dict response from LCX status, got {type(raw_data)}"
            )
        return LXCStatus.from_dict(raw_data)

    async def snapshot(self) -> str:
        """Create a new Snapshot for a VM."""
        payload = {
            "snapname": self.snapshot_name,
            "vmstate": int(self.snapshot_state),  # Note, convert bool back to int
        }
        if self.snapshot_description:
            payload["description"] = self.snapshot_description

        return str(
            await self.client.post(
                f"nodes/{self.node}/lxc/{self.vmid}/snapshot", data=payload
            )
        )

    start = lxc_action("start")
    restart = lxc_action("restart")
    stop = lxc_action("stop")


class LXCEndpoint:
    """LXC Container endpoint."""

    def __init__(self, client: Any, node: str, vmid: int) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node
        self.vmid = vmid
        self.status = LXCStatusEndpoint(client, node, vmid)


class AccessEndpoint:
    """Access endpoint."""

    def __init__(self, client: Any) -> None:
        """Endpoint initialisation."""
        self.client = client

    async def permissions(self) -> PVEPermissions:
        """Fetch the full, granular ACL permissions map for the active session."""
        raw_data = await self.client.request("GET", "access/permissions")
        self.client.permissions = PVEPermissions.from_api_response(raw_data)

        return cast(PVEPermissions, self.client.permissions)


class NodeEndpoint:
    """Node endpoint."""

    def __init__(self, client: Any, node: str) -> None:
        """Endpoint initialisation."""
        self.client = client
        self.node = node

    def qemu(self, vmid: int) -> QemuEndpoint:
        """Map individual Qemu endpoint."""
        return QemuEndpoint(self.client, self.node, vmid)

    def lxc(self, vmid: int) -> LXCEndpoint:
        """Map LXC endpoint."""
        return LXCEndpoint(self.client, self.node, vmid)

    async def qemu_all(self) -> list[QemuResource]:
        """Fetch all Qemu resources."""
        raw = await self.client.request("GET", f"nodes/{self.node}/qemu")
        return [QemuResource.from_dict(item) for item in raw]

    async def lxc_all(self) -> list[ContainerResource]:
        """Fetch all LXC resources."""
        raw = await self.client.request("GET", f"nodes/{self.node}/lxc")
        return [ContainerResource.from_dict(item) for item in raw]

    async def status(self) -> NodeStatus:
        """Fetch deep operational status for this physical node."""
        raw_data = await self.client.request("GET", f"nodes/{self.node}/status")
        if not isinstance(raw_data, dict):
            raise ProxmoxError(
                f"Expected dict response from node status, got {type(raw_data)}"
            )
        return NodeStatus.from_dict(raw_data)

    async def tasks(
        self, typefilter: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch operational history blocks matching specific filters (e.g., vzdump)."""
        params: dict[str, Any] = {}
        if typefilter:
            params["typefilter"] = typefilter
        if limit is not None:
            params["limit"] = limit

        # The Proxmox API handles query constraints cleanly via standard payload mappings
        raw_data = await self.client.request(
            "GET",
            f"nodes/{self.node}/tasks",
            params=params or None,
        )
        return cast(
            list[dict[str, Any]], raw_data if isinstance(raw_data, list) else []
        )

    async def storage(self) -> list[dict[str, Any]]:
        """Fetch high-level allocations and health for all storages on this node."""
        raw_data = await self.client.request("GET", f"nodes/{self.node}/storage")
        return cast(
            list[dict[str, Any]], raw_data if isinstance(raw_data, list) else []
        )

    reboot = node_action("reboot")
    shutdown = node_action("shutdown")
    suspendall = node_action("suspendall")
    stopall = node_action("stopall")
    startall = node_action("startall")


class ClusterEndpoint:
    """Cluster endpoint."""

    def __init__(self, client: Any) -> None:
        """Endpoint initialisation."""
        self.client = client

    async def resources(self) -> ClusterResourcesCollection:
        """A direct, optimized call returning the complete cluster resources block."""
        raw_data = await self.client.request("GET", "cluster/resources")
        self.client.cluster_resources = ClusterResourcesCollection.from_dict(
            {"resources": raw_data}
        )

        # Update cache for rogue entries
        self.client.cluster_cache = pve_cluster_cache(self.client.cluster_resources)

        return cast(ClusterResourcesCollection, self.client.cluster_resources)
