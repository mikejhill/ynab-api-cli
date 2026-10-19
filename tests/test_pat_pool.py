"""Ordered PAT storage, bounded rollover, and immediate non-429 failures."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from tests.support import Server

from ynab_api_cli.__main__ import Application
from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import RequestValues


class TestPatPool:
    """Use only synthetic credentials in isolated config and HTTP boundaries."""

    def test_append_migrate_replace(self, store: ConfigStore) -> None:
        """Legacy credentials migrate without losing order or unrelated settings."""
        store.write(
            store.root / "auth.json",
            {"access_token": "first-fake", "other": 42},
            secret=True,
        )
        store.configure("second-fake", add=True)
        store.configure("third-fake", add=True)
        assert store.load().tokens == ("first-fake", "second-fake", "third-fake")
        assert store.read(store.root / "auth.json")["other"] == 42
        assert "access_token" not in store.read(store.root / "auth.json")
        before = (store.root / "auth.json").read_bytes()
        with pytest.raises(AppError, match="Duplicate"):
            store.configure("first-fake", add=True)
        assert (store.root / "auth.json").read_bytes() == before
        store.configure("replacement-fake", replace=True)
        assert store.load().tokens == ("replacement-fake",)
        assert "replacement-fake" not in repr(store.load())

    @pytest.mark.parametrize(
        "values",
        [
            {"access_tokens": []},
            {"access_tokens": "fake"},
            {"access_tokens": ["fake", None]},
            {"access_token": "fake", "access_tokens": ["other"]},
            {"access_tokens": ["fake", "fake"]},
            {"access_tokens": ["fake", "bad\nvalue"]},
        ],
    )
    def test_invalid_pools(self, values: dict[str, object]) -> None:
        """Invalid pools fail without including credential values."""
        with pytest.raises(AppError):
            ConfigStore.credentials(json.loads(json.dumps(values)))

    @pytest.mark.parametrize("operation", ["getUser", "deleteTransaction"])
    def test_rollover_and_session_cursor(
        self, contract: Contract, operation: str
    ) -> None:
        """Only explicit throttling replays requests with another PAT."""
        server = Server(contract, operation)
        observed: list[str] = []

        def handle(request: httpx.Request) -> httpx.Response:
            """Throttle the first synthetic credential only."""
            observed.append(request.headers["Authorization"])
            if request.headers["Authorization"] == "Bearer first-fake":
                return httpx.Response(429, headers={"Retry-After": "60"})
            return server.handle(request)

        path = (
            {"plan_id": "fixture", "transaction_id": "fixture"}
            if operation == "deleteTransaction"
            else {}
        )
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            transport = Transport(
                Connection(
                    "first-fake", additional_tokens=("second-fake", "third-fake")
                ),
                contract,
                client,
            )
            transport.send(operation, RequestValues(path))
            transport.send(operation, RequestValues(path))
        assert observed == [
            "Bearer first-fake",
            "Bearer second-fake",
            "Bearer second-fake",
        ]
        assert transport.request_count == 3

    @pytest.mark.parametrize("status", [301, 400, 401, 403, 404, 409, 500])
    def test_only_429_rotates(self, contract: Contract, status: int) -> None:
        """No additional token is tried for any other HTTP failure."""
        server = Server(contract)
        server.status = status
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(
                Connection("first-fake", additional_tokens=("second-fake",)),
                contract,
                client,
            )
            with pytest.raises(AppError, match=f"HTTP {status}"):
                transport.send("getUser", RequestValues())
        assert len(server.requests) == 1

    def test_exhaustion_cooldown_and_expiry(
        self, contract: Contract, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bound exhaustion and re-enable expired cooldowns."""
        clock = Mock(return_value=100.0)
        monkeypatch.setattr("ynab_api_cli.transport.time.monotonic", clock)
        server = Server(contract)
        server.status = 429
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(
                Connection("first-fake", additional_tokens=("second-fake",)),
                contract,
                client,
            )
            for _ in range(2):
                with pytest.raises(AppError, match="all configured PATs"):
                    transport.send("getUser", RequestValues())
            assert len(server.requests) == 2
            clock.return_value = 161.0
            server.status = 200
            transport.send("getUser", RequestValues())
        assert len(server.requests) == 3

    def test_network_and_budget_no_replay(self, contract: Contract) -> None:
        """Network ambiguity and exhausted request budgets never trigger rollover."""
        server = Server(contract)
        server.error = httpx.ReadTimeout("second-fake")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(
                Connection("first-fake", additional_tokens=("second-fake",)),
                contract,
                client,
            )
            with pytest.raises(AppError, match="network failure"):
                transport.send("getUser", RequestValues())
            transport.request_limit = 1
            with pytest.raises(AppError, match="budget exhausted"):
                transport.send("getUser", RequestValues())
        assert len(server.requests) == 1

    def test_doctor_checks_every_pat(
        self, store: ConfigStore, contract: Contract, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Doctor cannot hide an invalid spare token behind the first valid one."""
        store.configure("second-fake", add=True)
        server = Server(contract)
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            assert (
                Application(store, Transport(store.load(), contract, client)).run(
                    ["doctor"]
                )
                == 0
            )
        assert len(server.requests) == 2
        assert json.loads(capsys.readouterr().out)["pat_count"] == 2

    def test_new_add_and_invalid_modes(self, tmp_path: Path) -> None:
        """Add can initialize an empty pool but cannot combine replacement."""
        store = ConfigStore(tmp_path)
        store.configure("first-fake", add=True)
        with pytest.raises(AppError, match="either"):
            store.configure("second-fake", add=True, replace=True)
        assert store.load().tokens == ("first-fake",)

    @pytest.mark.parametrize("status", [401, 403, 500])
    def test_non429_after_rollover_stops(self, contract: Contract, status: int) -> None:
        """A bad second PAT is reported without trying the third credential."""
        observed: list[httpx.Request] = []

        def handle(request: httpx.Request) -> httpx.Response:
            """Return throttling followed by a different explicit failure."""
            observed.append(request)
            return httpx.Response(429 if len(observed) == 1 else status)

        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            transport = Transport(
                Connection(
                    "first-fake", additional_tokens=("second-fake", "third-fake")
                ),
                contract,
                client,
            )
            with pytest.raises(AppError, match=f"HTTP {status}"):
                transport.send("getUser", RequestValues())
        assert len(observed) == 2

    def test_write_replay_is_byte_identical(self, contract: Contract) -> None:
        """PAT rollover changes only authorization on a rejected write."""
        server = Server(contract, "createPayee")
        requests: list[httpx.Request] = []

        def handle(request: httpx.Request) -> httpx.Response:
            """Reject the first request explicitly, then accept its replay."""
            requests.append(request)
            return httpx.Response(429) if len(requests) == 1 else server.handle(request)

        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            Transport(
                Connection("first-fake", additional_tokens=("second-fake",)),
                contract,
                client,
            ).send(
                "createPayee",
                RequestValues(
                    {"plan_id": "fixture"}, body={"payee": {"name": "café 日本語"}}
                ),
            )
        assert requests[0].content == requests[1].content
        assert requests[0].url == requests[1].url
        assert requests[0].method == requests[1].method
