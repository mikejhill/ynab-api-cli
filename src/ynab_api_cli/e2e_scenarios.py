"""Compose read acceptance and reversible mutation scenario services."""

from __future__ import annotations

from ynab_api_cli.e2e_assertions import Assertions
from ynab_api_cli.e2e_filtered_reads import FilteredReads
from ynab_api_cli.e2e_fixtures import Fixtures
from ynab_api_cli.e2e_resource_writes import ResourceWrites
from ynab_api_cli.e2e_transaction_reads import TransactionReads
from ynab_api_cli.e2e_transaction_writes import TransactionWrites


class Scenarios:
    """Run the same explicit scenario contract for local and CI acceptance."""

    def __init__(self, fixtures: Fixtures) -> None:
        self._assertions = Assertions(fixtures)
        self._transactions = TransactionReads(self._assertions)
        self._filtered = FilteredReads(self._assertions)
        self._transaction_writes = TransactionWrites(self._assertions)
        self._resources = ResourceWrites(self._assertions)

    @property
    def passed(self) -> list[str]:
        """Return fixed labels of assertions that actually passed."""
        return self._assertions.passed

    def reads(self) -> None:
        """Verify the complete required baseline contract."""
        counterpart = self._transactions.run()
        self._filtered.run(counterpart)

    def mutations(self) -> None:
        """Verify write lifecycles, restore their state, and recheck baseline reads."""
        self._transaction_writes.run()
        self._resources.scheduled()
        self._transaction_writes.bulk()
        self._resources.resources()
        self._resources.budget()
        self.reads()

    def remaining_reads(self) -> None:
        """Validate all other selected-plan reads with available fixture IDs."""
        self._filtered.remaining_reads()
