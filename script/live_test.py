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
        pve = phais.Backend(
            session=session,
            host=args.host,
            user=args.user,
            password=args.password,
            verify_ssl=args.verify_ssl,
        )

        cluster = await pve.connect()
        _LOGGER.warning(
            "Successfully connected with %s cluster resources.", len(cluster.resources)
        )

        try:
            cluster = await pve.cluster.resources()
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
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            node_status = await pve.nodes("pvex").status()
            _LOGGER.warning("Successfully retrieved node resource")
            _LOGGER.warning(node_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            vm_status = await pve.nodes("pvex").qemu(102).status.current()
            _LOGGER.warning("Successfully retrieved qemu resource")
            _LOGGER.warning(vm_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")

        try:
            lxc_status = await pve.nodes("pvex").lxc(501).status.current()
            _LOGGER.warning("Successfully retrieved lxc resource")
            _LOGGER.warning(lxc_status)
        except Exception:
            _LOGGER.exception("Failed to fetch resources.")


if __name__ == "__main__":
    asyncio.run(main())
