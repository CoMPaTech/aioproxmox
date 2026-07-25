"""Helpers for Proxmox."""

import logging

from .model.pve import (
    ClusterContainerResource,
    ClusterQemuResource,
    ClusterResourcesCollection,
    ClusterStatusCache,
    NodeResource,
    StorageResource,
)

_LOGGER = logging.getLogger(__name__)


def pve_find_node_in_cache(
    cluster_resources: ClusterResourcesCollection,
    vmid: int,
) -> str | None:
    """Helper to extract the node location from the resource model instances."""
    if not cluster_resources:
        return None
    for res in cluster_resources.resources:
        if (
            isinstance(res, (ClusterQemuResource, ClusterContainerResource))
            and res.vmid == vmid
        ):
            return str(res.node)
    return None


def pve_reconcile_status_cache(
    cluster_resources: ClusterResourcesCollection,
    status_cache: ClusterStatusCache,
) -> ClusterStatusCache:
    """Purge stale telemetry models from cache when vanished from cluster resources."""
    if not cluster_resources:
        return status_cache

    active_nodes = set()
    active_qemu = set()
    active_lxc = set()
    active_storage = set()

    for res in cluster_resources.resources:
        match res:
            case NodeResource():
                active_nodes.add(res.node)
            case ClusterQemuResource():
                active_qemu.add(res.vmid)
            case ClusterContainerResource():
                active_lxc.add(res.vmid)
            case StorageResource():
                active_storage.add(f"{res.node}:{res.storage}")

    stale_nodes = set(status_cache.nodes.keys()) - active_nodes
    for node in stale_nodes:
        _LOGGER.info("Evicting decommissioned node from cache: %s", node)
        del status_cache.nodes[node]

    stale_vms = set(status_cache.qemu.keys()) - active_qemu
    for vmid in stale_vms:
        _LOGGER.info("Evicting deleted QEMU VMID from cache: %d", vmid)
        del status_cache.qemu[vmid]

    stale_lxcs = set(status_cache.lxc.keys()) - active_lxc
    for vmid in stale_lxcs:
        _LOGGER.info("Evicting deleted LXC ID from cache: %d", vmid)
        del status_cache.lxc[vmid]

    for key in set(status_cache.storage) - active_storage:
        _LOGGER.info("Evicting deleted storage from cache: %d", key)
        del status_cache.storage[key]

    return status_cache
