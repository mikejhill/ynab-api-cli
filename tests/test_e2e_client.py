"""Adversarial process output, credential isolation, and preview failure paths."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.e2e_client import CliSession, JournaledSession
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.security import FileSecurity
from ynab_api_cli.transport import Connection
from ynab_api_cli.types import RequestValues


class TestCliSession:
    """Require bounded traffic and fail closed on malformed child metadata."""

    PLAN = "00000000-0000-4000-8000-000000000123"

    def session(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliSession:
        """Isolate synthetic credentials from actual platform ACL implementation."""
        monkeypatch.setattr(FileSecurity, "protect", Mock())
        return CliSession(
            tmp_path, Connection("first-fake", self.PLAN, ("second-fake",))
        )

    @pytest.mark.parametrize(
        "output",
        [
            "not-json",
            "[]",
            '{"request_count":0}',
            '{"request_count":true}',
            '{"request_count":3}',
            '{"request_count":1}',
            '{"request_count":1,"pat_index":true}',
            '{"request_count":1,"pat_index":2}',
        ],
    )
    def test_invalid_child_output(
        self, output: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bad JSON and untrustworthy accounting cannot produce passing results."""
        session = self.session(tmp_path, monkeypatch)
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run",
            Mock(return_value=subprocess.CompletedProcess([], 0, output, "")),
        )
        with pytest.raises(AppError):
            session.command(["discover"])

    @pytest.mark.parametrize(
        "error", [OSError("first-fake"), subprocess.TimeoutExpired(["first-fake"], 30)]
    )
    def test_process_exceptions(
        self, error: Exception, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Subprocess exceptions redact private output and reserve worst-case usage."""
        session = self.session(tmp_path, monkeypatch)
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run", Mock(side_effect=error)
        )
        with pytest.raises(AppError, match="process failed") as caught:
            session.command(["discover"])
        assert "first-fake" not in str(caught.value)
        assert session.count == 2

    @pytest.mark.parametrize(
        "output", [{"preview": False}, {"preview": True, "request": {}}]
    )
    def test_preview_mismatch(
        self, output: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Previews must preserve the exact request before a write is authorized."""
        session = self.session(tmp_path, monkeypatch)
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run",
            Mock(
                return_value=subprocess.CompletedProcess([], 0, json.dumps(output), "")
            ),
        )
        with pytest.raises(AppError, match="preview did not preserve"):
            session.invoke(
                "createPayee",
                RequestValues(
                    {"plan_id": self.PLAN}, body={"payee": {"name": "fixture"}}
                ),
                preview=True,
            )
        assert session.count == 0

    def test_missing_status_and_minimum_budget(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No response is accepted without its HTTP status or sufficient budget."""
        session = self.session(tmp_path, monkeypatch)
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run",
            Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, '{"request_count":1,"pat_index":0}', ""
                )
            ),
        )
        with pytest.raises(AppError, match="HTTP status"):
            session.invoke("getPlanById", RequestValues({"plan_id": self.PLAN}))
        with pytest.raises(AppError, match="budget must cover"):
            CliSession(tmp_path, session.connection, request_limit=1)

    def test_private_pool_reordering(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remember the working PAT only in the ephemeral session configuration."""
        session = self.session(tmp_path, monkeypatch)
        original = session.connection
        monkeypatch.setattr(
            "ynab_api_cli.e2e_client.subprocess.run",
            Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, '{"request_count":2,"pat_index":1}', ""
                )
            ),
        )
        session.command(["discover"])
        assert session.connection.tokens == ("second-fake", "first-fake")
        assert original.tokens == ("first-fake", "second-fake")
        assert session.count == 2

    def test_invalid_history_keeps_pending(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A malformed journal never erases a successfully submitted write intent."""
        client = self.session(tmp_path, monkeypatch)
        monkeypatch.setattr(client, "invoke", Mock(return_value={}))
        store = ConfigStore(tmp_path)
        session = JournaledSession(
            client, store, tmp_path / "state.json", {"history": False}, writes=True
        )
        with pytest.raises(AppError, match="journal history"):
            session.invoke("createPayee", body={"payee": {"name": "fixture"}})
        assert session.state["pending"] is not None
