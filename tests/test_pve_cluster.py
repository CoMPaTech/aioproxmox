"""Testing."""

import logging

from phais.model.pve import (
    ClusterResourcesCollection,
    NodeResource,
    QemuResource,
    ResourceStatus,
    ResourceType,
    StorageResource,
)


def test_deserialize_pve_cluster_resources(mock_pve_cluster_resources_raw):
    """Ensure raw array parses cleanly into distinct structured object types."""
    payload = {"resources": mock_pve_cluster_resources_raw}
    collection = ClusterResourcesCollection.from_dict(payload)

    assert len(collection.resources) == 3

    # 1. Verify Physical Node Parsing & Camel-Case Hyphen Aliasing
    node = collection.resources[0]
    assert isinstance(node, NodeResource)
    assert node.id == "node/pve-01"
    assert node.resource_type == ResourceType.NODE
    assert node.cgroup_mode == 2  # Handled via metadata alias "cgroup-mode"

    # 2. Verify VM Parsing & Delimited Semicolon String-to-List Conversion
    vm = collection.resources[1]
    assert isinstance(vm, QemuResource)
    assert vm.name == "homeassistant-core"
    assert vm.resource_type == ResourceType.QEMU
    assert vm.tags == ["homeautomation", "production", "important"]

    # 3. Verify Storage Sub-Type Targeting
    storage = collection.resources[2]
    assert isinstance(storage, StorageResource)
    assert storage.storage == "local-lvm"
    assert storage.status == ResourceStatus.AVAILABLE


def test_deserialize_resilience_to_unknown_elements(caplog):
    """Unknown types/enums shouldn't crash collection loading; they fallback safely."""
    malformed_payload = {
        "resources": [
            {
                "id": "qemu/999",
                "vmid": 999,
                "name": "future-vm",
                "node": "pve-01",
                "type": "qemu",
                "status": "some-new-status-from-pve-update",  # Evaluates via _missing_ fallback
                "template": 0,
                "maxcpu": 2,
                "maxmem": 1024,
                "maxdisk": 1024,
            },
            {
                "id": "unknown/123",
                "type": "brand-new-pve-resource-type",  # Handled cleanly inside loop
            },
        ]
    }

    collection = ClusterResourcesCollection.from_dict(malformed_payload)

    # The unknown collection type string drops out cleanly without crashing the loop
    assert len(collection.resources) == 1

    # The unknown status fallback on the matching VM becomes ResourceStatus.UNKNOWN
    parsed_vm = collection.resources[0]
    assert parsed_vm.status == ResourceStatus.UNKNOWN
    assert "Unknown Proxmox resource status encountered" in caplog.text


def test_deserialize_handles_broken_items(caplog):
    """A completely broken dictionary item shouldn't prevent parsing valid elements."""
    malformed_payload = {
        "resources": [
            {
                "id": "node/broken-node",
                "type": "node",
                # Missing all required fields like node, status, cpu, maxcpu, etc.
            },
            {
                "id": "storage/working-storage",
                "storage": "local-lvm",
                "node": "pve-01",
                "type": "storage",
                "status": "available",
                "plugintype": "lvmthin",
                "shared": 0,
                "content": "rootdir",
            },
        ]
    }

    with caplog.at_level(logging.ERROR):
        collection = ClusterResourcesCollection.from_dict(malformed_payload)

    # The broken item dropped into the except block, leaving only the healthy storage item
    assert len(collection.resources) == 1
    assert isinstance(collection.resources[0], StorageResource)
    assert "Failed to parse resource item 'node/broken-node'" in caplog.text
