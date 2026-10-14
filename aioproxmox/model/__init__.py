"""Models for Proxmox."""

from dataclasses import dataclass, field

# Paths Proxmox always evaluates for the whole-tree permissions response;
# when one is absent, nothing is granted there or below via inheritance.
ALWAYS_REPORTED_PATHS = frozenset(
    {"/", "/access", "/access/groups", "/nodes", "/pool", "/sdn", "/storage", "/vms"}
)


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
    """Effective ACL privileges per path, as returned by /access/permissions."""

    # path -> {privilege: whether it propagates to child paths}
    # Example: {"/vms/101": {"VM.Audit", "VM.PowerMgmt"}}
    _perm_map: dict[str, dict[str, bool]] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict[str, dict[str, int]]) -> PVEPermissions:
        """Compile the raw access/permissions response."""
        return cls(
            _perm_map={
                path: {priv: bool(propagate) for priv, propagate in privs.items()}
                for path, privs in data.items()
            }
        )

    def has_permission(self, path: str, privilege: str) -> bool:
        """Check a privilege on a path or its direct parent.

        Proxmox omits paths with no effective privileges, so a NoAccess ACL is
        indistinguishable from a path without its own ACL. Only the direct
        parent is trusted for inheritance; fetch the path itself with
        ``AccessEndpoint.permissions(path=...)`` when this matters.
        """
        path = path.rstrip("/") or "/"
        if (privs := self._perm_map.get(path)) is not None:
            return privilege in privs
        if path in ALWAYS_REPORTED_PATHS:
            return False

        parent = path.rpartition("/")[0] or "/"
        return self._perm_map.get(parent, {}).get(privilege, False)

    def has_vm_permission(self, vmid: int | str, privilege: str) -> bool:
        """Helper to check permissions for a specific VM ID."""
        return self.has_permission(f"/vms/{vmid}", privilege)

    def has_storage_permission(self, storage_id: str, privilege: str) -> bool:
        """Helper to check permissions for a specific storage pool."""
        return self.has_permission(f"/storage/{storage_id}", privilege)

    def has_node_permission(self, node: str, privilege: str) -> bool:
        """Helper to check permissions for a specific cluster node."""
        return self.has_permission(f"/nodes/{node}", privilege)
