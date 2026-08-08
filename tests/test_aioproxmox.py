"""Aynschronous Proxmox library tests."""

import logging

from aioproxmox.model.pve import OperationalStatus


def test_enum_fallback_mechanism(caplog):
    """Ensure global StrEnum overrides convert unexpected payloads without exceptions."""
    with caplog.at_level(logging.WARNING):
        fallback_value = OperationalStatus("_missing_val_test_")

        assert fallback_value == OperationalStatus.UNKNOWN
        assert "Unknown Proxmox resource status encountered" in caplog.text
