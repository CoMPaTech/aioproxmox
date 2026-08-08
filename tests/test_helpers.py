"""Tests for Proxmox helpers."""

from aioproxmox.helpers import pve_cluster_cache, pve_find_node_in_cache
from aioproxmox.model.pve import ClusterCache, ClusterResourcesCollection


def test_pve_find_node_in_cache(mock_pve_dual_node_cluster_raw):
    """Test extracting the node name for a given VMID."""
    collection = ClusterResourcesCollection.from_dict(
        {"resources": mock_pve_dual_node_cluster_raw}
    )

    assert pve_find_node_in_cache(collection, 101) == "pve-01"
    assert pve_find_node_in_cache(collection, 102) == "pve-02"
    assert pve_find_node_in_cache(collection, 201) == "pve-01"

    # Non-existent VMID
    assert pve_find_node_in_cache(collection, 999) is None

    # Missing collection
    assert pve_find_node_in_cache(None, 101) is None


def test_pve_cluster_cache(mock_pve_dual_node_cluster_raw):
    """Test evicting stale data from the status cache."""
    collection = ClusterResourcesCollection.from_dict(
        {"resources": mock_pve_dual_node_cluster_raw}
    )

    updated_cache = pve_cluster_cache(collection)

    # Assert valid entries remain
    assert "pve-01" in updated_cache.nodes
    assert 101 in updated_cache.qemu
    assert 202 in updated_cache.lxc

    # Assert stale entries are evicted
    assert "stale-node" not in updated_cache.nodes
    assert 999 not in updated_cache.qemu
    assert 888 not in updated_cache.lxc

    assert pve_cluster_cache(None) == ClusterCache()
