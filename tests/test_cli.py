"""CLI configuration, discovery, previews, execution, and failure statuses."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from pydantic import ValidationError
from tests.support import Server

from ynab_api_cli.__main__ import Application
from ynab_api_cli.cli import CommandLine
from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.transport import Transport


class TestApplication:
    """Exercise the public process behavior with isolated settings and HTTP."""

    @pytest.mark.parametrize(
        "argv",
        [
            ["discover"],
            ["discover", "transactions"],
            ["inspect", "createTransaction"],
            ["doctor", "--offline"],
        ],
    )
    def test_local_commands(
        self, store: ConfigStore, capsys: pytest.CaptureFixture[str], argv: list[str]
    ) -> None:
        """Local discovery and offline doctor return valid JSON without networking."""
        assert Application(store).run(argv) == 0
        value = json.loads(capsys.readouterr().out)
        if argv[0] == "doctor":
            assert value["api_checked"] is False
        if argv[0] == "inspect":
            assert value["components"]
            assert len(value["components"]) < 96

    def test_preview_and_execution(
        self, store: ConfigStore, contract: Contract, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Writes make no requests until execute is supplied, then send once."""
        server = Server(contract, "createTransaction")
        payload = {
            "path": {"plan_id": "fixture"},
            "body": {
                "transaction": {
                    "account_id": "00000000-0000-4000-8000-000000000001",
                    "date": "2026-01-01",
                    "amount": -12340,
                }
            },
        }
        argv = ["call", "createTransaction", "--request", json.dumps(payload)]
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            app = Application(store, Transport(store.load(), contract, client))
            assert app.run(argv) == 0
            assert json.loads(capsys.readouterr().out)["preview"] is True
            assert server.requests == []
            assert app.run([*argv, "--execute", "--metadata"]) == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == 201
        assert len(server.requests) == 1

    def test_default_plan_and_file(
        self,
        store: ConfigStore,
        contract: Contract,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Resource flags and JSON files resolve a configured default plan."""
        store.select_plan("00000000-0000-4000-8000-000000000001")
        server = Server(contract, "getTransactions")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            app = Application(store, Transport(store.load(), contract, client))
            assert (
                app.run(
                    [
                        "transactions",
                        "get-transactions",
                        "--since-date",
                        "2026-01-01",
                        "--type",
                        "unapproved",
                    ]
                )
                == 0
            )
            capsys.readouterr()
            body = tmp_path / "body.json"
            body.write_text(
                '{"path": {}, "query": {"since_date":"2026-01-01"}}', encoding="utf-8"
            )
            assert (
                app.run(["call", "getTransactions", "--request", "@" + str(body)]) == 0
            )
        assert all(
            "/plans/00000000-0000-4000-8000-000000000001/" in str(request.url)
            for request in server.requests
        )

    def test_stdin_and_body_commands(
        self,
        store: ConfigStore,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Uniform stdin input and endpoint body files preserve JSON presence."""
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                '{"path":{"plan_id":"fixture","transaction_id":"fixture"},"body":{"transaction":{"memo":null}}}'
            ),
        )
        assert (
            Application(store).run(["call", "updateTransaction", "--request", "-"]) == 0
        )
        assert (
            json.loads(capsys.readouterr().out)["request"]["body"]["transaction"][
                "memo"
            ]
            is None
        )
        assert (
            Application(store).run(
                [
                    "transactions",
                    "update-transaction",
                    "--plan-id",
                    "fixture",
                    "--transaction-id",
                    "fixture",
                    "--body",
                    '{"transaction":{"amount":0}}',
                ]
            )
            == 0
        )

    @pytest.mark.parametrize(
        "argv",
        [
            ["discover", "bogus"],
            ["inspect", "bogus"],
            ["call", "getUser", "--request", "broken"],
            ["call", "getUser", "--request", "[]"],
            ["call", "getUser", "--request", '{"unexpected":1}'],
            ["configure"],
        ],
    )
    def test_handled_errors(
        self, store: ConfigStore, argv: list[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed requests and noninteractive configuration fail safely."""
        monkeypatch.setattr("sys.stdin", io.StringIO())
        assert Application(store).run(argv) == 1

    def test_configure_and_select(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Interactive configuration hides tokens and selects an explicit plan."""
        stdin = Mock()
        stdin.isatty.return_value = True
        monkeypatch.setattr("sys.stdin", stdin)
        monkeypatch.setattr(
            "ynab_api_cli.__main__.getpass.getpass",
            Mock(return_value="synthetic-test-token"),
        )
        store = ConfigStore(tmp_path)
        app = Application(store)
        assert app.run(["configure"]) == 0
        assert "synthetic-test-token" not in capsys.readouterr().out
        assert app.run(["select-plan", "00000000-0000-4000-8000-000000000001"]) == 0
        assert app.run(["configure", "--replace"]) == 0

    def test_doctor_online(
        self,
        store: ConfigStore,
        contract: Contract,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Doctor distinguishes API validation and optional upstream validation."""
        server = Server(contract)
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            app = Application(store, Transport(store.load(), contract, client))
            assert app.run(["doctor"]) == 0
            assert json.loads(capsys.readouterr().out)["api_checked"] is True
            monkeypatch.setattr(
                "ynab_api_cli.compat.Compatibility.fetch",
                Mock(return_value=contract.document),
            )
            assert app.run(["doctor", "--offline", "--upstream"]) == 0
            assert app.run(["compat", "check"]) == 0
            monkeypatch.setattr(
                "ynab_api_cli.compat.Compatibility.compare",
                Mock(return_value={"compatible": False}),
            )
            assert app.run(["compat", "check"]) == 1

    def test_entrypoint_and_interrupt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The entry point exits correctly and interruption returns 130."""
        monkeypatch.setattr(Application, "run", Mock(return_value=2))
        with pytest.raises(SystemExit) as captured:
            Application.main(["unknown"])
        assert captured.value.code == 2
        monkeypatch.undo()
        monkeypatch.setattr(
            Application, "dispatch", Mock(side_effect=KeyboardInterrupt)
        )
        assert Application().run(["discover"]) == 130

    def test_model_and_filesystem_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected boundary failures never print raw exceptions."""
        for error in (
            OSError("synthetic-test-token"),
            ValidationError.from_exception_data("synthetic", []),
        ):
            monkeypatch.setattr(Application, "dispatch", Mock(side_effect=error))
            assert Application().run(["discover"]) == 1

    def test_skill_export(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Skill resources can be read and exported from the package."""
        app = Application()
        assert app.run(["skill", "show"]) == 0
        assert "name: ynab-api-cli" in capsys.readouterr().out
        assert app.run(["skill", "export", str(tmp_path / "ynab-api-cli")]) == 0
        assert (tmp_path / "ynab-api-cli/SKILL.md").exists()
        assert app.run(["skill", "export", str(tmp_path / "ynab-api-cli")]) == 1
        assert app.run(["skill", "export"]) == 1


class TestCommandLine:
    """Verify endpoint flags are decoded into appropriate primitive types."""

    def test_primitive_flags(self, contract: Contract) -> None:
        """False remains false and server knowledge becomes an integer."""
        parser = CommandLine(contract)
        assert parser.parse(
            ["plans", "get-plans", "--include-accounts", "false"]
        ).arguments.query == {"include_accounts": False}
        assert parser.parse(
            ["accounts", "get-accounts", "--last-knowledge-of-server", "7"]
        ).arguments.query == {"last_knowledge_of_server": 7}

    @pytest.mark.parametrize(
        "argv",
        [
            ["unknown"],
            ["plans", "get-plans", "--include-accounts", "yes"],
            ["accounts", "get-accounts", "--last-knowledge-of-server", "bad"],
            ["transactions", "get-transaction-by-id"],
        ],
    )
    def test_usage_errors(self, contract: Contract, argv: list[str]) -> None:
        """Invalid commands and missing flags use the standard usage status."""
        with pytest.raises(SystemExit) as captured:
            CommandLine(contract).parse(argv)
        assert captured.value.code == 2
