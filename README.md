# Proxmox Home Assistant Integration Service

An asynchronous, type-safe Python client tailored for extracting raw performance telemetry out of Proxmox VE clusters, nodes, and guests.

## The Backstory: Why "PHAIS"?

**PHAISE** stands for **Proxmox Home Assistant Integration Service**.

But there is an intentional double meaning here: **it is hopefully just a PHASE.**

This library was built out of necessity because existing ecosystem integrations and underlying client libraries have structural limitations—whether they are synchronous bottlenecks, missing granular unnested endpoint layouts, or lacking strict runtime type enforcement via tools like Mashumaro. PHAIS serves as our high-performance bridge today while we wait for mainstream upstream libraries to catch up, open up, or accept modern async paradigms. Once they do, this phase can comfortably conclude.

## Features

* **Strict Asynchronous Execution:** Native `aiohttp` implementation designed never to block the event loop.
* **Unified REST Client:** Centralized HTTP architecture managing internal auth tickets, cookie construction, and CSRF token propagation seamlessly.
* **Granular Telemetry Models:** Distinct dataclasses separating cluster maps from deep host (`NodeStatus`), VM (`QemuStatus`), and container (`LXCStatus`) sensor profiles.
* **Smart Reconciliation:** Automated cache pruning to instantly evict vanished or decommissioned resources from tracking tables using fast set operations.

## Performance

PVE calls can be intense, the `live_test.py` script adds basic timing, especially storage is expensive. Example for a one-node cluster with only local storage:

```text
Marker / Total time / Diff. time / Progress
Timing /    0.12 ms /    0.12 ms / Init
Timing /    0.17 ms /    0.01 ms / Setup
Timing /   61.20 ms /   61.01 ms / Connect
Timing /   62.82 ms /    1.57 ms / Cluster Resources
Timing /   63.00 ms /    0.14 ms / Resource printing done
Timing /   64.72 ms /    1.72 ms / Node Status
Timing /   70.25 ms /    5.49 ms / VM Status
Timing /   81.97 ms /   11.69 ms / LXC
Timing /   82.07 ms /    0.04 ms / Check existing capabilities
Timing /   82.15 ms /    0.06 ms / Mark time
Timing /   85.69 ms /    3.51 ms / Permissions fetch
Timing / 3268.02 ms / 3182.28 ms / Storage
Timing / 3274.38 ms /    6.29 ms / Backups
Timing / 3274.50 ms /    0.06 ms / Starting agent tests
Timing / 3274.52 ms /    0.00 ms / Alive VM
Timing / 3423.25 ms /  148.70 ms / Stopped VM
Timing / 3429.48 ms /    6.22 ms / Completed agent tests
Timing / 3429.51 ms /    0.00 ms / Time
```

## Usage

The library provides a modern, fluent interface built on asyncio and aiohttp, designed to mirror the structure of the Proxmox VE API while maintaining strict type safety via dataclasses.

Instead of passing endpoints via string formatting or multi-level item lookups, phais exposes clean, chainable endpoint paths. All data responses are fully validated dataclass objects rather than raw nested dictionaries.

```python
import asyncio
import aiohttp
import phais

async def main():
    async with aiohttp.ClientSession() as session:
        # Initialize the type-safe client backend
        pve = phais.ProxmoxVE(
            session=session,
            host="192.168.1.100",
            user="root@pam",
            password="your_secure_password",
            verify_ssl=False
        )

        cluster = await pve.connect()
        print(f"Connected to cluster with: {len(cluster.resources)} resources")

        lxc_status = await pve.nodes("pvex").lxc(501).status.current()
        print(f"Container Memory: {lxc_status.mem} bytes")

        cluster_resources = await pve.cluster.resources()
        print(f"Total cluster resources tracked: {len(cluster_resources.resources)}")

        node_status = await pve.nodes("pvex").status()
        print(f"Node CPU usage: {node_status.cpu * 100}%")

        vm_status = await pve.nodes("pvex").qemu(102).status.current()
        print(f"VM {vm_status.name} Status: {vm_status.status}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Contrast from Proxmoxer

| Feature | `proxmoxer` (Generic String Wrapper) | `phais` (Type-Safe Telemetry Client) |
| :--- | :--- | :--- |
| **I/O Strategy** | Synchronous (blocks the event loop) | Native Asynchronous (`aiohttp`) |
| **Path Navigation** | Verbatim endpoint strings / properties | Fluid, chainable endpoint paths |
| **Terminal Calls** | Explicit method tags required (`.get()`) | Direct execution or explicit telemetry targets |
| **Data Format** | Untyped primitives (`dict` / `list`) | Validated `Mashumaro` Dataclasses |

```python
"""Example implementation, see scripts/live_test.py for more examples."""
from proxmoxer import ProxmoxAPI

# Initialize synchronous client
proxmox = ProxmoxAPI(
    "192.168.1.100",
    user="root@pam",
    password="your_secure_password",
    verify_ssl=False
)

# 1. Fetch cluster resources (returns raw lists of dicts)
resources = proxmox.cluster.resources.get()
print(f"Total cluster resources tracked: {len(resources)}")

# 2. Fetch specific physical node status
node_status = proxmox.nodes("pvex").status.get()
print(f"Node CPU usage: {node_status.get('cpu', 0) * 100}%")

# 3. Fetch QEMU VM status
vm_status = proxmox.nodes("pvex").qemu(102).status.current.get()
print(f"VM Status: {vm_status.get('status')}")

# 4. Fetch LXC container status
lxc_status = proxmox.nodes("pvex").lxc(501).status.current.get()
print(f"Container Memory: {lxc_status.get('mem')} bytes")
```

## Development Diagnostics

The repository provides a diagnostic CLI utility to verify authentication mechanics, cookie/ticket attachment, and data serialization against live systems.

### Running the Live Test Script

Execute the script from the root directory by providing your targeted cluster parameters:

```bash
scripts/live_test.py <host-ip-or-fqdn> "<user@realm>" "<password>"
```
