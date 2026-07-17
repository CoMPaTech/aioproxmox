"""Test migration scenarios."""

import copy

from phais.model.pve import ClusterResourcesCollection, ContainerResource, QemuResource


def test_migrate_qemu_virtual_machine(mock_pve_dual_node_cluster_raw):
    """Verify that a QEMU VM (vmid 101) transitions hosts cleanly inside the collection collection."""
    # 1. Establish state baseline
    collection = ClusterResourcesCollection.from_dict(
        {"resources": mock_pve_dual_node_cluster_raw}
    )
    vms = [r for r in collection.resources if isinstance(r, QemuResource)]
    target_vm = next(v for v in vms if v.vmid == 101)

    assert target_vm.node == "pve-01"

    # 2. Simulate API state update post-migration
    updated_raw = copy.deepcopy(mock_pve_dual_node_cluster_raw)
    for item in updated_raw:
        if item["id"] == "qemu/101":
            item["node"] = "pve-02"

    new_collection = ClusterResourcesCollection.from_dict({"resources": updated_raw})
    new_vms = [r for r in new_collection.resources if isinstance(r, QemuResource)]
    migrated_vm = next(v for v in new_vms if v.vmid == 101)

    # 3. Assert target node isolation changed without impacting sibling structures
    assert migrated_vm.node == "pve-02"
    assert next(v for v in new_vms if v.vmid == 102).node == "pve-02"


def test_migrate_lxc_container(mock_pve_dual_node_cluster_raw):
    """Verify an LXC container (vmid 202) relocates across hosts successfully."""
    collection = ClusterResourcesCollection.from_dict(
        {"resources": mock_pve_dual_node_cluster_raw}
    )
    lxcs = [r for r in collection.resources if isinstance(r, ContainerResource)]
    target_lxc = next(lx for lx in lxcs if lx.vmid == 202)

    assert target_lxc.node == "pve-02"

    # Simulate cross-node migration change mapping
    updated_raw = copy.deepcopy(mock_pve_dual_node_cluster_raw)
    for item in updated_raw:
        if item["id"] == "lxc/202":
            item["node"] = "pve-01"

    new_collection = ClusterResourcesCollection.from_dict({"resources": updated_raw})
    new_lxcs = [r for r in new_collection.resources if isinstance(r, ContainerResource)]
    migrated_lxc = next(lx for lx in new_lxcs if lx.vmid == 202)

    assert migrated_lxc.node == "pve-01"
