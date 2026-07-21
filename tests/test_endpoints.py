"""Tests for Proxmox endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phais.endpoints import (
    AccessEndpoint,
    ClusterEndpoint,
    LXCStatusEndpoint,
    NodeEndpoint,
    QemuStatusEndpoint,
    TasksEndpoint,
)
from phais.exceptions import ProxmoxAPIError, ResourceNotFoundError
from phais.model.pve import (
    ClusterResourcesCollection,
    ClusterStatusCache,
    QemuResource,
    QemuStatus,
    ResourceStatus,
    ResourceType,
)


@pytest.mark.asyncio
async def test_unimplemented_stubs():
    """Hit the NotImplementedError branches for coverage."""
    mock_client = MagicMock()

    qemu_endpoint = NodeEndpoint(mock_client, "pve-01").qemu(101)
    with pytest.raises(NotImplementedError):
        await qemu_endpoint.status.status()

    with pytest.raises(NotImplementedError):
        qemu_endpoint.status.snapshot_create()

    lxc_endpoint = NodeEndpoint(mock_client, "pve-01").lxc(202)
    with pytest.raises(NotImplementedError):
        await lxc_endpoint.status.status()

    with pytest.raises(NotImplementedError):
        lxc_endpoint.status.snapshot_create()


@pytest.mark.asyncio
async def test_cluster_endpoint_resources(mock_pve_cluster_resources_raw):
    """Test ClusterEndpoint fetches and updates cache properly."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_pve_cluster_resources_raw)
    mock_client.status_cache = ClusterStatusCache()

    endpoint = ClusterEndpoint(mock_client)
    collection = await endpoint.resources()

    assert len(collection.resources) == 3
    mock_client.request.assert_called_with("GET", "cluster/resources")


@pytest.mark.asyncio
async def test_node_endpoint_actions():
    """Test dynamically generated node actions (PostAction)."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock()

    node_endpoint = NodeEndpoint(mock_client, "pve-01")

    # Call the property directly to invoke the PostAction
    await node_endpoint.reboot()
    mock_client.request.assert_called_with("POST", "nodes/pve-01/reboot", json_data={})

    await node_endpoint.startall()
    mock_client.request.assert_called_with(
        "POST", "nodes/pve-01/startall", json_data={}
    )


@pytest.mark.asyncio
async def test_qemu_endpoint_actions():
    """Test dynamically generated VM actions."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock()

    node_endpoint = NodeEndpoint(mock_client, "pve-01")
    qemu = node_endpoint.qemu(101)

    await qemu.status.start()
    mock_client.request.assert_called_with(
        "POST", "nodes/pve-01/qemu/101/status/start", json_data={}
    )


@pytest.mark.asyncio
async def test_agent_ping():
    """Test Qemu Agent Ping."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock()

    node_endpoint = NodeEndpoint(mock_client, "pve-01")
    agent = node_endpoint.qemu(101).agent

    result = await agent.ping()
    assert result is True
    mock_client.request.assert_called_with("POST", "nodes/pve-01/qemu/101/agent/ping")

    # Simulate failure
    mock_client.request.side_effect = ProxmoxAPIError("status", "message", "endpoint")
    assert await agent.ping() is False


@pytest.mark.asyncio
async def test_access_endpoint_permissions():
    """Test fetching and mapping ACL permissions."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value={"/vms/101": {"VM.PowerMgmt": 1}})

    endpoint = AccessEndpoint(mock_client)
    perms = await endpoint.permissions()

    assert perms.has_vm_permission(101, "VM.PowerMgmt") is True


@pytest.mark.asyncio
async def test_tasks_endpoint_filters():
    """Test task history with filters and await dunder."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=[{"upid": "task1"}])

    endpoint = TasksEndpoint(mock_client, "pve-01")
    tasks = await endpoint.get(typefilter="vzdump", limit=5)

    assert len(tasks) == 1
    mock_client.request.assert_called_with(
        "GET", "nodes/pve-01/tasks", params={"typefilter": "vzdump", "limit": 5}
    )


@pytest.mark.asyncio
async def test_node_endpoint_status_and_storage():
    """Test node-level fetchers."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock(
        side_effect=[
            {
                "uptime": 100,
                "cpu": 0.5,
                "idle": 0,
                "memory": {"total": 1, "used": 1, "free": 0},
                "swap": {"total": 1, "free": 1, "used": 0},
                "rootfs": {"total": 1, "used": 1, "free": 0},
                "cpuinfo": {
                    "cpus": 1,
                    "cores": 1,
                    "sockets": 1,
                    "model": "test",
                    "vendor": "test",
                },
                "pveversion": "8.0",
            },
            [{"storage": "local-lvm", "content": "images"}],
        ]
    )

    endpoint = NodeEndpoint(mock_client, "pve-01")

    status = await endpoint.status()
    assert status.uptime == 100

    storage = await endpoint.storage()
    assert storage[0]["storage"] == "local-lvm"


@pytest.mark.asyncio
async def test_lxc_qemu_current_fallback_logic():
    """Test the VM/LXC telemetry fallback if missing from cache."""
    mock_client = MagicMock()
    # Mocking a cluster resources response that contains our missing LXC
    mock_client.cluster.resources = AsyncMock()

    # Mock the direct request to lxc/qemu current
    mock_client.request = AsyncMock(
        return_value={
            "vmid": 202,
            "status": "running",
            "name": "test",
            "cpus": 1,
            "cpu": 0.5,
            "mem": 1,
            "maxmem": 1,
            "swap": 0,
            "maxswap": 0,
            "disk": 1,
            "maxdisk": 1,
            "diskread": 0,
            "diskwrite": 0,
            "netin": 0,
            "netout": 0,
            "uptime": 1,
        }
    )

    # Start with empty cache so pve_find_node_in_cache returns None initially
    mock_client.cluster_resources = None

    endpoint = NodeEndpoint(mock_client, "unknown").lxc(202)

    # We patch the helper so it fails the first time, but succeeds after cluster.resources() is called
    with patch("phais.endpoints.pve_find_node_in_cache", side_effect=[None, "pve-02"]):
        status = await endpoint.status.current()
        assert status.vmid == 202
        mock_client.cluster.resources.assert_called_once()
        mock_client.request.assert_called_with(
            "GET", "nodes/pve-02/lxc/202/status/current"
        )


@pytest.mark.asyncio
async def test_qemu_current_with_fallback():
    """Test Qemu current fetch handles cache misses."""
    client = MagicMock()
    client.cluster_resources = None  # Force cache miss

    # Mock the cluster.resources() fallback to "find" the node
    async def mock_cluster_resources():
        client.cluster_resources = ClusterResourcesCollection(
            resources=[
                QemuResource(
                    id="qemu/101",
                    vmid=101,
                    name="vm",
                    node="pve-02",
                    status=ResourceStatus.RUNNING,
                    template=0,
                    maxcpu=1,
                    maxmem=1,
                    maxdisk=1,
                    resource_type=ResourceType.QEMU,
                )
            ]
        )

    client.cluster.resources = AsyncMock(side_effect=mock_cluster_resources)

    # Mock the actual GET request payload
    client.request = AsyncMock(
        return_value={
            "vmid": 101,
            "status": "running",
            "qmpstatus": "running",
            "name": "vm",
            "cpus": 1,
            "cpu": 0.5,
            "mem": 1,
            "maxmem": 1,
            "disk": 1,
            "maxdisk": 1,
            "uptime": 100,
            "netin": 0,
            "netout": 0,
        }
    )

    endpoint = QemuStatusEndpoint(client, "pve-01", 101)
    status = await endpoint.current()

    assert isinstance(status, QemuStatus)
    assert status.status == "running"  # Pulled from mocked fallback
    client.cluster.resources.assert_awaited_once()


@pytest.mark.asyncio
async def test_lxc_current_missing_node_exception():
    """Ensure LXC current throws a KeyError if the VMID doesn't exist anywhere."""
    client = MagicMock()
    client.cluster_resources = None
    client.cluster.resources = AsyncMock()  # Fallback finds nothing

    endpoint = LXCStatusEndpoint(client, "pve-01", 999)
    with pytest.raises(ResourceNotFoundError, match="could not be located anywhere"):
        await endpoint.current()


@pytest.mark.asyncio
async def test_access_permissions():
    """Test permission map endpoint."""
    client = MagicMock()
    client.request = AsyncMock(return_value={"/vms/101": {"VM.PowerMgmt": 1}})

    endpoint = AccessEndpoint(client)
    perms = await endpoint.permissions()

    assert perms.has_vm_permission(101, "VM.PowerMgmt") is True


@pytest.mark.asyncio
async def test_tasks_endpoint():
    """Test task history retrieval with parameters."""
    client = MagicMock()
    client.request = AsyncMock(return_value=[{"upid": "UPID:pve-01..."}])

    endpoint = TasksEndpoint(client, "pve-01")

    # Test specific params
    await endpoint.get(typefilter="vzdump", limit=50)
    client.request.assert_called_with(
        "GET", "nodes/pve-01/tasks", params={"typefilter": "vzdump", "limit": 50}
    )


@pytest.mark.asyncio
async def test_node_status_and_storage():
    """Test Node status and storage retrieval."""
    client = MagicMock()
    endpoint = NodeEndpoint(client, "pve-01")
    client.request = AsyncMock()

    # Mock Node Status payload
    client.request.return_value = {
        "uptime": 100,
        "cpu": 0.1,
        "idle": 90,
        "memory": {"total": 1, "used": 1, "free": 1},
        "swap": {"total": 1, "used": 1, "free": 1},
        "rootfs": {"total": 1, "used": 1, "free": 1},
        "cpuinfo": {"cpus": 1, "cores": 1, "sockets": 1, "model": "a", "vendor": "b"},
        "pveversion": "8.0",
    }

    status = await endpoint.status()
    assert status.uptime == 100

    # Mock Storage payload
    client.request = AsyncMock(return_value=[{"storage": "local-lvm"}])
    storage = await endpoint.storage()
    assert storage[0]["storage"] == "local-lvm"
