"""Stateful HTTP simulator and subprocess boundary for CLI acceptance tests."""

from __future__ import annotations

import contextlib
import copy
import io
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch
from uuid import UUID

import httpx
from tests.support import Server

from ynab_api_cli.__main__ import Application
from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import JsonCodec, JsonValue


class Api:
    """Model server-side balances, deltas, splits, transfers, and tombstones."""

    PLAN = str(UUID(int=123))
    FIELDS: ClassVar[dict[str, str]] = {
        "Account": "account",
        "CategoryGroup": "category_group",
        "Category": "category",
        "Payee": "payee",
        "ScheduledTransaction": "scheduled_transaction",
        "Transaction": "transaction",
    }

    def __init__(self) -> None:
        self.contract = Contract()
        self.records: dict[str, list[dict[str, JsonValue]]] = {
            value: [] for value in self.FIELDS.values()
        }
        self.requests: list[httpx.Request] = []
        self.version = 0
        self.sequence = 1000
        self.plan_name = "YNAB API CLI TEST synthetic"
        self.fail_write = False
        self.throttle = False
        self._samples: dict[str, dict[str, JsonValue]] = {}

    def sample(self, operation: str, request: httpx.Request) -> dict[str, JsonValue]:
        """Use contract samples for irrelevant fields, retaining independent state."""
        if operation not in self._samples:
            self._samples[operation] = Contract.object(
                Contract.object(
                    JsonCodec.loads(
                        Server(self.contract, operation).handle(request).text
                    )
                )["data"]
            )
        return copy.deepcopy(self._samples[operation])

    def handle(self, request: httpx.Request) -> httpx.Response:
        """Serve the reviewed wire contract with stateful semantic behavior."""
        self.requests.append(request)
        if self.throttle and request.headers["Authorization"] == "Bearer first-fake":
            return httpx.Response(429)
        operation = next(
            item
            for item in self.contract.operations.values()
            if item.method == request.method
            and re.fullmatch(
                re.sub(r"\{[^}]+\}", "[^/]+", item.path),
                request.url.path.removeprefix("/v1"),
            )
        )
        if self.fail_write and operation.write:
            raise httpx.ReadTimeout("Bearer first-fake")
        data = self.sample(operation.identifier, request)
        if operation.identifier == "getPlanById":
            plan = Contract.object(data["plan"])
            plan.update({"id": self.PLAN, "name": self.plan_name})
        field = next(
            (
                self.FIELDS[key]
                for key in sorted(self.FIELDS, key=len, reverse=True)
                if key in operation.identifier
            ),
            None,
        )
        if operation.identifier == "getCategories":
            field = "category"
        if field is not None:
            data = self.resource(operation.identifier, field, request, data)
        status = next(
            int(code)
            for code in Contract.object(operation.definition["responses"])
            if code.startswith("2")
        )
        return httpx.Response(status, json={"data": data})

    def resource(  # noqa: C901, PLR0911 - synthetic HTTP CRUD dispatcher.
        self,
        operation: str,
        field: str,
        request: httpx.Request,
        sample: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        """Dispatch resource writes and collection reads at the HTTP boundary."""
        payload = (
            Contract.object(JsonCodec.loads(request.content.decode()))
            if request.content
            else {}
        )
        if operation.startswith("create"):
            bulk = payload.get("transactions")
            entries = (
                [Contract.object(item) for item in bulk]
                if isinstance(bulk, list)
                else [Contract.object(payload[field])]
            )
            created: list[JsonValue] = []
            duplicates: list[JsonValue] = []
            for entry in entries:
                existing = next(
                    (
                        item
                        for item in self.records[field]
                        if entry.get("import_id") is not None
                        and item.get("import_id") == entry["import_id"]
                    ),
                    None,
                )
                if existing is not None:
                    duplicates.append(entry["import_id"])
                else:
                    created.append(self.create(field, entry, request))
            if isinstance(bulk, list):
                return {
                    "transactions": created,
                    "duplicate_import_ids": duplicates,
                    "transaction_ids": [
                        Contract.object(item)["id"] for item in created
                    ],
                    "server_knowledge": self.version,
                }
            return sample | {field: created[0]}
        if operation == "updateTransactions":
            for item in ExpectationsBoundary.records(payload["transactions"]):
                self.find(field, str(item["id"])).update(item)
            return sample | {"transactions": JsonCodec.encode(self.records[field])}
        if operation.startswith("update"):
            identifier = request.url.path.split("/")[-1]
            record = self.find(field, identifier)
            record.update(Contract.object(payload[field]))
            self.version += 1
            record["_version"] = self.version
            return sample | {field: record}
        if operation.startswith("delete"):
            record = self.find(field, request.url.path.split("/")[-1])
            self.version += 1
            record.update({"deleted": True, "_version": self.version})
            linked = record.get("transfer_transaction_id")
            if isinstance(linked, str):
                self.find(field, linked).update(
                    {"deleted": True, "_version": self.version}
                )
            return sample | {field: record}
        self.balances()
        if operation == "getCategories":
            groups = [
                item
                | {
                    "categories": JsonCodec.encode(
                        [
                            category
                            for category in self.records["category"]
                            if category.get("category_group_id") == item["id"]
                        ]
                    )
                }
                for item in self.records["category_group"]
            ]
            return sample | {"category_groups": JsonCodec.encode(groups)}
        if operation.endswith("ById"):
            identifier = request.url.path.split("/")[-1]
            return sample | {field: self.find(field, identifier)}
        records = self.collection(field, operation, request)
        return sample | {
            field + "s": JsonCodec.encode(records),
            "server_knowledge": self.version,
        }

    def create(
        self, field: str, entry: dict[str, JsonValue], request: httpx.Request
    ) -> dict[str, JsonValue]:
        """Create complete resource records and linked transfer counterparts."""
        operation = (
            "get"
            + next(key for key, value in self.FIELDS.items() if value == field)
            + "ById"
        )
        if field == "category_group":
            record: dict[str, JsonValue] = {
                "hidden": False,
                "internal": False,
                "deleted": False,
            }
        else:
            record = dict(Contract.object(self.sample(operation, request)[field]))
        self.sequence += 1
        self.version += 1
        record.update(
            entry
            | {
                "id": str(UUID(int=self.sequence)),
                "deleted": False,
                "_version": self.version,
            }
        )
        if field == "account":
            record["transfer_payee_id"] = str(UUID(int=self.sequence + 10000))
        if field == "transaction":
            record["type"] = "transaction"
            record["subtransactions"] = entry.get("subtransactions", [])
            record["memo"] = entry.get("memo")
            record["category_id"] = entry.get("category_id")
            record["transfer_transaction_id"] = None
            target = next(
                (
                    item
                    for item in self.records["account"]
                    if entry.get("payee_id") == item.get("transfer_payee_id")
                ),
                None,
            )
            if target is not None:
                record["transfer_account_id"] = target["id"]
                self.sequence += 1
                counterpart = record | {
                    "id": str(UUID(int=self.sequence)),
                    "account_id": target["id"],
                    "transfer_account_id": entry["account_id"],
                    "transfer_transaction_id": record["id"],
                    "amount": -int(str(record["amount"])),
                }
                record["transfer_transaction_id"] = counterpart["id"]
                self.records[field].append(counterpart)
            children = record["subtransactions"]
            if isinstance(children, list):
                child_sample = (
                    Contract.object(
                        ExpectationsBoundary.records(
                            Contract.object(
                                self.sample("getTransactionById", request)[
                                    "transaction"
                                ]
                            )["subtransactions"]
                        )[0]
                    )
                    if children
                    else {}
                )
                record["subtransactions"] = [
                    child_sample
                    | Contract.object(child)
                    | {"transaction_id": record["id"]}
                    for child in children
                ]
        if field == "scheduled_transaction":
            record["date_first"] = entry["date"]
            record["date_next"] = entry["date"]
        self.records[field].append(record)
        if field == "account":
            opening = self.create(
                "transaction",
                {
                    "account_id": record["id"],
                    "amount": 0,
                    "date": datetime.now(UTC).date().isoformat(),
                    "cleared": "cleared",
                    "approved": True,
                },
                request,
            )
            opening.update(
                {"payee_name": "Starting Balance", "import_id": None, "memo": None}
            )
        return record

    def find(self, field: str, identifier: str) -> dict[str, JsonValue]:
        """Select a synthetic resource by explicit identity."""
        return next(item for item in self.records[field] if item["id"] == identifier)

    def balances(self) -> None:
        """Calculate server balances from active transactions independently."""
        active = [
            item
            for item in self.records["transaction"]
            if item.get("deleted") is not True
        ]
        for account in self.records["account"]:
            account["balance"] = sum(
                int(str(item["amount"]))
                for item in active
                if item.get("account_id") == account["id"]
            )
        for category in self.records["category"]:
            total = sum(
                int(str(item["amount"]))
                for item in active
                if item.get("category_id") == category["id"]
            )
            for item in active:
                total += sum(
                    int(str(child["amount"]))
                    for child in ExpectationsBoundary.records(
                        item.get("subtransactions", [])
                    )
                    if child.get("category_id") == category["id"]
                )
            category["activity"] = total

    def collection(
        self, field: str, operation: str, request: httpx.Request
    ) -> list[dict[str, JsonValue]]:
        """Apply supported filters and delta versions to stored resources."""
        knowledge = request.url.params.get("last_knowledge_of_server")
        records: list[dict[str, JsonValue]] = [
            item for item in self.records[field] if item.get("deleted") is not True
        ]
        if knowledge is not None:
            records = [
                item
                for item in self.records[field]
                if int(str(item.get("_version", 0))) > int(knowledge)
            ]
        for label in ("Account", "Payee", "Category"):
            if operation.endswith("By" + label):
                key = label.lower() + "_id"
                identifier = request.url.path.split("/")[-2]
                selected: list[dict[str, JsonValue]] = [
                    item for item in records if item.get(key) == identifier
                ]
                if label == "Category":
                    for parent in records:
                        for child in ExpectationsBoundary.records(
                            parent.get("subtransactions", [])
                        ):
                            if child.get("category_id") == identifier:
                                selected.append(  # noqa: PERF401 - combine typed parent and child records.
                                    parent
                                    | child
                                    | {
                                        "type": "subtransaction",
                                        "parent_transaction_id": parent["id"],
                                    }
                                )
                records = selected
        if operation.endswith("ByMonth"):
            month = request.url.path.split("/")[-2][:7]
            records = [
                item for item in records if str(item.get("date", "")).startswith(month)
            ]
        since = request.url.params.get("since_date")
        if since is not None:
            records = [item for item in records if str(item.get("date")) >= since]
        return records


class ExpectationsBoundary:
    """Decode collection values only at the test HTTP boundary."""

    @staticmethod
    def records(value: JsonValue) -> list[dict[str, JsonValue]]:
        """Require lists in the synthetic API store."""
        assert isinstance(value, list)
        return [Contract.object(item) for item in value]


class Processes:
    """Run real CLI orchestration while replacing the OS subprocess boundary."""

    def __init__(self, api: Api) -> None:
        self.api = api
        self.calls: list[list[str]] = []

    def run(
        self, arguments: list[str], **settings: object
    ) -> subprocess.CompletedProcess[str]:
        """Pass stdin, config, and real CLI parsing through a mock HTTP transport."""
        self.calls.append(arguments)
        environment = settings["env"]
        assert isinstance(environment, dict)
        assert not any(key.startswith("YNAB_ACCESS_TOKEN") for key in environment)
        store = ConfigStore(Path(str(environment["XDG_CONFIG_HOME"])) / "ynab-api-cli")
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            httpx.Client(transport=httpx.MockTransport(self.api.handle)) as client,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
            patch("sys.stdin", io.StringIO(str(settings["input"]))),
        ):
            code = Application(
                store, Transport(store.load(), self.api.contract, client)
            ).run(arguments[3:])
        return subprocess.CompletedProcess(
            arguments, code, stdout.getvalue(), stderr.getvalue()
        )
