"""Versioned synthetic fixtures with independently specified expected values."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ynab_api_cli.contract import Contract
from ynab_api_cli.e2e_client import JournaledSession
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonValue


class Expectations:
    """Fail required acceptance checks without printing financial records."""

    @staticmethod
    def equal(actual: object, expected: object, scenario: str) -> None:
        """Compare exact expected values with a fixed, non-sensitive failure label."""
        if actual != expected:
            raise AppError("E2E assertion failed: " + scenario)

    @staticmethod
    def records(value: JsonValue) -> list[dict[str, JsonValue]]:
        """Require a JSON array of objects at a collection boundary."""
        if not isinstance(value, list):
            raise AppError("E2E expected a record collection.")
        return [Contract.object(item) for item in value]

    @staticmethod
    def opening_balance(record: dict[str, JsonValue]) -> bool:
        """Recognize only the server-created zero opening balance fixture."""
        return (
            record.get("amount") == 0
            and record.get("payee_name") == "Starting Balance"
            and record.get("import_id") is None
            and record.get("memo") is None
        )

    @classmethod
    def named(
        cls, records: list[dict[str, JsonValue]], name: str
    ) -> dict[str, JsonValue] | None:
        """Reject duplicate or deleted fixture identities instead of guessing."""
        matches = [
            item
            for item in records
            if item.get("name") == name and item.get("deleted") is not True
        ]
        if len(matches) > 1:
            raise AppError("Duplicate E2E fixture names; reconcile manually.")
        return matches[0] if matches else None


class Fixtures:
    """Discover persistent fixtures through API names, never a local ID cache."""

    PREFIX = "ynab-api-cli-e2e-v1"
    SPLIT_AMOUNT = -1000
    DATE = "2026-01-15"
    MONTH = "2026-01-01"
    MEMO = "YNAB CLI E2E v1 café 日本語"

    def __init__(self, session: JournaledSession) -> None:
        self.session = session
        self.ids: dict[str, str] = {}
        self.transactions: dict[str, dict[str, JsonValue]] = {}

    def discover(self, *, seed: bool = False) -> None:
        """Create only missing resources in seed mode; fail missing read fixtures."""
        accounts = Expectations.records(self.session.invoke("getAccounts")["accounts"])
        for role in ("source", "target"):
            record = Expectations.named(accounts, self.PREFIX + "-" + role)
            if record is None and seed:
                record = Contract.object(
                    self.session.invoke(
                        "createAccount",
                        body={
                            "account": {
                                "name": self.PREFIX + "-" + role,
                                "type": "checking",
                                "balance": 0,
                            }
                        },
                    )["account"]
                )
            self.ids[role] = self._required_id(record)
        groups = Expectations.records(
            self.session.invoke("getCategories")["category_groups"]
        )
        group = Expectations.named(groups, self.PREFIX)
        if group is None and seed:
            group = Contract.object(
                self.session.invoke(
                    "createCategoryGroup",
                    body={"category_group": {"name": self.PREFIX}},
                )["category_group"]
            )
        self.ids["group"] = self._required_id(group)
        category = Expectations.named(
            Expectations.records((group or {}).get("categories", [])), self.PREFIX
        )
        if category is None and seed:
            category = Contract.object(
                self.session.invoke(
                    "createCategory",
                    body={
                        "category": {
                            "name": self.PREFIX,
                            "category_group_id": self.ids["group"],
                        }
                    },
                )["category"]
            )
        self.ids["category"] = self._required_id(category)
        payees = Expectations.records(self.session.invoke("getPayees")["payees"])
        payee = Expectations.named(payees, self.PREFIX)
        if payee is None and seed:
            payee = Contract.object(
                self.session.invoke(
                    "createPayee", body={"payee": {"name": self.PREFIX}}
                )["payee"]
            )
        self.ids["payee"] = self._required_id(payee)
        self._transactions(seed=seed)
        self._scheduled(seed=seed)
        if seed:
            self.session.invoke(
                "updateMonthCategory",
                path={"month": self.MONTH, "category_id": self.ids["category"]},
                body={"category": {"budgeted": 1000}},
            )

    @staticmethod
    def _required_id(record: dict[str, JsonValue] | None) -> str:
        """Reject absent fixtures and malformed identifiers before later writes."""
        if record is None or not isinstance(record.get("id"), str):
            raise AppError("Required E2E v1 fixture missing; run seed explicitly.")
        return str(record["id"])

    def _transactions(self, *, seed: bool) -> None:
        """Discover immutable baseline records through distinct import identifiers."""
        records = Expectations.records(
            self.session.invoke(
                "getTransactionsByAccount", path={"account_id": self.ids["source"]}
            )["transactions"]
        )
        target = Contract.object(
            self.session.invoke(
                "getAccountById", path={"account_id": self.ids["target"]}
            )["account"]
        )
        transfer_payee = target.get("transfer_payee_id")
        if not isinstance(transfer_payee, str):
            raise AppError("Required transfer capability missing in fixture account.")
        base: dict[str, JsonValue] = {
            "account_id": self.ids["source"],
            "date": self.DATE,
            "cleared": "uncleared",
            "approved": False,
        }
        payloads: dict[str, dict[str, JsonValue]] = {
            "main": {
                "amount": -12000,
                "category_id": self.ids["category"],
                "payee_id": self.ids["payee"],
                "memo": self.MEMO,
            },
            "zero": {"amount": 0, "category_id": None, "memo": None},
            "split": {
                "amount": -1000,
                "category_id": None,
                "memo": self.PREFIX + "-split",
                "subtransactions": [
                    {"amount": -400, "category_id": self.ids["category"]},
                    {"amount": -600, "category_id": self.ids["category"]},
                ],
            },
            "transfer": {
                "amount": -2000,
                "payee_id": transfer_payee,
                "memo": self.PREFIX + "-transfer",
            },
        }
        for role, payload in payloads.items():
            import_id = "e2e-v1-" + role
            matches = [
                item
                for item in records
                if item.get("import_id") == import_id
                and item.get("deleted") is not True
            ]
            if len(matches) > 1:
                raise AppError("Duplicate E2E import fixtures.")
            record = matches[0] if matches else None
            if record is None and seed:
                record = Contract.object(
                    self.session.invoke(
                        "createTransaction",
                        body={"transaction": base | payload | {"import_id": import_id}},
                    )["transaction"]
                )
            self.ids[role + "_transaction"] = self._required_id(record)
            self.transactions[role] = record or {}

    def _scheduled(self, *, seed: bool) -> None:
        """Keep a distant future schedule that cannot materialize during normal CI."""
        records = Expectations.records(
            self.session.invoke("getScheduledTransactions")["scheduled_transactions"]
        )
        matches = [
            item
            for item in records
            if item.get("memo") == self.PREFIX and item.get("deleted") is not True
        ]
        if len(matches) > 1:
            raise AppError("Duplicate E2E scheduled fixtures.")
        record = matches[0] if matches else None
        if record is None and seed:
            scheduled_date = (
                datetime.now(UTC).date() + timedelta(days=1460)
            ).isoformat()
            record = Contract.object(
                self.session.invoke(
                    "createScheduledTransaction",
                    body={
                        "scheduled_transaction": {
                            "account_id": self.ids["source"],
                            "payee_id": self.ids["payee"],
                            "category_id": self.ids["category"],
                            "date": scheduled_date,
                            "amount": -3000,
                            "frequency": "monthly",
                            "memo": self.PREFIX,
                        }
                    },
                )["scheduled_transaction"]
            )
        self.ids["scheduled"] = self._required_id(record)
