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


@dataclass(slots=True)
class PVEPermissions:
    """Strongly-typed lookup mapping paths (vms, storage, nodes) to specific ACL privileges."""

    # Internal structure: dict[path_string, set[privilege_strings]]
    # Example: {"/vms/101": {"VM.Audit", "VM.PowerMgmt"}}
    _perm_map: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict[str, dict[str, int]]) -> PVEPermissions:
        """Factory to compile the raw access/permissions dict into clean lookups."""
        compiled: dict[str, set[str]] = {}

        for path, priv_dict in data.items():
            # Proxmox returns permissions as {"VM.Audit": 1, "VM.PowerMgmt": 1}
            allowed_privs = {priv for priv, val in priv_dict.items() if val == 1}
            if allowed_privs:
                compiled[path] = allowed_privs

        return cls(_perm_map=compiled)

    def has_permission(self, path: str, privilege: str) -> bool:
        """Check privilege using ProxmoxVE ACL inheritance."""
        paths = [
            path,
            path.rpartition("/")[0],
            "/",
        ]

        for p in paths:
            privs = self._perm_map.get(p)
            if privs and privilege in privs:
                return True

        return False

    def has_vm_permission(self, vmid: int | str, privilege: str) -> bool:
        """Helper to check permissions for a specific VM ID."""
        return self.has_permission(f"/vms/{vmid}", privilege)

    def has_storage_permission(self, storage_id: str, privilege: str) -> bool:
        """Helper to check permissions for a specific storage pool."""
        return self.has_permission(f"/storage/{storage_id}", privilege)

    def has_node_permission(self, node: str, privilege: str) -> bool:
        """Helper to check permissions for a specific cluster node."""
        return self.has_permission(f"/nodes/{node}", privilege)
