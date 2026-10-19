"""Verified transaction, import-ID, bulk, split, and transfer lifecycles."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from ynab_api_cli.contract import Contract
from ynab_api_cli.e2e_assertions import Assertions
from ynab_api_cli.e2e_fixtures import Expectations, Fixtures
from ynab_api_cli.types import JsonValue


class TransactionWrites:
    """Verified transaction, import-ID, bulk, split, and transfer lifecycles."""

    def __init__(self, assertions: Assertions) -> None:
        self.assertions = assertions
        self.fixtures = assertions.fixtures
        self.session = assertions.session
        self.ids = assertions.ids

    def run(self) -> None:
        """Verify run-unique imports, duplicate handling, updates, and cleanup."""
        baseline = self.session.invoke("getTransactions")
        payload: dict[str, JsonValue] = {
            "account_id": self.ids["source"],
            "category_id": self.ids["category"],
            "payee_id": self.ids["payee"],
            "date": Fixtures.DATE,
            "amount": -321,
            "memo": Fixtures.MEMO,
            "import_id": "e2e:" + uuid4().hex[:28],
        }
        created = Contract.object(
            self.session.invoke("createTransaction", body={"transaction": payload})[
                "transaction"
            ]
        )
        identifier = str(created["id"])
        path: Mapping[str, object] = {"transaction_id": identifier}
        record = self.assertions.record("getTransactionById", "transaction", path)
        self.assertions.check(
            (record.get("amount"), record.get("memo")),
            (-321, Fixtures.MEMO),
            "create-readback",
        )
        duplicate = self.session.invoke(
            "createTransaction", body={"transactions": [payload]}
        )
        self.assertions.check(
            duplicate.get("duplicate_import_ids"),
            [payload["import_id"]],
            "duplicate-import-id",
        )
        self.session.invoke(
            "updateTransaction",
            path=path,
            body={"transaction": {"amount": 0, "memo": None}},
        )
        record = self.assertions.record("getTransactionById", "transaction", path)
        self.assertions.check(
            (record.get("amount"), record.get("memo"), record.get("payee_id")),
            (0, None, self.ids["payee"]),
            "update-null-zero-omission",
        )
        self.session.invoke(
            "updateTransactions",
            body={"transactions": [{"id": identifier, "amount": -654}]},
        )
        self.assertions.check(
            self.assertions.record("getTransactionById", "transaction", path).get(
                "amount"
            ),
            -654,
            "bulk-update-readback",
        )
        self.session.invoke("deleteTransaction", path=path)
        delta = self.session.invoke(
            "getTransactions",
            query={"last_knowledge_of_server": baseline["server_knowledge"]},
        )
        tombstones = [
            item
            for item in Expectations.records(delta["transactions"])
            if item.get("id") == identifier
        ]
        self.assertions.check(len(tombstones), 1, "deleted-delta-present")
        self.assertions.check(
            tombstones[0].get("deleted"),
            True,  # noqa: FBT003 - expected JSON value.
            "deleted-delta-tombstone",
        )

    def bulk(self) -> None:
        """Read back bulk split and transfer records, then verify both are removed."""
        target = self.assertions.record(
            "getAccountById", "account", {"account_id": self.ids["target"]}
        )
        base: dict[str, JsonValue] = {
            "account_id": self.ids["source"],
            "date": Fixtures.DATE,
            "memo": "e2e:" + uuid4().hex,
        }
        split = base | {
            "amount": -1000,
            "category_id": None,
            "subtransactions": [
                {"amount": -400, "category_id": self.ids["category"]},
                {"amount": -600, "category_id": self.ids["category"]},
            ],
        }
        transfer = base | {"amount": -2000, "payee_id": target.get("transfer_payee_id")}
        created = Expectations.records(
            self.session.invoke(
                "createTransaction", body={"transactions": [split, transfer]}
            )["transactions"]
        )
        self.assertions.check(len(created), 2, "bulk-create-count")
        deleted_ids: list[str] = []
        for item in created:
            identifier = str(item["id"])
            path: Mapping[str, object] = {"transaction_id": identifier}
            record = self.assertions.record("getTransactionById", "transaction", path)
            if record.get("amount") == Fixtures.SPLIT_AMOUNT:
                children = Expectations.records(record.get("subtransactions"))
                self.assertions.check(
                    sorted(int(str(child["amount"])) for child in children),
                    [-600, -400],
                    "bulk-split-readback",
                )
            else:
                self.assertions.check(
                    record.get("transfer_account_id"),
                    self.ids["target"],
                    "bulk-transfer-readback",
                )
                linked = self.assertions.record(
                    "getTransactionById",
                    "transaction",
                    {"transaction_id": record.get("transfer_transaction_id")},
                )
                self.assertions.check(
                    (linked.get("amount"), linked.get("transfer_transaction_id")),
                    (2000, identifier),
                    "bulk-transfer-linked",
                )
                deleted_ids.append(str(linked["id"]))
            self.session.invoke("deleteTransaction", path=path)
            deleted_ids.append(identifier)
        remaining = Expectations.records(
            self.session.invoke("getTransactions")["transactions"]
        )
        self.assertions.check(
            any(
                item.get("id") in deleted_ids and item.get("deleted") is not True
                for item in remaining
            ),
            False,  # noqa: FBT003 - expected JSON value.
            "bulk-cleanup-verified",
        )
