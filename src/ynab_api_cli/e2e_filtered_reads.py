"""Filter, schedule, budgeting, and remaining read contracts."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from ynab_api_cli.e2e_assertions import Assertions
from ynab_api_cli.e2e_fixtures import Expectations, Fixtures


class FilteredReads:
    """Filter, schedule, budgeting, and remaining read contracts."""

    def __init__(self, assertions: Assertions) -> None:
        self.assertions = assertions
        self.fixtures = assertions.fixtures
        self.session = assertions.session
        self.ids = assertions.ids

    def run(self, counterpart: str) -> None:
        """Verify filters, budgeting, schedules, selection, and unchanged deltas."""
        for operation, path in (
            ("getTransactionsByPayee", {"payee_id": self.ids["payee"]}),
            ("getTransactionsByCategory", {"category_id": self.ids["category"]}),
            ("getTransactionsByMonth", {"month": Fixtures.MONTH}),
        ):
            entries = Expectations.records(
                self.session.invoke(operation, path=path)["transactions"]
            )
            self.assertions.check(
                self.ids["main_transaction"] in {item.get("id") for item in entries},
                True,  # noqa: FBT003 - expected JSON value.  # noqa: FBT003 - expected JSON value.
                operation + "-contains-main",
            )
            if operation == "getTransactionsByPayee":
                self.assertions.check(
                    {item.get("id") for item in entries},
                    {self.ids["main_transaction"]},
                    "payee-exact-filter",
                )
            if operation == "getTransactionsByCategory":
                self.assertions.check(
                    sorted(int(str(item["amount"])) for item in entries),
                    [-12000, -600, -400],
                    "category-split-filter",
                )
                self.assertions.check(
                    {item.get("category_id") for item in entries},
                    {self.ids["category"]},
                    "category-only-filter",
                )
        other_month = Expectations.records(
            self.session.invoke("getTransactionsByMonth", path={"month": "2026-02-01"})[
                "transactions"
            ]
        )
        self.assertions.check(
            any(
                item.get("id")
                in {
                    self.ids[role + "_transaction"]
                    for role in ("main", "zero", "split", "transfer")
                }
                | {counterpart}
                for item in other_month
            ),
            False,  # noqa: FBT003 - expected JSON value.
            "month-exclusion-filter",
        )
        filtered = Expectations.records(
            self.session.invoke(
                "getTransactionsByAccount",
                path={"account_id": self.ids["source"]},
                query={"since_date": "2026-01-16"},
            )["transactions"]
        )
        self.assertions.check(
            [item for item in filtered if not Expectations.opening_balance(item)],
            [],
            "since-date-filter",
        )
        self.assertions.check(
            all(str(item.get("date")) >= "2026-01-16" for item in filtered),
            True,  # noqa: FBT003 - expected JSON value.
            "since-date-boundary",
        )
        category = self.assertions.record(
            "getMonthCategoryById",
            "category",
            {"category_id": self.ids["category"], "month": Fixtures.MONTH},
        )
        self.assertions.check(
            (category.get("budgeted"), category.get("activity")),
            (1000, -13000),
            "category-budget-activity",
        )
        scheduled = self.assertions.record(
            "getScheduledTransactionById",
            "scheduled_transaction",
            {"scheduled_transaction_id": self.ids["scheduled"]},
        )
        self.assertions.check(
            (
                scheduled.get("amount"),
                scheduled.get("frequency"),
                scheduled.get("account_id"),
            ),
            (-3000, "monthly", self.ids["source"]),
            "scheduled-values",
        )
        self.assertions.check(
            scheduled.get("date_first"),
            scheduled.get("date_next"),
            "scheduled-unchanged",
        )
        self.assertions.check(
            date.fromisoformat(str(scheduled.get("date_next")))
            > datetime.now(UTC).date() + timedelta(days=90),
            True,  # noqa: FBT003 - expected JSON value.
            "scheduled-not-near-execution",
        )
        default = self.session.client.accounts(explicit=False)
        explicit = self.session.client.accounts(explicit=True)
        self.assertions.check(default, explicit, "default-and-explicit-plan")
        data = self.session.invoke(
            "getTransactionsByAccount", path={"account_id": self.ids["source"]}
        )
        delta = self.session.invoke(
            "getTransactionsByAccount",
            path={"account_id": self.ids["source"]},
            query={"last_knowledge_of_server": data["server_knowledge"]},
        )
        self.assertions.check(delta.get("transactions"), [], "unchanged-delta")

    def remaining_reads(self) -> None:
        """Validate all other selected-plan read responses with available fixtures."""
        paths: dict[str, object] = {
            "plan_id": self.session.client.connection.plan_id,
            "account_id": self.ids["source"],
            "category_id": self.ids["category"],
            "category_group_id": self.ids["group"],
            "payee_id": self.ids["payee"],
            "transaction_id": self.ids["main_transaction"],
            "scheduled_transaction_id": self.ids["scheduled"],
            "month": Fixtures.MONTH,
        }
        contract = self.session.client.contract
        for operation in contract.operations.values():
            if (
                operation.write
                or operation.identifier in self.session.client.completed
                or "{plan_id}" not in operation.path
            ):
                continue
            names = {
                str(item["name"])
                for item in contract.parameters(operation)
                if item["in"] == "path"
            }
            if names <= paths.keys():
                self.session.invoke(
                    operation.identifier, path={key: paths[key] for key in names}
                )
