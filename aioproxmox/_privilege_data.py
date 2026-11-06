"""What Proxmox checks before it answers - generated, do not edit.

Written by `script/generate_privileges.py` out of `schema/pve_api.json`,
which comes from Proxmox's own API schema. One entry per route this
library calls that states a check; the entry is the alternatives that
satisfy it, and each alternative is the ACL path, the privileges, and
whether one of them is enough.

    ("GET", "nodes/{node}/apt/update"): ((("/nodes/{node}", ("Sys.Modify",), False),),)

`aioproxmox.privileges` is the way to read this.
"""

CHECKS: dict[tuple[str, str], tuple[tuple[str, tuple[str, ...], bool], ...]] = {
    ("GET", "nodes/{node}/apt/update"): (("/nodes/{node}", ("Sys.Modify",), False),),
    ("GET", "nodes/{node}/lxc/{vmid}/status/current"): (
        ("/vms/{vmid}", ("VM.Audit",), False),
    ),
    ("GET", "nodes/{node}/qemu/{vmid}/status/current"): (
        ("/vms/{vmid}", ("VM.Audit",), False),
    ),
    ("GET", "nodes/{node}/status"): (("/nodes/{node}", ("Sys.Audit",), False),),
    ("POST", "nodes/{node}/lxc/{vmid}/snapshot"): (
        ("/vms/{vmid}", ("VM.Snapshot",), False),
    ),
    ("POST", "nodes/{node}/lxc/{vmid}/status/reboot"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/lxc/{vmid}/status/start"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/lxc/{vmid}/status/stop"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/agent/ping"): (
        ("/vms/{vmid}", ("VM.GuestAgent.Audit", "VM.GuestAgent.Unrestricted"), True),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/snapshot"): (
        ("/vms/{vmid}", ("VM.Snapshot",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/reboot"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/reset"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/resume"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/shutdown"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/start"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/stop"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/qemu/{vmid}/status/suspend"): (
        ("/vms/{vmid}", ("VM.PowerMgmt",), False),
    ),
    ("POST", "nodes/{node}/status"): (("/nodes/{node}", ("Sys.PowerMgmt",), False),),
}
