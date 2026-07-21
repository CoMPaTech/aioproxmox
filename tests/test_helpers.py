"""Tests for Proxmox helpers."""

from phais.helpers import pve_find_node_in_cache, pve_reconcile_status_cache
from phais.model.pve import (
    ClusterResourcesCollection,
    ClusterStatusCache,
    LXCStatus,
    NodeCpuInfo,
    NodeStatus,
    NodeSwapStats,
    QemuStatus,
    ResourceDiskStats,
    ResourceMemoryStats,
)


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


def test_pve_reconcile_status_cache(mock_pve_dual_node_cluster_raw):
    """Test evicting stale data from the status cache."""
    collection = ClusterResourcesCollection.from_dict(
        {"resources": mock_pve_dual_node_cluster_raw}
    )

    # Setup a mock cache with both valid and stale entries
    mem = ResourceMemoryStats(total=1, used=1, free=1)
    disk = ResourceDiskStats(total=1, used=1, free=1)
    swap = NodeSwapStats(total=1, used=1, free=1)
    cpu = NodeCpuInfo(cpus=1, cores=1, sockets=1, model="A", vendor="B")

    mock_node = NodeStatus(
        uptime=1,
        cpu=1.0,
        idle=1,
        memory=mem,
        swap=swap,
        rootfs=disk,
        cpuinfo=cpu,
        pveversion="1.0",
    )
    mock_qemu = QemuStatus(
        vmid=1,
        status="running",
        qmpstatus="running",
        name="A",
        cpus=1,
        cpu=1.0,
        mem=1,
        maxmem=1,
        disk=1,
        maxdisk=1,
        uptime=1,
        netin=1,
        netout=1,
    )
    mock_lxc = LXCStatus(
        vmid=1,
        status="running",
        name="A",
        cpus=1,
        cpu=1.0,
        mem=1,
        maxmem=1,
        swap=1,
        maxswap=1,
        disk=1,
        maxdisk=1,
        diskread=1,
        diskwrite=1,
        netin=1,
        netout=1,
        uptime=1,
    )

    cache = ClusterStatusCache(
        nodes={"pve-01": mock_node, "stale-node": mock_node},
        qemu={101: mock_qemu, 999: mock_qemu},
        lxc={202: mock_lxc, 888: mock_lxc},
    )

    updated_cache = pve_reconcile_status_cache(collection, cache)

    # Assert valid entries remain
    assert "pve-01" in updated_cache.nodes
    assert 101 in updated_cache.qemu
    assert 202 in updated_cache.lxc

    # Assert stale entries are evicted
    assert "stale-node" not in updated_cache.nodes
    assert 999 not in updated_cache.qemu
    assert 888 not in updated_cache.lxc

    # Assert None handling
    assert pve_reconcile_status_cache(None, cache) == cache
