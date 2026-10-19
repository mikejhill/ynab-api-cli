"""Known account, transaction, split, and transfer assertions."""

from __future__ import annotations

from ynab_api_cli.e2e_assertions import Assertions
from ynab_api_cli.e2e_fixtures import Expectations, Fixtures
from ynab_api_cli.exceptions import AppError


class TransactionReads:
    """Known account, transaction, split, and transfer assertions."""

    def __init__(self, assertions: Assertions) -> None:
        self.assertions = assertions
        self.fixtures = assertions.fixtures
        self.session = assertions.session
        self.ids = assertions.ids

    def run(self) -> str:
        """Verify exact baseline values, relationships, filters, and CLI selection."""
        source = self.assertions.record(
            "getAccountById", "account", {"account_id": self.ids["source"]}
        )
        target = self.assertions.record(
            "getAccountById", "account", {"account_id": self.ids["target"]}
        )
        self.assertions.check(source.get("balance"), -15000, "source-balance")
        self.assertions.check(target.get("balance"), 2000, "target-balance")
        self.assertions.check(
            (source.get("type"), target.get("type")),
            ("checking", "checking"),
            "account-types",
        )
        source_records = Expectations.records(
            self.session.invoke(
                "getTransactionsByAccount", path={"account_id": self.ids["source"]}
            )["transactions"]
        )
        self.assertions.check(
            {
                str(item["id"])
                for item in source_records
                if not Expectations.opening_balance(item)
            },
            {
                self.ids[role + "_transaction"]
                for role in ("main", "zero", "split", "transfer")
            },
            "source-fixture-identities",
        )
        main = self.assertions.record(
            "getTransactionById",
            "transaction",
            {"transaction_id": self.ids["main_transaction"]},
        )
        for key, expected in {
            "amount": -12000,
            "date": Fixtures.DATE,
            "memo": Fixtures.MEMO,
            "approved": False,
            "cleared": "uncleared",
            "category_id": self.ids["category"],
            "payee_id": self.ids["payee"],
        }.items():
            self.assertions.check(main.get(key), expected, "main-" + key)
        zero = self.fixtures.transactions["zero"]
        self.assertions.check(
            (zero.get("amount"), zero.get("memo"), zero.get("category_id")),
            (0, None, None),
            "zero-null",
        )
        split = self.assertions.record(
            "getTransactionById",
            "transaction",
            {"transaction_id": self.ids["split_transaction"]},
        )
        children = Expectations.records(split.get("subtransactions"))
        self.assertions.check(
            sorted(int(str(item["amount"])) for item in children),
            [-600, -400],
            "split-children",
        )
        self.assertions.check(split.get("amount"), -1000, "split-parent")
        self.assertions.check(
            [item.get("category_id") for item in children],
            [self.ids["category"], self.ids["category"]],
            "split-categories",
        )
        transfer = self.fixtures.transactions["transfer"]
        self.assertions.check(
            transfer.get("transfer_account_id"), self.ids["target"], "transfer-target"
        )
        counterpart = transfer.get("transfer_transaction_id")
        if not isinstance(counterpart, str):
            raise AppError("E2E transfer counterpart missing.")
        linked = self.assertions.record(
            "getTransactionById", "transaction", {"transaction_id": counterpart}
        )
        self.assertions.check(
            (
                linked.get("amount"),
                linked.get("transfer_transaction_id"),
                linked.get("account_id"),
            ),
            (2000, self.ids["transfer_transaction"], self.ids["target"]),
            "transfer-counterpart",
        )
        target_records = Expectations.records(
            self.session.invoke(
                "getTransactionsByAccount", path={"account_id": self.ids["target"]}
            )["transactions"]
        )
        self.assertions.check(
            {
                item.get("id")
                for item in target_records
                if not Expectations.opening_balance(item)
            },
            {counterpart},
            "target-account-filter",
        )
        return counterpart
