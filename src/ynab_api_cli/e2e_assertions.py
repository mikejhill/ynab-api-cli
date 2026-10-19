"""Shared semantic assertions and readback context for acceptance services."""

from __future__ import annotations

from collections.abc import Mapping

from ynab_api_cli.contract import Contract
from ynab_api_cli.e2e_fixtures import Expectations, Fixtures
from ynab_api_cli.types import JsonValue


class Assertions:
    """Record fixed assertion labels and keep financial values out of errors."""

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures
        self.session = fixtures.session
        self.ids = fixtures.ids
        self.passed: list[str] = []

    def check(self, actual: object, expected: object, label: str) -> None:
        """Record an assertion only after its independent expectation passes."""
        Expectations.equal(actual, expected, label)
        self.passed.append(label)

    def record(
        self, operation: str, field: str, path: Mapping[str, object]
    ) -> dict[str, JsonValue]:
        """Read one record through the CLI and independent response validation."""
        return Contract.object(self.session.invoke(operation, path=path)[field])
