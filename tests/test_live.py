"""Live-workflow isolation and lifecycle tests against a synthetic API adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar, override
from unittest.mock import Mock
from uuid import UUID

import httpx
import pytest
from tests.support import Server

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.live import LiveOptions, LiveRunner
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import UNSET, JsonCodec, JsonValue


class SyntheticLive(LiveRunner):
    """Replace the external API boundary with a deterministic resource store."""

    FIELDS: ClassVar[dict[str, str]] = {
        "Account": "account",
        "Category": "category",
        "CategoryGroup": "category_group",
        "Payee": "payee",
        "Transaction": "transaction",
        "ScheduledTransaction": "scheduled_transaction",
    }

    def __init__(self, options: LiveOptions) -> None:
        super().__init__(
            options, Transport(Connection("synthetic-test-token", options.plan_id))
        )
        self.resources: dict[str, list[dict[str, JsonValue]]] = {
            field: [] for field in self.FIELDS.values()
        }
        self.submitted: list[tuple[str, JsonValue]] = []
        self.sequence = 0

    @override
    def invoke(
        self,
        operation: str,
        *,
        body: object = UNSET,
        path: dict[str, object] | None = None,
    ) -> dict[str, JsonValue]:
        """Simulate external resource operations without network access."""
        self.completed.add(operation)
        if operation == "getPlanById":
            return {"plan": {"name": "YNAB API CLI TEST synthetic"}}
        values = dict(self.ids) | (path or {})
        payload = JsonCodec.encode(body) if body is not UNSET else {}
        self.submitted.append((operation, payload))
        if operation == "getCategories":
            groups = [
                dict(item)
                | {"categories": JsonCodec.encode(self.resources["category"])}
                for item in self.resources["category_group"]
            ]
            return {"category_groups": JsonCodec.encode(groups)}
        if operation == "updateTransactions":
            entries = self.contract.object(payload)["transactions"]
            if not isinstance(entries, list):
                raise AppError("Synthetic bulk payload must be an array.")
            for entry in entries:
                record = self.contract.object(entry)
                self.update("transaction", str(record["id"]), record)
            return {"transactions": JsonCodec.encode(self.resources["transaction"])}
        field = next(
            (
                self.FIELDS[key]
                for key in sorted(self.FIELDS, key=len, reverse=True)
                if key in operation
            ),
            None,
        )
        if field is None:
            return {}
        return self.dispatch_resource(field, operation, payload, values)

    def dispatch_resource(
        self, field: str, operation: str, payload: JsonValue, values: dict[str, object]
    ) -> dict[str, JsonValue]:
        """Dispatch a synthetic resource lifecycle operation."""
        if operation.startswith("create"):
            return self.create(field, self.contract.object(payload))
        if operation.startswith("update"):
            record = self.contract.object(self.contract.object(payload)[field])
            return {field: self.update(field, str(values[field + "_id"]), record)}
        if operation.startswith("delete"):
            identifier = str(values[field + "_id"])
            self.resources[field] = [
                item for item in self.resources[field] if item["id"] != identifier
            ]
            return {}
        return self.read(field, values, operation)

    def create(self, field: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        """Create synthetic records and simulate duplicate import-ID responses."""
        bulk = payload.get("transactions")
        data = (
            self.contract.object(bulk[0])
            if isinstance(bulk, list) and bulk
            else self.contract.object(payload[field])
        )
        existing = next(
            (
                item
                for item in self.resources[field]
                if data.get("import_id") is not None
                and item.get("import_id") == data["import_id"]
            ),
            None,
        )
        if existing is not None:
            return {"transactions": [], "duplicate_import_ids": [data["import_id"]]}
        self.sequence += 1
        record = dict(data) | {"id": str(UUID(int=self.sequence))}
        if field == "account":
            record["transfer_payee_id"] = str(UUID(int=self.sequence + 100))
        if field == "transaction" and "category_id" not in data and "payee_id" in data:
            record["transfer_account_id"] = self.ids["target_account_id"]
        self.resources[field].append(record)
        return {"transactions": [record]} if isinstance(bulk, list) else {field: record}

    def update(
        self, field: str, identifier: str, data: dict[str, JsonValue]
    ) -> dict[str, JsonValue]:
        """Apply an update to the synthetic ID selected by the workflow."""
        record = next(
            item for item in self.resources[field] if item["id"] == identifier
        )
        record.update(data)
        return record

    def read(
        self, field: str, values: dict[str, object], operation: str
    ) -> dict[str, JsonValue]:
        """Return the requested synthetic collection or record."""
        if operation.endswith("ById"):
            return {
                field: next(
                    item
                    for item in self.resources[field]
                    if item["id"] == values[field + "_id"]
                )
            }
        if operation == "getMonthCategoryById":
            return {field: self.resources[field][0]}
        return {field + "s": JsonCodec.encode(self.resources[field])}


class TestLive:
    """Opt-in workflow guards must remain separate from ordinary defaults."""

    def options(self, tmp_path: Path, *, writes: bool = True) -> LiveOptions:
        """Choose a synthetic explicit UUID and isolated paths."""
        return LiveOptions(
            str(UUID(int=500)), tmp_path / "auth.json", tmp_path / "state", writes
        )

    def test_full_lifecycle(self, tmp_path: Path) -> None:
        """All supported live mutation workflows verify and clean their records."""
        runner = SyntheticLive(self.options(tmp_path))
        report = runner.run()
        assert len(runner.resources["account"]) == 2
        assert len(runner.resources["category"]) == 1
        assert runner.resources["transaction"] == []
        assert runner.resources["scheduled_transaction"] == []
        assert report["complete_live_coverage"] is False
        assert "updateTransactions" in runner.completed
        assert "createScheduledTransaction" in runner.completed
        assert bool(report["gaps"])
        assert runner.state_file.exists()
        runner.provision()
        assert len(runner.resources["account"]) == 2

    def test_read_only_and_mismatched_plan(self, tmp_path: Path) -> None:
        """Read-only runs cannot provision fixtures or use a transport default."""
        options = self.options(tmp_path, writes=False)
        runner = SyntheticLive(options)
        report = runner.run()
        assert bool(report["missing_operations"])
        assert runner.resources["account"] == []
        with pytest.raises(AppError, match="agree explicitly"):
            LiveRunner(
                options,
                Transport(Connection("synthetic-test-token", str(UUID(int=999)))),
            )

    def test_journal_before_failed_write(
        self, tmp_path: Path, contract: Contract
    ) -> None:
        """An uncertain mutation remains journaled and blocks subsequent execution."""
        options = self.options(tmp_path)
        server = Server(contract, "createPayee")
        server.error = httpx.ReadTimeout("synthetic")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            runner = LiveRunner(
                options,
                Transport(
                    Connection("synthetic-test-token", options.plan_id),
                    contract,
                    client,
                ),
            )
            with pytest.raises(AppError, match="network failure"):
                runner.invoke("createPayee", body={"payee": {"name": "synthetic"}})
            assert runner.store.read(runner.state_file)["pending"] is not None
            with pytest.raises(AppError, match="Unresolved"):
                runner.invoke("createPayee", body={"payee": {"name": "synthetic"}})
            with pytest.raises(AppError, match="Unresolved"):
                runner.run()
        assert len(server.requests) == 1

    def test_successful_journal_and_write_guard(
        self, tmp_path: Path, contract: Contract
    ) -> None:
        """Successful writes clear intents while opt-out blocks mutations."""
        options = self.options(tmp_path)
        server = Server(contract, "createPayee")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            runner = LiveRunner(
                options,
                Transport(
                    Connection("synthetic-test-token", options.plan_id),
                    contract,
                    client,
                ),
            )
            runner.invoke("createPayee", body={"payee": {"name": "synthetic"}})
            assert runner.store.read(runner.state_file).get("pending") is None
            fresh = LiveRunner(self.options(tmp_path, writes=False), runner.transport)
            with pytest.raises(AppError, match="enable-writes"):
                fresh.invoke("createPayee", body={"payee": {"name": "synthetic"}})

    def test_wrong_plan_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The isolated-plan name must be checked before any writes."""
        runner = SyntheticLive(self.options(tmp_path))
        monkeypatch.setattr(
            runner, "invoke", Mock(return_value={"plan": {"name": "ordinary budget"}})
        )
        with pytest.raises(AppError, match="name must begin"):
            runner.run()

    def test_duplicate_and_invalid_fixtures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ambiguous fixture collections fail without arbitrary selection."""
        runner = SyntheticLive(self.options(tmp_path))
        monkeypatch.setattr(
            runner,
            "invoke",
            Mock(return_value={"accounts": [{"name": "fixture"}, {"name": "fixture"}]}),
        )
        with pytest.raises(AppError, match="Duplicate"):
            runner.fixture("accounts", "account", "createAccount", {}, "fixture")
        monkeypatch.setattr(runner, "invoke", Mock(return_value={"accounts": False}))
        with pytest.raises(AppError, match="fixture list"):
            runner.fixture("accounts", "account", "createAccount", {}, "fixture")

    def test_verify_and_deleted_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Readback mismatches and undeleted records stop the live workflow."""
        runner = SyntheticLive(self.options(tmp_path))
        runner.state["last_mutation"] = {"operation": "updatePayee"}
        monkeypatch.setattr(
            runner, "invoke", Mock(return_value={"payee": {"name": "wrong"}})
        )
        with pytest.raises(AppError, match="readback mismatch"):
            runner.verify("getPayeeById", "payee", {"name": "expected"})
        assert runner.store.read(runner.state_file)["pending"] is not None
        with pytest.raises(AppError, match="remains active"):
            runner.assert_deleted(
                {"transactions": [{"id": "fixture", "deleted": False}]},
                "transactions",
                "fixture",
            )
        with pytest.raises(AppError, match="verification list"):
            runner.assert_deleted({"transactions": False}, "transactions", "fixture")
        runner.assert_deleted(
            {"transactions": [{"id": "fixture", "deleted": True}]},
            "transactions",
            "fixture",
        )

    def test_cli_live_auth(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The live entry point requires explicitly supplied protected credentials."""
        options = self.options(tmp_path)
        options.auth_file.write_text(
            json.dumps({"access_token": "synthetic-test-token"}), encoding="utf-8"
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "live",
                "--plan-id",
                options.plan_id,
                "--auth-file",
                str(options.auth_file),
                "--state-directory",
                str(options.state_directory),
            ],
        )
        monkeypatch.setattr("ynab_api_cli.live.FileSecurity.validate", Mock())
        monkeypatch.setattr(
            LiveRunner, "run", Mock(return_value={"complete_live_coverage": False})
        )
        LiveRunner.main()
        assert "synthetic-test-token" not in capsys.readouterr().out
        options.auth_file.write_text("{}", encoding="utf-8")
        with pytest.raises(SystemExit) as captured:
            LiveRunner.main()
        assert captured.value.code == 1
