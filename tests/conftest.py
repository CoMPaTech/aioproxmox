"""Testing."""

import pytest


@pytest.fixture
def mock_pve_cluster_resources_raw() -> list[dict]:
    """Represents raw data payload from a single-node Proxmox cluster."""
    return [
        {
            "id": "node/pve-01",
            "node": "pve-01",
            "type": "node",
            "status": "online",
            "cpu": 0.042,
            "maxcpu": 16,
            "mem": 34359738368,
            "maxmem": 68719476736,
            "disk": 52428800000,
            "maxdisk": 100000000000,
            "uptime": 86400,
            "cgroup-mode": 2,
            "level": "administrator",
        },
        {
            "id": "qemu/101",
            "vmid": 101,
            "name": "homeassistant-core",
            "node": "pve-01",
            "type": "qemu",
            "status": "running",
            "template": 0,
            "maxcpu": 4,
            "maxmem": 8589934592,
            "maxdisk": 34359738368,
            "cpu": 0.12,
            "mem": 4294967296,
            "uptime": 43200,
            "tags": "homeautomation;production;important",
        },
        {
            "id": "storage/pve-01/local-lvm",
            "storage": "local-lvm",
            "node": "pve-01",
            "type": "storage",
            "status": "available",
            "plugintype": "lvmthin",
            "shared": 0,
            "content": "rootdir,images",
            "disk": 214748364800,
            "maxdisk": 500000000000,
        },
    ]


@pytest.fixture
def mock_pve_dual_node_cluster_raw() -> list[dict]:
    """Represents raw data payload from a 2-node cluster with mixed VMs and LXCs."""
    return [
        # --- Physical Nodes ---
        {
            "id": "node/pve-01",
            "node": "pve-01",
            "type": "node",
            "status": "online",
            "cpu": 0.1,
            "maxcpu": 8,
            "mem": 16000,
            "maxmem": 32000,
            "disk": 1000,
            "maxdisk": 2000,
            "uptime": 100,
        },
        {
            "id": "node/pve-02",
            "node": "pve-02",
            "type": "node",
            "status": "online",
            "cpu": 0.1,
            "maxcpu": 8,
            "mem": 16000,
            "maxmem": 32000,
            "disk": 1000,
            "maxdisk": 2000,
            "uptime": 100,
        },
        # --- Virtual Machines (QEMU) ---
        {
            "id": "qemu/101",
            "vmid": 101,
            "name": "prod-app",
            "node": "pve-01",
            "type": "qemu",
            "status": "running",
            "template": 0,
            "maxcpu": 2,
            "maxmem": 4000,
            "maxdisk": 40,
        },
        {
            "id": "qemu/102",
            "vmid": 102,
            "name": "dev-db",
            "node": "pve-02",
            "type": "qemu",
            "status": "running",
            "template": 0,
            "maxcpu": 2,
            "maxmem": 4000,
            "maxdisk": 40,
        },
        # --- Linux Containers (LXC) ---
        {
            "id": "lxc/201",
            "vmid": 201,
            "name": "nginx-proxy",
            "node": "pve-01",
            "type": "lxc",
            "status": "running",
            "template": 0,
            "maxcpu": 1,
            "maxmem": 1000,
            "maxdisk": 10,
        },
        {
            "id": "lxc/202",
            "vmid": 202,
            "name": "mqtt-broker",
            "node": "pve-02",
            "type": "lxc",
            "status": "running",
            "template": 0,
            "maxcpu": 1,
            "maxmem": 1000,
            "maxdisk": 10,
        },
    ]
