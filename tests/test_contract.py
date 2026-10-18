"""Independent operation inventory, wire expectations, and schema probes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import ClassVar
from urllib.parse import quote

import httpx
import pytest
from hypothesis import given
from hypothesis import strategies as st

from ynab_api_cli.contract import Contract
from ynab_api_cli.contract_testing import SchemaCases
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.generated.bindings import Bindings
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import JsonCodec, JsonValue, RequestValues


class WireFixtures:
    """Read the independent case table with explicit structural checks."""

    @staticmethod
    def load() -> list[list[JsonValue]]:
        """Require an array of case arrays rather than assuming decoded types."""
        value = JsonCodec.loads(
            (Path(__file__).parent / "fixtures/wire_cases.json").read_text(
                encoding="utf-8"
            )
        )
        if not isinstance(value, list):
            raise TypeError("Expected case array.")
        cases = [item for item in value if isinstance(item, list)]
        if len(cases) != len(value):
            raise ValueError("Expected every case to be an array.")
        return cases


class TestContract:
    """Require explicit examples for every public operation."""

    CASES: ClassVar[list[list[JsonValue]]] = WireFixtures.load()
    DELTA_OPERATIONS: ClassVar[frozenset[str]] = frozenset(
        {
            "getPlanById",
            "getAccounts",
            "getCategories",
            "getPayees",
            "getPlanMonths",
            "getScheduledTransactions",
        }
    )

    def test_complete_inventory(self, contract: Contract) -> None:
        """Spec, catalog, generated methods, and independent cases agree exactly."""
        names = {str(case[0]) for case in self.CASES}
        assert names == set(contract.operations) == set(contract.catalog)
        assert {op.alias for op in contract.operations.values()} == set(
            Bindings.operations
        )
        for op in contract.operations.values():
            assert contract.catalog[op.identifier] == {
                "method": op.method,
                "path": op.path,
            }

    @pytest.mark.parametrize("case", CASES, ids=[str(case[0]) for case in CASES])
    def test_every_wire_operation(
        self, contract: Contract, case: list[JsonValue]
    ) -> None:
        """Each generated operation produces the independently declared wire request."""
        identifier, verb, expected = str(case[0]), str(case[1]), str(case[2])
        operation = contract.get(identifier)
        path = {
            name: "2026-01-01"
            if name == "month"
            else "fixture /?& café"
            if name == "plan_id"
            else SchemaCases.UUID
            for name in re.findall(r"{(\w+)}", expected)
        }
        query: dict[str, object] = {}
        if identifier == "getPlans":
            query["include_accounts"] = False
        if identifier in self.DELTA_OPERATIONS:
            query["last_knowledge_of_server"] = 7
        if identifier.startswith("getTransactions"):
            query.update(
                {
                    "since_date": "2026-01-01",
                    "until_date": "2026-01-31",
                    "type": "unapproved",
                    "last_knowledge_of_server": 7,
                }
            )
        assert set(query) == {
            str(parameter["name"])
            for parameter in contract.parameters(operation)
            if parameter["in"] == "query"
        }
        response_defs = contract.object(operation.definition["responses"])
        status = int(next(name for name in response_defs if name.startswith("2")))
        response_schema = contract.object(
            contract.object(contract.object(response_defs[str(status)])["content"])[
                "application/json"
            ]
        )["schema"]
        raw = SchemaCases(contract).sample(contract.object(response_schema))
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            """Capture the HTTP boundary and return a synthetic success response."""
            requests.append(request)
            return httpx.Response(status, json=raw, headers={"X-Rate-Limit": "fixture"})

        request_values = (
            RequestValues(path, query, case[3])
            if len(case) == 4
            else RequestValues(path, query)
        )
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            transport = Transport(Connection("synthetic-test-token"), contract, client)
            result = Bindings.operations[operation.alias](transport, request_values)
        assert len(requests) == 1
        wire = requests[0]
        assert wire.method == verb
        assert wire.url.host == "api.ynab.com"
        for name, value in path.items():
            expected = expected.replace("{" + name + "}", quote(value, safe=""))
        assert wire.url.raw_path.split(b"?")[0].decode() == "/v1" + expected
        assert wire.headers["Authorization"] == "Bearer synthetic-test-token"
        assert wire.headers["Accept"] == "application/json"
        assert dict(wire.url.params) == {
            key: str(value).lower() if isinstance(value, bool) else str(value)
            for key, value in query.items()
        }
        if len(case) == 4:
            assert json.loads(wire.content) == case[3]
            assert wire.headers["Content-Type"] == "application/json"
        else:
            assert wire.content == b""
        assert result.raw == raw
        assert result.parsed is not None

    def test_every_schema_feature(self, contract: Contract) -> None:
        """Every schema node, enum value, and nullable branch has a valid witness."""
        probes = SchemaCases(contract).probes()
        assert len({probe.identifier for probe in probes}) == len(probes)
        for probe in probes:
            try:
                contract.validate(probe.schema, probe.value, probe.identifier)
            except AppError as err:
                pytest.fail(f"Schema witness failed: {probe.identifier}: {err}")

    @pytest.mark.parametrize(
        "payload", [{}, {"transaction": {}, "transactions": []}, {"transactions": None}]
    )
    def test_transaction_wrapper_semantics(
        self, contract: Contract, payload: dict[str, JsonValue]
    ) -> None:
        """Creation requires exactly one transaction collection representation."""
        with pytest.raises(AppError):
            contract.validate_request(
                contract.get("createTransaction"),
                RequestValues({"plan_id": "fixture"}, body=payload),
            )

    @given(st.integers(min_value=-(2**63), max_value=2**63 - 1), st.text())
    def test_milliunits_and_unicode(self, amount: int, memo: str) -> None:
        """Integer amounts and arbitrary memo text survive JSON without rounding."""
        value = {"amount": amount, "memo": memo, "approved": False, "category_id": None}
        assert JsonCodec.loads(json.dumps(JsonCodec.encode(value))) == value
