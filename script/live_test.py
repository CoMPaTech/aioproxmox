#!/usr/bin/env python
"""Live testing for phais."""

import argparse
import asyncio
import logging

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

    async with aiohttp.ClientSession() as session:
        cluster = phais.Backend(
            session=session,
            host=args.host,
            user=args.user,
            password=args.password,
            verify_ssl=args.verify_ssl,
        )

        if hasattr(cluster.auth, "async_init"):
            await cluster.auth.async_init()

        try:
            cluster_resources = await cluster.pve_cluster_resources()
            resources = cluster_resources.resources
            _LOGGER.warning(
                "Successfully retrieved %s cluster resources.", len(resources)
            )
            for resource in resources:
                _LOGGER.warning(
                    "- %s: %s (%s) ",
                    resource.resource_type,
                    resource.id,
                    resource.status,
                )
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            node_status = await cluster.pve_node_status("pvex")
            _LOGGER.warning("Successfully retrieved node resource")
            _LOGGER.warning(node_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            vm_status = await cluster.pve_qemu_status(102)
            _LOGGER.warning("Successfully retrieved qemu resource")
            _LOGGER.warning(vm_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            lxc_status = await cluster.pve_lxc_status(501)
            _LOGGER.warning("Successfully retrieved lxc resource")
            _LOGGER.warning(lxc_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")


if __name__ == "__main__":
    asyncio.run(main())
