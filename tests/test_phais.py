"""Proxmox Home Assistant Integration Service."""

import logging

from phais.model.pve import ResourceStatus


def test_enum_fallback_mechanism(caplog):
    """Ensure global StrEnum overrides convert unexpected payloads without exceptions."""
    with caplog.at_level(logging.WARNING):
        fallback_value = ResourceStatus("_missing_val_test_")

        assert fallback_value == ResourceStatus.UNKNOWN
        assert "Unknown Proxmox resource status encountered" in caplog.text
