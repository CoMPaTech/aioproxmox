"""Proxmox Virtualisation Engine (proxmoxve or pve) Models."""

from dataclasses import dataclass, field
from enum import StrEnum
import logging
from typing import Annotated, Any

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

_LOGGER = logging.getLogger(__name__)


class PhaisDataClass(DataClassDictMixin):
    """Base phais class."""

    class Config(BaseConfig):
        """DataClass configuration."""

        allow_unknown_fields = True


class ResourceType(StrEnum):
    """Proxmox cluster resource types."""

    NODE = "node"
    QEMU = "qemu"
    LXC = "lxc"
    STORAGE = "storage"
    NETWORK = "network"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: Any) -> ResourceType:
        _LOGGER.warning("Unknown Proxmox resource type encountered: %r", value)
        return cls.UNKNOWN


class OperationalStatus(StrEnum):
    """Operational status of resources."""

    ONLINE = "online"
    OFFLINE = "offline"
    RUNNING = "running"
    STOPPED = "stopped"
    AVAILABLE = "available"
    UNKNOWN = "unknown"
    OK = "ok"

    @classmethod
    def _missing_(cls, value: Any) -> OperationalStatus:
        _LOGGER.warning("Unknown Proxmox resource status encountered: %r", value)
        return cls.UNKNOWN


class QmpStatus(StrEnum):
    """QMP engine status of QEMU."""

    RUNNING = "running"
    STOPPED = "stopped"
    FROZEN = "frozen"
    PAUSED = "paused"
    PRELAUNCH = "prelaunch"
    POSTMIGRATE = "postmigrate"


class StoragePluginType(StrEnum):
    """Proxmox storage backend plugins."""

    DIR = "dir"
    LVMTHIN = "lvmthin"
    LVM = "lvm"
    NFS = "nfs"
    PBS = "pbs"
    CEPHFS = "cephfs"
    RBD = "rbd"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: Any) -> StoragePluginType:
        _LOGGER.warning("Unknown Proxmox storage plugin type encountered: %r", value)
        return cls.UNKNOWN


def deserialize_tags(value: Any) -> list[str]:
    """Cleanly split Proxmox semicolon-separated tag strings for Home Assistant."""
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(";") if tag.strip()]
    if isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return []


@dataclass
class NodeResource(PhaisDataClass):
    """Represents a physical Proxmox Node on Cluster Level."""

    id: str
    node: str
    status: OperationalStatus
    cpu: float
    maxcpu: int
    mem: int
    maxmem: int
    disk: int
    maxdisk: int
    uptime: int
    resource_type: ResourceType = field(metadata={"alias": "type"})
    cgroup_mode: int | None = field(default=None, metadata={"alias": "cgroup-mode"})
    level: str | None = None


@dataclass
class ResourceMemoryStats(DataClassDictMixin):
    """Memory resources."""

    total: int
    used: int
    free: int
    available: int | None = None


@dataclass
class ResourceDiskStats(DataClassDictMixin):
    """Storage resources."""

    total: int
    used: int
    free: int
    avail: int | None = None


@dataclass
class NodeSwapStats(DataClassDictMixin):
    """Swap resources."""

    total: int
    free: int
    used: int


@dataclass
class NodeCpuInfo(DataClassDictMixin):
    """CPU resources."""

    cpus: int
    cores: int
    sockets: int
    model: str
    vendor: str
    mhz: str | None = None


@dataclass
class NodeStatus(DataClassDictMixin):
    """Represents the complete nested structure returned by /nodes/{node}/status."""

    uptime: int
    cpu: float
    idle: int
    memory: ResourceMemoryStats
    swap: NodeSwapStats
    rootfs: ResourceDiskStats
    cpuinfo: NodeCpuInfo
    pveversion: str
    loadavg: list[str] = field(default_factory=list)
    wait: float | None = None

    class Config(BaseConfig):
        """Class configuration."""

        allow_unknown_fields = (
            True  # Drops boot-info, kversion, and kernel metadata gracefully
        )


@dataclass
class ClusterQemuResource(PhaisDataClass):
    """Represents a QEMU Virtual Machine on Cluster Level."""

    id: str
    vmid: int
    name: str
    node: str
    status: OperationalStatus
    template: int
    maxcpu: int
    maxmem: int
    maxdisk: int
    resource_type: ResourceType = field(metadata={"alias": "type"})
    cpu: float = 0.0
    mem: int = 0
    memhost: int = 0
    disk: int = 0
    diskread: int = 0
    diskwrite: int = 0
    netin: int = 0
    netout: int = 0
    uptime: int = 0
    tags: list[str] = field(
        default_factory=list, metadata={"deserialize": deserialize_tags}
    )


@dataclass
class QemuResource(DataClassDictMixin):
    """Represents a QEMU Virtual Machine summary on a specific Node."""

    vmid: int
    name: str
    status: OperationalStatus
    cpus: int
    cpu: float = 0.0
    mem: int = 0
    maxmem: int = 0
    disk: int = 0
    maxdisk: int = 0
    memhost: int = 0
    netin: int = 0
    netout: int = 0
    uptime: int = 0
    pid: int | None = None
    template: int = 0


@dataclass
class QemuStatus(DataClassDictMixin):
    """Represents the real-time operational telemetry of a specific QEMU virtual machine."""

    vmid: int
    status: OperationalStatus
    qmpstatus: QmpStatus
    name: str
    cpus: int
    cpu: float
    mem: int
    maxmem: int
    disk: int
    maxdisk: int
    uptime: int
    netin: int
    netout: int
    agent: int | None = None

    class Config(BaseConfig):
        """Class configuration."""

        allow_unknown_fields = (
            True  # Drops the internal "ha" block and "clipboard" safely
        )


@dataclass
class ClusterContainerResource(PhaisDataClass):
    """Represents an LXC Container on Cluster Level."""

    id: str
    vmid: int
    name: str
    node: str
    status: OperationalStatus
    template: int
    maxcpu: int
    maxmem: int
    maxdisk: int
    resource_type: ResourceType = field(metadata={"alias": "type"})
    cpu: float = 0.0
    mem: int = 0
    memhost: int = 0
    disk: int = 0
    diskread: int = 0
    diskwrite: int = 0
    netin: int = 0
    netout: int = 0
    uptime: int = 0
    tags: list[str] = field(
        default_factory=list, metadata={"deserialize": deserialize_tags}
    )


@dataclass
class ContainerResource(DataClassDictMixin):
    """Represents a LXC Container summary on a specific Node."""

    vmid: int
    name: str
    status: OperationalStatus
    cpus: int
    cpu: float = 0.0
    mem: int = 0
    maxmem: int = 0
    disk: int = 0
    maxdisk: int = 0
    netin: int = 0
    netout: int = 0
    swap: int = 0
    maxswap: int = 0
    uptime: int = 0
    pid: int | None = None
    template: int = 0


@dataclass
class LXCStatus(DataClassDictMixin):
    """Represents the real-time operational telemetry of a specific LXC container."""

    vmid: int
    status: str
    name: str
    cpus: int
    cpu: float
    mem: int
    maxmem: int
    swap: int
    maxswap: int
    disk: int
    maxdisk: int
    diskread: int
    diskwrite: int
    netin: int
    netout: int
    uptime: int
    pid: int | None = None

    class Config(BaseConfig):
        """Class configuration."""

        allow_unknown_fields = True  # Safely ignores the PSI 'pressure' strings and 'ha' flags, also removes flags which are already in cluster resources


@dataclass
class StorageResource(PhaisDataClass):
    """Represents a defined Cluster or Node Storage pool."""

    id: str
    storage: str
    node: str
    status: OperationalStatus
    plugintype: StoragePluginType
    shared: int
    content: str
    resource_type: ResourceType = field(metadata={"alias": "type"})
    disk: int = 0
    maxdisk: int = 0


@dataclass
class NetworkResource(PhaisDataClass):
    """Represents a SDN or physical cluster network interface definition."""

    id: str
    node: str
    resource_type: ResourceType = field(metadata={"alias": "type"})
    status: str = "unknown"

    class Config(BaseConfig):
        """Class configuration."""

        allow_unknown_fields = True


def route_pve_resource(data: Any) -> type:
    """Map the raw API type attribute directly to the correct parsing target."""
    if isinstance(data, dict) and (kind := data.get("type")):
        match kind:
            case ResourceType.NODE | "node":
                return NodeResource
            case ResourceType.QEMU | "qemu":
                return ClusterQemuResource
            case ResourceType.LXC | "lxc":
                return ClusterContainerResource
            case ResourceType.STORAGE | "storage":
                return StorageResource
            case ResourceType.NETWORK | "network":
                return NetworkResource
    raise ValueError(f"Unsupported or missing Proxmox resource type tag: {data}")


ProxmoxResource = Annotated[
    NodeResource | ClusterQemuResource | ClusterContainerResource | StorageResource,
    Discriminator(
        variant_tagger_fn=route_pve_resource,
        include_subtypes=True,  # Satisfies the internal Mashumaro safety guardrail
    ),
]


def deserialize_resource_list(value: Any) -> list[Any]:
    """Manually route each raw dictionary item to its corresponding dataclass."""
    if not isinstance(value, list):
        return []

    parsed_items: list[Any] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        kind = item.get("type")
        try:
            match kind:
                case "node":
                    parsed_items.append(NodeResource.from_dict(item))
                case "qemu":
                    parsed_items.append(ClusterQemuResource.from_dict(item))
                case "lxc":
                    parsed_items.append(ClusterContainerResource.from_dict(item))
                case "storage":
                    parsed_items.append(StorageResource.from_dict(item))
                case "network":
                    parsed_items.append(NetworkResource.from_dict(item))
                case _:
                    _LOGGER.warning("Skipping unknown Proxmox resource type: %r", kind)
        except Exception:
            _LOGGER.exception("Failed to parse resource item %r", item.get("id"))

    return parsed_items


@dataclass
class ClusterResourcesCollection(PhaisDataClass):
    """Container mapping to deserialize raw /cluster/resources payloads securely."""

    resources: list[
        NodeResource
        | ClusterQemuResource
        | ClusterContainerResource
        | StorageResource
        | NetworkResource
    ] = field(metadata={"deserialize": deserialize_resource_list})

    def __iter__(self) -> Any:
        """Provide iteration."""
        return iter(self.resources)


@dataclass
class ClusterStatusCache:
    """Centralized, indexed state hub storing real-time telemetry metrics."""

    nodes: dict[str, NodeStatus] = field(default_factory=dict)
    qemu: dict[int, QemuStatus] = field(default_factory=dict)
    lxc: dict[int, LXCStatus] = field(default_factory=dict)
    storage: dict[str, StorageResource] = field(default_factory=dict)
