"""Isolated fixtures that never read real YNAB credentials."""

from __future__ import annotations

from pathlib import Path

import pytest

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.security import FileSecurity


@pytest.fixture
def contract() -> Contract:
    """Return the bundled reviewed contract."""
    return Contract()


@pytest.fixture
def store(tmp_path: Path) -> ConfigStore:
    """Create isolated fake credentials using real platform protection."""
    result = ConfigStore(tmp_path / "ynab-api-cli", FileSecurity())
    result.configure("synthetic-test-token")
    return result
