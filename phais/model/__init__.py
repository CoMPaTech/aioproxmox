"""Models for Proxmox."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PVECapabilities:
    """Strongly-typed evaluation mapping of active ProxmoxVE user session permissions."""

    nodes: dict[str, int] = field(default_factory=dict)
    sdn: dict[str, int] = field(default_factory=dict)
    storage: dict[str, int] = field(default_factory=dict)
    vms: dict[str, int] = field(default_factory=dict)
    access: dict[str, int] = field(default_factory=dict)
    dc: dict[str, int] = field(default_factory=dict)
    mapping: dict[str, int] = field(default_factory=dict)

    def has_vm_permission(self, perm: str) -> bool:
        """Helper to quickly check a VM flag (e.g., 'VM.PowerMgmt')."""
        return bool(self.vms.get(perm, 0))

    def has_node_permission(self, perm: str) -> bool:
        """Helper to quickly check a Node flag (e.g., 'Sys.Console')."""
        return bool(self.nodes.get(perm, 0))
