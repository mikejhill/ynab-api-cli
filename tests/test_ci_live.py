"""Network-boundary tests for CI confinement, redaction, and credential cleanup."""

from __future__ import annotations

import json
import os
import re
import tempfile
from enum import StrEnum
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from tests.support import Server

from ynab_api_cli.ci_live import Application
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError


class Failure(StrEnum):
    """Adversarial API outcomes that must not disclose request secrets."""

    NONE = "none"
    STATUS = "status"
    MALFORMED = "malformed"
    NETWORK = "network"
    UNEXPECTED = "unexpected"
    PLAN_NAME = "plan-name"


class LiveServer:
    """Serve reviewed response schemas at an observable HTTP boundary."""

    def __init__(self, contract: Contract, *, failure: Failure = Failure.NONE) -> None:
        self._contract = contract
        self._failure = failure
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        """Return representative responses or deliberately secret-bearing failures."""
        self.requests.append(request)
        secret = request.headers["Authorization"]
        if self._failure == Failure.STATUS:
            return httpx.Response(502, json={"detail": secret})
        if self._failure == Failure.MALFORMED:
            return httpx.Response(200, text=secret)
        if self._failure == Failure.NETWORK:
            raise httpx.ReadTimeout(secret)
        if self._failure == Failure.UNEXPECTED:
            raise ValueError(secret)
        path = request.url.path.removeprefix("/v1")
        operation = next(
            item
            for item in self._contract.operations.values()
            if item.method == request.method
            and re.fullmatch(re.sub(r"\{[^}]+\}", "[^/]+", item.path), path)
        )
        response = Server(self._contract, operation.identifier).handle(request)
        if operation.identifier != "getPlanById":
            return response
        data = response.json()
        data["data"]["plan"]["name"] = (
            "ordinary plan"
            if self._failure == Failure.PLAN_NAME
            else "YNAB API CLI TEST synthetic"
        )
        return httpx.Response(response.status_code, json=data)


class TestApplication:
    """Exercise real orchestration while replacing only the HTTP boundary."""

    CREDENTIAL = "synthetic-ci-secret-do-not-log"
    PLAN = str(UUID(int=123))

    def environment(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Supply fake step secrets and confine temporary files to the test."""
        monkeypatch.setenv("YNAB_ACCESS_TOKEN", self.CREDENTIAL)
        monkeypatch.setenv("YNAB_TEST_PLAN_ID", self.PLAN)
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

    def test_read_only_scope_and_summary(
        self,
        contract: Contract,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CI submits only selected-plan GETs and exports no private record data."""
        self.environment(monkeypatch, tmp_path)
        server = LiveServer(contract)
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            Application.main(client)

        output = capsys.readouterr().out
        report = json.loads(output)
        assert report["ok"] is True
        assert report["mode"] == "read-only"
        assert report["complete_live_coverage"] is False
        assert "getPlanById" in report["completed_operations"]
        assert "getPlans" not in report["completed_operations"]
        assert "getUser" not in report["completed_operations"]
        assert all(request.method == "GET" for request in server.requests)
        assert all(
            request.url.path.startswith("/v1/plans/" + self.PLAN)
            for request in server.requests
        )
        assert self.CREDENTIAL not in output
        assert self.PLAN not in output
        assert "YNAB_ACCESS_TOKEN" not in os.environ
        assert "YNAB_TEST_PLAN_ID" not in os.environ
        assert not list(tmp_path.rglob("auth.json"))
        assert not list(tmp_path.iterdir())

    @pytest.mark.parametrize(
        "failure", [item for item in Failure if item != Failure.NONE]
    )
    def test_failure_redaction_and_cleanup(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
        failure: Failure,
    ) -> None:
        """API payloads, nested exception details, and credentials stay out of logs."""
        self.environment(monkeypatch, tmp_path)
        server = LiveServer(Contract(), failure=failure)
        with (
            httpx.Client(transport=httpx.MockTransport(server.handle)) as client,
            pytest.raises(SystemExit) as caught,
        ):
            Application.main(client)

        captured = capsys.readouterr()
        assert caught.value.code == 1
        assert self.CREDENTIAL not in captured.out + captured.err + caplog.text
        assert self.PLAN not in captured.out + captured.err + caplog.text
        assert captured.out == ""
        assert "Live CI probe failed" in caplog.text
        assert not list(tmp_path.iterdir())

    @pytest.mark.parametrize(
        ("token", "plan"),
        [
            ("", PLAN),
            ("contains whitespace", PLAN),
            (CREDENTIAL, ""),
            (CREDENTIAL, "default"),
        ],
    )
    def test_invalid_settings_prevent_network(
        self, contract: Contract, token: str, plan: str
    ) -> None:
        """Missing secrets, invalid headers, and implicit plan aliases fail locally."""
        environment = {"YNAB_ACCESS_TOKEN": token, "YNAB_TEST_PLAN_ID": plan}
        server = LiveServer(contract)
        with (
            httpx.Client(transport=httpx.MockTransport(server.handle)) as client,
            pytest.raises((ValueError, AppError)),
        ):
            Application.run(environment, client)
        assert environment == {}
        assert server.requests == []
