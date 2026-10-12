"""Tests for Proxmox models."""

from aioproxmox.model import PVECapabilities, PVEPermissions


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
    assert perms.has_vm_permission(101, "VM.Console") is True
    assert perms.has_vm_permission(999, "VM.Audit") is False

    # Node check
    assert perms.has_node_permission("pve-01", "Sys.Audit") is True
    assert perms.has_node_permission("pve-01", "Sys.Modify") is False

    # Storage check
    assert perms.has_storage_permission("local-lvm", "Datastore.AllocateSpace") is True

    # Generic check
    assert perms.has_permission("/vms/101", "VM.PowerMgmt") is True


def test_pve_permissions_inheritance():
    """Test privileges propagate from the closest parent path only when flagged."""
    perms = PVEPermissions.from_api_response(
        {
            "/": {"Sys.Audit": 1, "VM.Audit": 0},
            "/vms": {"VM.PowerMgmt": 1},
            "/vms/200": {},
        }
    )

    # Inherited from /vms with propagate flag
    assert perms.has_vm_permission(101, "VM.PowerMgmt") is True
    # /vms is the closest match, so / is not consulted
    assert perms.has_vm_permission(101, "Sys.Audit") is False
    # Empty path means nothing is granted there
    assert perms.has_vm_permission(200, "VM.PowerMgmt") is False
    # Non-propagating privilege only applies on the exact path
    assert perms.has_permission("/", "VM.Audit") is True
    assert perms.has_node_permission("pve-01", "VM.Audit") is False
    assert perms.has_node_permission("pve-01", "Sys.Audit") is True
    # Trailing slashes are normalised
    assert perms.has_permission("/vms/", "VM.PowerMgmt") is True
    assert perms.has_permission("//", "Sys.Audit") is True


def test_pve_permissions_no_root():
    """Test lookup without a root entry returns False."""
    perms = PVEPermissions.from_api_response({"/vms/101": {"VM.Audit": 1}})

    assert perms.has_storage_permission("local", "Datastore.Audit") is False
