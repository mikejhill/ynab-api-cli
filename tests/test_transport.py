"""REST execution, schema rejection, redaction, and serialization behavior."""

from __future__ import annotations

import json
from typing import ClassVar
from unittest.mock import Mock

import httpx
import pytest
from tests.support import Server

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.generated.api.transactions.create_transaction import Endpoint
from ynab_api_cli.generated.models.post_transactions_wrapper import (
    PostTransactionsWrapper,
)
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import JsonCodec, RequestValues


class TestTransport:
    """Require one bounded request and lossless contract representations."""

    PAYLOAD: ClassVar[dict[str, object]] = {
        "transaction": {
            "account_id": "00000000-0000-4000-8000-000000000001",
            "date": "2026-01-01",
            "amount": 0,
            "category_id": None,
            "memo": "fixture",
            "extra_allowed": {"preserve": True},
        }
    }

    def test_typed_models_preserve_fields(self, contract: Contract) -> None:
        """Omission, null, zero, and additional properties survive model encoding."""
        server = Server(contract, "createTransaction")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(Connection("synthetic-test-token"), contract, client)
            result = Endpoint.execute(
                transport=transport,
                plan_id="fixture",
                body=PostTransactionsWrapper.model_validate(self.PAYLOAD),
            )
        assert json.loads(server.requests[0].content) == self.PAYLOAD
        assert result.raw is not None
        assert server.requests[0].extensions["timeout"] == {
            "connect": 30,
            "read": 30,
            "write": 30,
            "pool": 30,
        }

    @pytest.mark.parametrize("status", [301, 302, 400, 401, 403, 404, 409, 429, 500])
    def test_errors_never_retry(self, contract: Contract, status: int) -> None:
        """Redirects and API failures produce one sanitized error."""
        server = Server(contract)
        server.status = status
        with (
            httpx.Client(
                transport=httpx.MockTransport(server.handle), follow_redirects=True
            ) as client,
            pytest.raises(AppError, match=f"HTTP {status}") as captured,
        ):
            Transport(Connection("synthetic-test-token"), contract, client).send(
                "getUser", RequestValues()
            )
        assert len(server.requests) == 1
        assert "synthetic-test-token" not in str(captured.value)

    @pytest.mark.parametrize("operation", ["getUser", "deleteTransaction"])
    def test_network_uncertainty(self, contract: Contract, operation: str) -> None:
        """Write transport failures identify an uncertain outcome without retrying."""
        server = Server(contract)
        server.error = httpx.ReadTimeout("synthetic-test-token")
        path = (
            {"plan_id": "fixture", "transaction_id": "fixture"}
            if operation == "deleteTransaction"
            else {}
        )
        with (
            httpx.Client(transport=httpx.MockTransport(server.handle)) as client,
            pytest.raises(AppError) as captured,
        ):
            Transport(Connection("synthetic-test-token"), contract, client).send(
                operation, RequestValues(path)
            )
        assert len(server.requests) == 1
        assert "synthetic-test-token" not in str(captured.value)
        assert ("unknown" in str(captured.value)) == (operation == "deleteTransaction")

    @pytest.mark.parametrize(
        "raw", [None, {}, {"data": {}}, {"data": {"user": {"id": "invalid"}}}]
    )
    def test_response_drift(self, contract: Contract, raw: object) -> None:
        """Invalid success responses fail the independent schema validator."""
        server = Server(contract)
        server.raw = JsonCodec.encode(raw)
        with (
            httpx.Client(transport=httpx.MockTransport(server.handle)) as client,
            pytest.raises(AppError, match="Invalid response"),
        ):
            Transport(Connection("synthetic-test-token"), contract, client).send(
                "getUser", RequestValues()
            )

    def test_malformed_and_undocumented_success(self, contract: Contract) -> None:
        """Malformed JSON and undeclared success statuses fail explicitly."""
        server = Server(contract)
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(Connection("synthetic-test-token"), contract, client)
            server.text = "not json"
            with pytest.raises(AppError, match="malformed JSON"):
                transport.send("getUser", RequestValues())
            server.text = None
            server.status = 202
            with pytest.raises(AppError, match="Unexpected HTTP"):
                transport.send("getUser", RequestValues())

    @pytest.mark.parametrize(
        "arguments",
        [
            RequestValues({"unexpected": "fixture"}),
            RequestValues(query={"bogus": False}),
            RequestValues(body=None),
        ],
    )
    def test_invalid_input_has_no_network(
        self, contract: Contract, arguments: RequestValues
    ) -> None:
        """Invalid paths, queries, and bodies fail before sending."""
        server = Server(contract)
        with (
            httpx.Client(transport=httpx.MockTransport(server.handle)) as client,
            pytest.raises(AppError),
        ):
            Transport(Connection("synthetic-test-token"), contract, client).send(
                "getUser", arguments
            )
        assert server.requests == []

    def test_default_http_security(
        self, contract: Contract, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Production requests use TLS, no retries, and no environment proxies."""
        server = Server(contract)
        client = httpx.Client(transport=httpx.MockTransport(server.handle))
        constructor = Mock(return_value=client)
        monkeypatch.setattr("ynab_api_cli.transport.httpx.Client", constructor)
        Transport(Connection("synthetic-test-token"), contract).send(
            "getUser", RequestValues()
        )
        assert constructor.call_args.kwargs["verify"] is True
        assert constructor.call_args.kwargs["follow_redirects"] is False
        assert constructor.call_args.kwargs["trust_env"] is False


class TestRequestSemantics:
    """Ensure nested transaction features remain represented verbatim."""

    @pytest.mark.parametrize(
        "transaction",
        [
            {
                "amount": -1000,
                "category_id": None,
                "subtransactions": [
                    {"amount": -400, "category_id": None},
                    {"amount": -600, "memo": "split"},
                ],
            },
            {
                "amount": -1000,
                "payee_id": "00000000-0000-4000-8000-000000000001",
                "import_id": "YNAB:-1000:2026-01-01:1",
            },
            {
                "amount": 0,
                "cleared": "reconciled",
                "approved": False,
                "flag_color": "blue",
            },
        ],
    )
    def test_nested_features(
        self, contract: Contract, transaction: dict[str, object]
    ) -> None:
        """Splits, transfers, imports, flags, and reconciled status serialize intact."""
        payload = {
            "transaction": transaction
            | {
                "account_id": "00000000-0000-4000-8000-000000000001",
                "date": "2026-01-01",
            }
        }
        server = Server(contract, "createTransaction")
        with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
            transport = Transport(Connection("synthetic-test-token"), contract, client)
            Endpoint.dispatch(
                transport, RequestValues({"plan_id": "fixture"}, body=payload)
            )
        assert json.loads(server.requests[0].content) == payload
