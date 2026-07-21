"""Helpers for Proxmox."""

import logging

from .model.pve import (
    ClusterResourcesCollection,
    ClusterStatusCache,
    ContainerResource,
    NodeResource,
    QemuResource,
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
        if isinstance(res, (QemuResource, ContainerResource)) and res.vmid == vmid:
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
    active_qemu_vmids = set()
    active_lxc_vmids = set()

    for res in cluster_resources.resources:
        match res:
            case NodeResource():
                active_nodes.add(res.node)
            case QemuResource():
                active_qemu_vmids.add(res.vmid)
            case ContainerResource():
                active_lxc_vmids.add(res.vmid)

    stale_nodes = set(status_cache.nodes.keys()) - active_nodes
    for node in stale_nodes:
        _LOGGER.info("Evicting decommissioned node from cache: %s", node)
        del status_cache.nodes[node]

    stale_vms = set(status_cache.qemu.keys()) - active_qemu_vmids
    for vmid in stale_vms:
        _LOGGER.info("Evicting deleted QEMU VMID from cache: %d", vmid)
        del status_cache.qemu[vmid]

    stale_lxcs = set(status_cache.lxc.keys()) - active_lxc_vmids
    for vmid in stale_lxcs:
        _LOGGER.info("Evicting deleted LXC ID from cache: %d", vmid)
        del status_cache.lxc[vmid]

    return status_cache
