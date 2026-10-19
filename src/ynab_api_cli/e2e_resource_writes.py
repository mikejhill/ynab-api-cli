"""Reversible category, payee, group, budget, and scheduled lifecycles."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from ynab_api_cli.contract import Contract
from ynab_api_cli.e2e_assertions import Assertions
from ynab_api_cli.e2e_fixtures import Expectations, Fixtures
from ynab_api_cli.types import JsonValue


class ResourceWrites:
    """Reversible category, payee, group, budget, and scheduled lifecycles."""

    def __init__(self, assertions: Assertions) -> None:
        self.assertions = assertions
        self.fixtures = assertions.fixtures
        self.session = assertions.session
        self.ids = assertions.ids

    def resources(self) -> None:
        """Verify reversible updates only within the fixture namespace."""
        category_path: Mapping[str, object] = {"category_id": self.ids["category"]}
        before = self.assertions.record("getCategoryById", "category", category_path)
        self.session.invoke(
            "updateCategory",
            path=category_path,
            body={"category": {"note": Fixtures.MEMO}},
        )
        self.assertions.check(
            self.assertions.record("getCategoryById", "category", category_path).get(
                "note"
            ),
            Fixtures.MEMO,
            "category-update-readback",
        )
        self.session.invoke(
            "updateCategory",
            path=category_path,
            body={"category": {"note": before.get("note")}},
        )
        self.assertions.check(
            self.assertions.record("getCategoryById", "category", category_path).get(
                "note"
            ),
            before.get("note"),
            "category-note-restored",
        )
        payee_path: dict[str, object] = {"payee_id": self.ids["payee"]}
        self.session.invoke(
            "updatePayee",
            path=payee_path,
            body={"payee": {"name": Fixtures.PREFIX + "-updated"}},
        )
        self.assertions.check(
            self.assertions.record("getPayeeById", "payee", payee_path).get("name"),
            Fixtures.PREFIX + "-updated",
            "payee-update-readback",
        )
        self.session.invoke(
            "updatePayee", path=payee_path, body={"payee": {"name": Fixtures.PREFIX}}
        )
        self.assertions.check(
            self.assertions.record("getPayeeById", "payee", payee_path).get("name"),
            Fixtures.PREFIX,
            "payee-name-restored",
        )
        group_path: dict[str, object] = {"category_group_id": self.ids["group"]}
        for suffix, label in (
            ("-updated", "group-update-readback"),
            ("", "group-name-restored"),
        ):
            name = Fixtures.PREFIX + suffix
            self.session.invoke(
                "updateCategoryGroup",
                path=group_path,
                body={"category_group": {"name": name}},
            )
            groups = Expectations.records(
                self.session.invoke("getCategories")["category_groups"]
            )
            group = Expectations.named(groups, name)
            self.assertions.check(
                group.get("id") if group is not None else None, self.ids["group"], label
            )

    def scheduled(self) -> None:
        """Create, update, read, and remove one separate scheduled transaction."""
        payload: dict[str, JsonValue] = {
            "account_id": self.ids["source"],
            "date": (datetime.now(UTC).date() + timedelta(days=1460)).isoformat(),
            "amount": -1000,
            "frequency": "monthly",
            "memo": "e2e:" + uuid4().hex,
        }
        created = Contract.object(
            self.session.invoke(
                "createScheduledTransaction", body={"scheduled_transaction": payload}
            )["scheduled_transaction"]
        )
        identifier = str(created["id"])
        path: Mapping[str, object] = {"scheduled_transaction_id": identifier}
        self.assertions.check(
            self.assertions.record(
                "getScheduledTransactionById", "scheduled_transaction", path
            ).get("amount"),
            -1000,
            "scheduled-create-readback",
        )
        self.session.invoke(
            "updateScheduledTransaction",
            path=path,
            body={"scheduled_transaction": payload | {"amount": -2000}},
        )
        self.assertions.check(
            self.assertions.record(
                "getScheduledTransactionById", "scheduled_transaction", path
            ).get("amount"),
            -2000,
            "scheduled-update-readback",
        )
        self.session.invoke("deleteScheduledTransaction", path=path)
        remaining = Expectations.records(
            self.session.invoke("getScheduledTransactions")["scheduled_transactions"]
        )
        self.assertions.check(
            any(
                item.get("id") == identifier and item.get("deleted") is not True
                for item in remaining
            ),
            False,  # noqa: FBT003 - expected JSON value.
            "scheduled-deleted",
        )

    def budget(self) -> None:
        """Change monthly budgeting, verify it, and restore the known baseline."""
        category_path: Mapping[str, object] = {
            "month": Fixtures.MONTH,
            "category_id": self.ids["category"],
        }
        self.session.invoke(
            "updateMonthCategory",
            path=category_path,
            body={"category": {"budgeted": 2000}},
        )
        self.assertions.check(
            self.assertions.record(
                "getMonthCategoryById", "category", category_path
            ).get("budgeted"),
            2000,
            "budget-update-readback",
        )
        self.session.invoke(
            "updateMonthCategory",
            path=category_path,
            body={"category": {"budgeted": 1000}},
        )
        self.assertions.check(
            self.assertions.record(
                "getMonthCategoryById", "category", category_path
            ).get("budgeted"),
            1000,
            "budget-restored",
        )
