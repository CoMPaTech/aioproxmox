#!/usr/bin/env python
"""Live testing for phais."""

import argparse
import asyncio
import logging
import time

import aiohttp

import phais

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Quick example script."""
    parser = argparse.ArgumentParser(description="Example")
    parser.add_argument("host", type=str, help="IP or FQDN.")
    parser.add_argument("user", type=str, help="User as user(name)@{realm}.")
    parser.add_argument("password", type=str, help="User password")
    parser.add_argument("--verify_ssl", type=bool, default=False, help="Verify SSL")
    args = parser.parse_args()

    start_time = time.monotonic()
    diff_time = start_time
    _LOGGER.warning("Marker / Total time / Diff. time / Progress")

    def call_time(annotate: str = "Mark") -> None:
        """Call out time lapsed."""
        nonlocal diff_time
        _LOGGER.warning(
            "Timing / %7.2f ms / %7.2f ms / %s",
            (time.monotonic() - start_time) * 1000,
            (time.monotonic() - diff_time) * 1000,
            annotate,
        )
        diff_time = time.monotonic()

    async with aiohttp.ClientSession() as session:
        call_time("Init")
        pve = phais.ProxmoxVE(
            session=session,
            host=args.host,
            user=args.user,
            password=args.password,
            verify_ssl=args.verify_ssl,
        )

        call_time("Setup")
        test_node: str | None = None
        cluster = await pve.connect()
        call_time("Connect")
        _LOGGER.warning(
            "Successfully connected with %s cluster resources.", len(cluster.resources)
        )

        stopped_vm: int | None = None
        started_vm: int | None = None
        started_lxc: int | None = None

        call_time("Cluster Resources")
        _LOGGER.warning(
            "Successfully updated %s cluster resources.", len(cluster.resources)
        )
        for resource in cluster.resources:
            _LOGGER.warning(
                "- %s: %s (%s) ",
                resource.resource_type,
                resource.id,
                resource.status,
            )
            if not test_node and resource.resource_type == "node":
                test_node = resource.id.split("/")[-1]
            # Find first stopped QEMU VM
            if (
                not stopped_vm
                and isinstance(resource, phais.model.pve.ClusterQemuResource)
                and resource.status == phais.model.pve.OperationalStatus.STOPPED
            ):
                stopped_vm = resource.vmid

            # Find first running QEMU VM
            if (
                not started_vm
                and isinstance(resource, phais.model.pve.ClusterQemuResource)
                and resource.status == phais.model.pve.OperationalStatus.RUNNING
            ):
                started_vm = resource.vmid

            # Find first running LXC Container
            if (
                not started_lxc
                and isinstance(resource, phais.model.pve.ClusterContainerResource)
                and resource.status == phais.model.pve.OperationalStatus.RUNNING
            ):
                started_lxc = resource.vmid

        call_time("Resource printing done")
        _LOGGER.warning("Using dynamic testing on:")
        _LOGGER.warning("  Stopped VM  = %s", stopped_vm)
        _LOGGER.warning("  Started VM  = %s", started_vm)
        _LOGGER.warning("  Started LXC = %s", started_lxc)
        call_time("Time")

        if not test_node:
            raise ValueError("Test node not found")

        _LOGGER.warning("Fetching Qemu and LXC lists")
        try:
            qemu = await pve.nodes(test_node).qemu_all()
            call_time("Qemu List")
            _LOGGER.warning("Successfully retrieved Qemu resources")
            _LOGGER.warning([vm.name for vm in qemu])
        except Exception:
            _LOGGER.exception("Failed to fetch Qemu resources.")
        try:
            lxc = await pve.nodes(test_node).lxc_all()
            call_time("LXC List")
            _LOGGER.warning("Successfully retrieved LXC resources")
            _LOGGER.warning([container.name for container in lxc])
        except Exception:
            _LOGGER.exception("Failed to fetch LXC resources.")
        call_time("Qemu/LXC listing done")

        _LOGGER.warning("Cached node resource")
        _LOGGER.warning(pve.cluster_cache.nodes)
        try:
            node_status = await pve.nodes(test_node).status()
            call_time("Node Status")
            _LOGGER.warning("Successfully retrieved node resource")
            _LOGGER.warning(node_status)
        except Exception:
            _LOGGER.exception("Failed to fetch nodes.")

        try:
            vm_status = await pve.nodes(test_node).qemu(102).status.current()
            call_time("VM Status")
            _LOGGER.warning("Successfully retrieved qemu resource")
            _LOGGER.warning(vm_status)
        except Exception:
            _LOGGER.exception("Failed to fetch qemu/vm.")

        try:
            lxc_status = await pve.nodes(test_node).lxc(501).status.current()
            call_time("LXC")
            _LOGGER.warning("Successfully retrieved lxc resource")
            _LOGGER.warning(lxc_status)
        except Exception:
            _LOGGER.exception("Failed to fetch lxc.")

        call_time("Check existing capabilities")
        _LOGGER.warning("Capabilities")
        _LOGGER.warning(pve.auth.capabilities)
        call_time("Mark time")

        try:
            permissions = await pve.access.permissions()
            call_time("Permissions fetch")
            _LOGGER.warning("Successfully retrieved permissions resource")
            _LOGGER.warning(permissions)
        except Exception:
            _LOGGER.exception("Failed to fetch permissions.")

        try:
            storage = await pve.nodes(test_node).storage()
            call_time("Storage")
            _LOGGER.warning("Successfully retrieved storage resource")
            _LOGGER.warning(storage)
        except Exception:
            _LOGGER.exception("Failed to fetch storage.")

        try:
            backups = await pve.nodes(test_node).tasks(typefilter="vzdump", limit=1)
            call_time("Backups")
            _LOGGER.warning("Successfully retrieved tasks resource")
            _LOGGER.warning(backups)
        except Exception:
            _LOGGER.exception("Failed to fetch backup task info.")

        call_time("Time")
        if started_vm:
            call_time("Guest Agent running VM start")
            agent_status = await pve.nodes(test_node).qemu(started_vm).agent.ping()
            call_time("Guest Agent running VM complete")
            _LOGGER.warning("Started VM result: %s", agent_status)
        if stopped_vm:
            call_time("Guest Agent stopped VM start")
            agent_status = await pve.nodes(test_node).qemu(stopped_vm).agent.ping()
            call_time("Guest Agent stopped VM complete")
            _LOGGER.warning("Stopped VM result: %s", agent_status)

        if started_vm or stopped_vm:
            call_time("Time")


if __name__ == "__main__":
    asyncio.run(main())
