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

## Development Diagnostics

The repository provides a diagnostic CLI utility to verify authentication mechanics, cookie/ticket attachment, and data serialization against live systems.

### Running the Live Test Script

Execute the script from the root directory by providing your targeted cluster parameters:

```bash
scripts/live_test.py <host-ip-or-fqdn> "<user@realm>" "<password>"
```
