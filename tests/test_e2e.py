"""Stateful acceptance, false-green prevention, and interrupted-write safety."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from tests.e2e_support import Api, Processes

from ynab_api_cli.ci_live import Application as CiApplication
from ynab_api_cli.config import ConfigStore
from ynab_api_cli.e2e import Application, E2eOptions, E2eRunner
from ynab_api_cli.e2e_client import CliSession, JournaledSession
from ynab_api_cli.e2e_fixtures import Expectations
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.security import FileSecurity
from ynab_api_cli.transport import Connection
from ynab_api_cli.types import RequestValues


class TestE2e:
    """Run production CLI parsing and execution against a stateful HTTP boundary."""

    def setup(self, monkeypatch: pytest.MonkeyPatch) -> tuple[Api, Processes]:
        """Replace only HTTP/process/platform boundaries, with synthetic secrets."""
        api = Api()
        processes = Processes(api)
        monkeypatch.setattr(FileSecurity, "protect", Mock())
        monkeypatch.setattr(FileSecurity, "validate", Mock())
        monkeypatch.setattr("ynab_api_cli.e2e_client.subprocess.run", processes.run)
        return api, processes

    def runner(self, tmp_path: Path, mode: str, *, limit: int = 180) -> E2eRunner:
        """Select a synthetic explicit plan and persistent private test state."""
        return E2eRunner(
            E2eOptions(
                mode,
                Api.PLAN,
                tmp_path / "state",
                enable_writes=mode != "reads",
                request_limit=limit,
            ),
            Connection("first-fake", Api.PLAN, ("second-fake",)),
        )

    def test_full_seed_read_mutation_lifecycle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Assert behavior across seed, reads, reseed, and restored mutation state."""
        api, processes = self.setup(monkeypatch)
        seed = self.runner(tmp_path, "seed").run()
        assert seed["ok"] is True
        read = self.runner(tmp_path, "reads").run()
        assert isinstance(read["assertions"], list)
        assert len(read["assertions"]) >= 20
        assert self.runner(tmp_path, "seed").run()["ok"] is True
        mutations = self.runner(tmp_path, "mutations").run()
        assert isinstance(mutations["assertions"], list)
        assert "deleted-delta-tombstone" in mutations["assertions"]
        assert "budget-restored" in mutations["assertions"]
        assert mutations["complete_live_coverage"] is False
        assert isinstance(mutations["request_count"], int)
        assert mutations["request_count"] < 180
        assert len(api.records["account"]) == 2
        assert (
            len(
                [
                    item
                    for item in api.records["transaction"]
                    if item.get("deleted") is not True
                ]
            )
            == 7
        )
        assert not any("first-fake" in str(call) for call in processes.calls)
        state = ConfigStore.read(tmp_path / "state" / (Api.PLAN + ".json"))
        assert "active_run" not in state
        assert "pending" not in state

    def test_missing_fixtures_fail_without_writes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty plan cannot pass the seeded read acceptance suite."""
        api, _ = self.setup(monkeypatch)
        with pytest.raises(AppError, match="fixture missing"):
            self.runner(tmp_path, "reads").run()
        assert all(request.method == "GET" for request in api.requests)
        assert not list((tmp_path / "state").glob("*.lock"))

    @pytest.mark.parametrize(
        "field", ["balance", "amount", "memo", "frequency", "budgeted"]
    )
    def test_corrupt_baseline_cannot_pass(
        self, field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Known-value assertions reject plausible but incorrect server data."""
        api, _ = self.setup(monkeypatch)
        self.runner(tmp_path, "seed").run()
        if field == "balance":
            api.records["transaction"][0]["amount"] = -9999
        elif field in {"amount", "memo"}:
            api.records["transaction"][0][field] = (
                -9999 if field == "amount" else "wrong"
            )
        elif field == "frequency":
            api.records["scheduled_transaction"][0][field] = "never"
        else:
            api.records["category"][0][field] = 9999
        with pytest.raises(AppError, match="assertion failed"):
            self.runner(tmp_path, "reads").run()

    def test_uncertain_write_latches_entire_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Timeouts retain durable intents and stop all later runs until reconciled."""
        api, _ = self.setup(monkeypatch)
        self.runner(tmp_path, "seed").run()
        api.fail_write = True
        with pytest.raises(AppError, match="CLI failed"):
            self.runner(tmp_path, "mutations").run()
        state = ConfigStore.read(tmp_path / "state" / (Api.PLAN + ".json"))
        assert state["active_run"] == "mutations"
        assert state["pending"] is not None
        count = len(api.requests)
        with pytest.raises(AppError, match="Unfinished"):
            self.runner(tmp_path, "mutations").run()
        assert len(api.requests) == count

    def test_pat_rollover_counts_real_attempts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The same multi-PAT transport powers subprocess acceptance requests."""
        api, _ = self.setup(monkeypatch)
        self.runner(tmp_path, "seed").run()
        api.throttle = True
        before = len(api.requests)
        report = self.runner(tmp_path, "reads").run()
        assert report["request_count"] == len(api.requests) - before
        assert any(
            request.headers["Authorization"] == "Bearer second-fake"
            for request in api.requests[before:]
        )

    def test_plan_identity_and_lock_guards(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Wrong plan names and concurrent runs cannot submit mutations."""
        api, _ = self.setup(monkeypatch)
        api.plan_name = "ordinary plan"
        runner = self.runner(tmp_path, "seed")
        with pytest.raises(AppError, match="exact explicit plan"):
            runner.run()
        assert len(api.requests) == 1
        lock = tmp_path / "state" / (Api.PLAN + ".lock")
        lock.write_text("synthetic", encoding="utf-8")
        with pytest.raises(AppError, match="locked"):
            runner.run()
        assert lock.read_text(encoding="utf-8") == "synthetic"

    def test_local_guards(self, tmp_path: Path) -> None:
        """Write opt-in, explicit UUIDs, and matching plan identities are required."""
        with pytest.raises(AppError, match="enable-writes"):
            E2eOptions("seed", Api.PLAN, tmp_path)
        with pytest.raises(ValueError, match="UUID"):
            E2eOptions("reads", "default", tmp_path)
        with pytest.raises(AppError, match="Select"):
            E2eOptions("unknown", Api.PLAN, tmp_path)
        with pytest.raises(AppError, match="agree"):
            E2eRunner(E2eOptions("reads", Api.PLAN, tmp_path), Connection("first-fake"))
        with pytest.raises(AppError, match="collection"):
            Expectations.records(None)

    def test_process_failure_redaction_and_budget(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Child output remains private and requests reserve worst-case PAT traffic."""
        self.setup(monkeypatch)
        session = CliSession(
            tmp_path, Connection("first-fake", Api.PLAN), request_limit=1
        )
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run",
            Mock(
                return_value=subprocess.CompletedProcess(
                    [], 1, "first-fake", "first-fake"
                )
            ),
        )
        with pytest.raises(AppError, match="details withheld"):
            session.invoke("getPlanById", RequestValues({"plan_id": Api.PLAN}))
        with pytest.raises(AppError, match="budget exhausted"):
            session.invoke("getPlanById", RequestValues({"plan_id": Api.PLAN}))

    def test_journal_scope_and_write_opt_in(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Journaled commands refuse cross-plan paths and unapproved mutations."""
        self.setup(monkeypatch)
        client = CliSession(tmp_path, Connection("first-fake", Api.PLAN))
        session = JournaledSession(
            client, ConfigStore(tmp_path), tmp_path / "state.json", {}, writes=False
        )
        with pytest.raises(AppError, match="cannot leave"):
            session.invoke("getPlanById", path={"plan_id": "different"})
        with pytest.raises(AppError, match="write disabled"):
            session.invoke("createPayee", body={"payee": {"name": "test"}})

    def test_entrypoint_safe_failures(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The standalone acceptance entry point produces no secret-bearing errors."""
        self.setup(monkeypatch)
        store = ConfigStore(tmp_path)
        store.configure("first-fake")
        monkeypatch.setattr(
            "sys.argv",
            [
                "e2e",
                "reads",
                "--plan-id",
                Api.PLAN,
                "--auth-file",
                str(tmp_path / "auth.json"),
                "--state-directory",
                str(tmp_path / "state"),
            ],
        )
        monkeypatch.setattr(E2eRunner, "run", Mock(return_value={"ok": True}))
        Application.main()
        assert json.loads(capsys.readouterr().out)["ok"] is True
        monkeypatch.setattr(
            E2eRunner, "run", Mock(side_effect=ValueError("first-fake"))
        )
        with pytest.raises(SystemExit) as caught:
            Application.main()
        assert caught.value.code == 1
        assert "first-fake" not in caplog.text

    def test_ci_requires_seed_and_scrubs_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Real CI orchestration performs only selected-plan reads and hides IDs."""
        api, _ = self.setup(monkeypatch)
        self.runner(tmp_path, "seed").run()
        start = len(api.requests)
        environment = {
            "YNAB_ACCESS_TOKENS": '["first-fake", "second-fake"]',
            "YNAB_TEST_PLAN_ID": Api.PLAN,
        }
        report = CiApplication.run(environment)
        assert report["ok"] is True
        assert environment == {}
        assert all(request.method == "GET" for request in api.requests[start:])
        assert all(
            request.url.path.startswith("/v1/plans/" + Api.PLAN)
            for request in api.requests[start:]
        )
        assert Api.PLAN not in json.dumps(report)
        assert "first-fake" not in json.dumps(report)
