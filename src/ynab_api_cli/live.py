"""Explicitly enabled live tests confined to a designated disposable plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.generated.bindings import Bindings
from ynab_api_cli.security import FileSecurity
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import UNSET, JsonCodec, JsonValue, RequestValues

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LiveOptions:
    """Explicit test-plan and credential selection with a separate write guard."""

    plan_id: str
    auth_file: Path
    state_directory: Path
    enable_writes: bool
    account_reads: bool = True


class LiveRunner:
    """Journal live mutations and reconcile fixtures through exact reads."""

    PREFIX = "ynab-api-cli-test"

    def __init__(self, options: LiveOptions, transport: Transport) -> None:
        UUID(options.plan_id)
        if options.plan_id != transport.connection.plan_id:
            raise AppError("Live plan and transport plan must agree explicitly.")
        self.options = options
        self.transport = transport
        self.contract = transport.contract
        self.store = ConfigStore(options.state_directory)
        self.state_file = options.state_directory / (options.plan_id + ".json")
        self.state = (
            self.store.read(self.state_file) if self.state_file.exists() else {}
        )
        self.completed: set[str] = set()
        self.gaps: list[str] = []
        self.ids: dict[str, str] = {
            "plan_id": options.plan_id,
            "month": datetime.now(UTC).date().replace(day=1).isoformat(),
        }

    @classmethod
    def main(cls) -> None:
        """Run live checks only with an explicit plan and protected auth file."""
        parser = argparse.ArgumentParser(description="Opt-in isolated-plan live tests")
        parser.add_argument("--plan-id", required=True)
        parser.add_argument("--auth-file", type=Path, required=True)
        parser.add_argument("--state-directory", type=Path, required=True)
        parser.add_argument("--enable-writes", action="store_true")
        args = parser.parse_args()
        options = LiveOptions(
            str(args.plan_id),
            Path(args.auth_file),
            Path(args.state_directory),
            bool(args.enable_writes),
        )
        logging.basicConfig(level=logging.WARNING)
        try:
            FileSecurity().validate(options.auth_file)
            token = cls.read_token(options.auth_file)
            runner = cls(options, Transport(Connection(token, options.plan_id)))
            sys.stdout.write(json.dumps(runner.run(), indent=2) + "\n")
        except (AppError, OSError, ValueError):
            logger.error("Live test failed; inspect its journal before retrying.")  # noqa: TRY400 - credentials and record bodies must remain private.
            raise SystemExit(1) from None

    @staticmethod
    def read_token(path: Path) -> str:
        """Validate live credentials without using ordinary CLI defaults."""
        token = ConfigStore.read(path).get("access_token")
        if (
            not isinstance(token, str)
            or not token
            or any(part.isspace() for part in token)
        ):
            raise AppError("Live auth file requires an access_token.")
        return token

    def invoke(
        self,
        operation: str,
        *,
        body: object = UNSET,
        path: dict[str, object] | None = None,
    ) -> dict[str, JsonValue]:
        """Journal before submitting a mutation and retain unresolved intents."""
        definition = self.contract.get(operation)
        values: dict[str, object] = {
            str(parameter["name"]): self.ids[str(parameter["name"])]
            for parameter in self.contract.parameters(definition)
            if parameter["in"] == "path" and str(parameter["name"]) in self.ids
        }
        if path is not None:
            values.update(path)
        if definition.write:
            if not self.options.enable_writes:
                raise AppError("Live writes require --enable-writes.")
            if self.state.get("pending") is not None:
                raise AppError(
                    "Unresolved live mutation; inspect state before retrying."
                )
            self.state["pending"] = {
                "operation": operation,
                "path": JsonCodec.encode(values),
                "body": JsonCodec.encode(body) if body is not UNSET else None,
            }
            self.store.write(self.state_file, self.state, secret=True)
        response = Bindings.operations[definition.alias](
            self.transport, RequestValues(values, body=body)
        )
        data = self.contract.object(self.contract.object(response.raw)["data"])
        self.completed.add(operation)
        if definition.write:
            self.state["last_mutation"] = self.state.pop("pending", None)
            self.store.write(self.state_file, self.state, secret=True)
        return data

    def fixture(
        self,
        plural: str,
        singular: str,
        create: str,
        body: dict[str, JsonValue],
        name: str,
    ) -> str:
        """Reuse an exact named fixture or create and verify it once."""
        records = self.invoke("get" + plural.title())[plural]
        if not isinstance(records, list):
            raise AppError("Expected fixture list.")
        matches = [
            self.contract.object(item)
            for item in records
            if self.contract.object(item).get("name") == name
        ]
        if len(matches) > 1:
            raise AppError("Duplicate named live fixtures; reconcile manually.")
        if matches:
            return str(matches[0]["id"])
        payload = dict(body)
        payload["name"] = name
        created = self.contract.object(
            self.invoke(create, body={singular: payload})[singular]
        )
        identifier = str(created["id"])
        verified = self.invoke(
            "get" + singular.title() + "ById", path={singular + "_id": identifier}
        )
        if str(self.contract.object(verified[singular])["id"]) != identifier:
            raise AppError("Fixture readback did not match the created ID.")
        return identifier

    def run(self) -> dict[str, JsonValue]:
        """Verify plan identity, provision fixtures, and report exact live coverage."""
        if self.state.get("pending") is not None:
            raise AppError("Unresolved live mutation; reconcile its journal first.")
        plan = self.contract.object(self.invoke("getPlanById")["plan"])
        if not str(plan.get("name", "")).startswith("YNAB API CLI TEST"):
            raise AppError("Live test plan name must begin YNAB API CLI TEST.")
        if self.options.enable_writes:
            self.provision()
            self.mutations()
        self.reads()
        missing = sorted(set(self.contract.operations) - self.completed)
        return {
            "plan_id": self.options.plan_id,
            "completed_operations": JsonCodec.encode(sorted(self.completed)),
            "missing_operations": JsonCodec.encode(missing),
            "gaps": JsonCodec.encode(self.gaps),
            "retained_fixture_ids": JsonCodec.encode(self.ids),
            "complete_live_coverage": not missing and not self.gaps,
            "journal": str(self.state_file),
        }

    def provision(self) -> None:
        """Provision reusable accounts, a category group, a category, and a payee."""
        for label in ("source", "target"):
            identifier = self.fixture(
                "accounts",
                "account",
                "createAccount",
                {"type": "checking", "balance": 0},
                self.PREFIX + "-" + label,
            )
            self.ids[label + "_account_id"] = identifier
        self.ids["account_id"] = self.ids["source_account_id"]
        categories = self.invoke("getCategories")["category_groups"]
        if not isinstance(categories, list):
            raise AppError("Expected category groups.")
        group = next(
            (
                self.contract.object(item)
                for item in categories
                if self.contract.object(item).get("name") == self.PREFIX
            ),
            None,
        )
        if group is None:
            group = self.contract.object(
                self.invoke(
                    "createCategoryGroup",
                    body={"category_group": {"name": self.PREFIX}},
                )["category_group"]
            )
        self.ids["category_group_id"] = str(group["id"])
        records = group.get("categories", [])
        if not isinstance(records, list):
            raise AppError("Expected category fixture list.")
        category = next(
            (
                self.contract.object(item)
                for item in records
                if self.contract.object(item).get("name") == self.PREFIX
            ),
            None,
        )
        if category is None:
            category = self.contract.object(
                self.invoke(
                    "createCategory",
                    body={
                        "category": {
                            "name": self.PREFIX,
                            "category_group_id": self.ids["category_group_id"],
                        }
                    },
                )["category"]
            )
        self.ids["category_id"] = str(category["id"])
        self.ids["payee_id"] = self.fixture(
            "payees", "payee", "createPayee", {}, self.PREFIX
        )
        self.state["fixtures"] = JsonCodec.encode(self.ids)
        self.store.write(self.state_file, self.state, secret=True)

    def mutations(self) -> None:
        """Exercise supported mutations and verify affected records by ID."""
        self.update_fixtures()
        today = datetime.now(UTC).date().isoformat()
        import_id = "cli:" + hashlib.sha256(str(uuid4()).encode()).hexdigest()[:28]
        transaction: dict[str, JsonValue] = {
            "account_id": self.ids["account_id"],
            "category_id": self.ids["category_id"],
            "date": today,
            "amount": -1000,
            "payee_id": self.ids["payee_id"],
            "import_id": import_id,
            "memo": self.PREFIX,
        }
        created = self.invoke("createTransaction", body={"transaction": transaction})
        self.ids["transaction_id"] = str(
            self.contract.object(created["transaction"])["id"]
        )
        self.verify("getTransactionById", "transaction", {"amount": -1000})
        repeated = self.invoke(
            "createTransaction", body={"transactions": [transaction]}
        )
        duplicates = repeated.get("duplicate_import_ids", [])
        if not isinstance(duplicates, list) or import_id not in duplicates:
            raise AppError("Duplicate import ID was not reported.")
        self.invoke(
            "updateTransaction",
            body={"transaction": {"memo": self.PREFIX + "-updated"}},
        )
        self.verify(
            "getTransactionById", "transaction", {"memo": self.PREFIX + "-updated"}
        )
        self.invoke(
            "updateTransactions",
            body={
                "transactions": [{"id": self.ids["transaction_id"], "amount": -2000}]
            },
        )
        self.verify("getTransactionById", "transaction", {"amount": -2000})
        self.splits_and_transfer(today)
        self.scheduled(today)
        self.invoke("importTransactions")
        self.gaps.append(
            "Direct Import needs a linked test account; "
            "manual accounts cannot verify bank imports."
        )
        self.invoke("deleteTransaction")
        deleted = self.invoke("getTransactions")
        self.assert_deleted(deleted, "transactions", self.ids["transaction_id"])

    def update_fixtures(self) -> None:
        """Exercise category, category-group, budgeting, and payee updates."""
        self.invoke("updateCategory", body={"category": {"note": self.PREFIX}})
        self.verify("getCategoryById", "category", {"note": self.PREFIX})
        self.invoke(
            "updateCategoryGroup", body={"category_group": {"name": self.PREFIX}}
        )
        self.invoke("updateMonthCategory", body={"category": {"budgeted": 1000}})
        self.verify("getMonthCategoryById", "category", {"budgeted": 1000})
        self.invoke("updatePayee", body={"payee": {"name": self.PREFIX}})
        self.verify("getPayeeById", "payee", {"name": self.PREFIX})

    def splits_and_transfer(self, today: str) -> None:
        """Create, verify, and delete split and transfer records in fixture accounts."""
        split = {
            "account_id": self.ids["account_id"],
            "date": today,
            "amount": -1000,
            "category_id": None,
            "subtransactions": [
                {"amount": -400, "category_id": self.ids["category_id"]},
                {"amount": -600, "category_id": self.ids["category_id"]},
            ],
        }
        created = self.invoke("createTransaction", body={"transactions": [split]})
        records = created.get("transactions")
        if not isinstance(records, list) or not records:
            raise AppError("Split bulk creation did not return a record.")
        identifier = str(self.contract.object(records[0])["id"])
        self.verify(
            "getTransactionById",
            "transaction",
            {"amount": -1000},
            path={"transaction_id": identifier},
        )
        self.invoke("deleteTransaction", path={"transaction_id": identifier})
        target = self.contract.object(
            self.invoke(
                "getAccountById", path={"account_id": self.ids["target_account_id"]}
            )["account"]
        )
        payee = target.get("transfer_payee_id")
        if not isinstance(payee, str):
            self.gaps.append("Target account has no transfer payee.")
            return
        created = self.invoke(
            "createTransaction",
            body={
                "transaction": {
                    "account_id": self.ids["account_id"],
                    "payee_id": payee,
                    "date": today,
                    "amount": -1000,
                }
            },
        )
        identifier = str(self.contract.object(created["transaction"])["id"])
        self.verify(
            "getTransactionById",
            "transaction",
            {"transfer_account_id": self.ids["target_account_id"]},
            path={"transaction_id": identifier},
        )
        self.invoke("deleteTransaction", path={"transaction_id": identifier})

    def scheduled(self, _today: str) -> None:
        """Create, read, update, and remove a scheduled transaction fixture."""
        date = (datetime.now(UTC).date() + timedelta(days=30)).isoformat()
        payload: dict[str, JsonValue] = {
            "account_id": self.ids["account_id"],
            "date": date,
            "amount": -1000,
            "frequency": "monthly",
            "memo": self.PREFIX,
        }
        created = self.invoke(
            "createScheduledTransaction", body={"scheduled_transaction": payload}
        )
        self.ids["scheduled_transaction_id"] = str(
            self.contract.object(created["scheduled_transaction"])["id"]
        )
        self.verify(
            "getScheduledTransactionById", "scheduled_transaction", {"amount": -1000}
        )
        payload["memo"] = self.PREFIX + "-updated"
        self.invoke(
            "updateScheduledTransaction", body={"scheduled_transaction": payload}
        )
        self.verify(
            "getScheduledTransactionById",
            "scheduled_transaction",
            {"memo": self.PREFIX + "-updated"},
        )
        self.invoke("deleteScheduledTransaction")
        self.assert_deleted(
            self.invoke("getScheduledTransactions"),
            "scheduled_transactions",
            self.ids["scheduled_transaction_id"],
        )
        del self.ids["scheduled_transaction_id"]

    def reads(self) -> None:
        """Run every read whose fixture prerequisites are available."""
        for operation in self.contract.operations.values():
            if operation.write or operation.identifier in self.completed:
                continue
            if not self.options.account_reads and operation.identifier in {
                "getPlans",
                "getUser",
            }:
                self.gaps.append(operation.identifier + ": account-wide read excluded")
                continue
            required = {
                str(param["name"])
                for param in self.contract.parameters(operation)
                if param["in"] == "path"
            }
            if required <= set(self.ids):
                self.invoke(operation.identifier)
            else:
                self.gaps.append(operation.identifier + ": fixture IDs unavailable")

    def verify(
        self,
        operation: str,
        field: str,
        expected: dict[str, JsonValue],
        *,
        path: dict[str, object] | None = None,
    ) -> None:
        """Read an affected record and compare exact changed fields."""
        record = self.contract.object(self.invoke(operation, path=path)[field])
        if any(record.get(key) != value for key, value in expected.items()):
            self.state["pending"] = self.state.get("last_mutation")
            self.store.write(self.state_file, self.state, secret=True)
            raise AppError("Live mutation readback mismatch; inspect the journal.")

    def assert_deleted(
        self, data: dict[str, JsonValue], field: str, identifier: str
    ) -> None:
        """Accept absence or a documented deleted marker after deletion."""
        records = data[field]
        if not isinstance(records, list):
            raise AppError("Expected deletion verification list.")
        if any(
            self.contract.object(record).get("id") == identifier
            and self.contract.object(record).get("deleted") is not True
            for record in records
        ):
            raise AppError("Deleted fixture remains active.")


if __name__ == "__main__":
    LiveRunner.main()
