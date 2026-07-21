"""Tests for Proxmox models."""

from phais.model import PVECapabilities, PVEPermissions


def test_pve_capabilities():
    """Test PVE capability flag evaluation."""
    caps = PVECapabilities(
        vms={"VM.PowerMgmt": 1, "VM.Console": 0}, nodes={"Sys.Console": 1}
    )

    assert caps.has_vm_permission("VM.PowerMgmt") is True
    assert caps.has_vm_permission("VM.Console") is False
    assert caps.has_vm_permission("VM.Audit") is False

    assert caps.has_node_permission("Sys.Console") is True
    assert caps.has_node_permission("Sys.Audit") is False


def test_pve_permissions_from_api():
    """Test generating and matching permissions from raw API responses."""
    raw_response = {
        "/vms/101": {"VM.Audit": 1, "VM.PowerMgmt": 1, "VM.Console": 0},
        "/nodes/pve-01": {"Sys.Audit": 1},
        "/storage/local-lvm": {"Datastore.AllocateSpace": 1},
    }

    perms = PVEPermissions.from_api_response(raw_response)

    # VM check
    assert perms.has_vm_permission(101, "VM.Audit") is True
    assert perms.has_vm_permission(101, "VM.Console") is False
    assert perms.has_vm_permission(999, "VM.Audit") is False

    # Node check
    assert perms.has_node_permission("pve-01", "Sys.Audit") is True
    assert perms.has_node_permission("pve-01", "Sys.Modify") is False

    # Storage check
    assert perms.has_storage_permission("local-lvm", "Datastore.AllocateSpace") is True

    # Generic check
    assert perms.has_permission("/vms/101", "VM.PowerMgmt") is True
