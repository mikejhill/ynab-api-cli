"""Detect structural upstream changes independently of generated signatures."""

from __future__ import annotations

import copy

import httpx
import pytest
import yaml

from ynab_api_cli.compat import Compatibility
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError


class TestCompatibility:
    """No optional addition or schema change can pass silently."""

    def test_unchanged_and_documentation(self, contract: Contract) -> None:
        """Descriptions are reported without treating them as structural changes."""
        checker = Compatibility(contract)
        assert checker.compare(contract.document)["compatible"] is True
        candidate = copy.deepcopy(contract.document)
        contract.object(candidate["info"])["description"] = "Documentation update"
        report = checker.compare(candidate)
        assert report["compatible"] is True
        assert report["documentation_only"] is True
        assert checker.digest(candidate) != checker.digest(contract.document)

    @pytest.mark.parametrize(
        "change", ["added", "removed", "parameter", "schema", "server"]
    )
    def test_structural_changes(self, contract: Contract, change: str) -> None:
        """Operations, optional parameters, schema fields, and servers trigger drift."""
        candidate = copy.deepcopy(contract.document)
        paths = contract.object(candidate["paths"])
        if change == "added":
            operation = copy.deepcopy(
                contract.object(contract.object(paths["/user"])["get"])
            )
            operation["operationId"] = "getNewFeature"
            paths["/new-feature"] = {"get": operation}
        elif change == "removed":
            del paths["/user"]
        elif change == "parameter":
            contract.object(contract.object(paths["/user"])["get"])["parameters"] = [
                {"name": "optional_new", "in": "query", "schema": {"type": "string"}}
            ]
        elif change == "schema":
            schemas = contract.object(
                contract.object(candidate["components"])["schemas"]
            )
            contract.object(contract.object(schemas["User"])["properties"])[
                "optional_new"
            ] = {"type": "string"}
        else:
            candidate["servers"] = [{"url": "https://changed.example"}]
        report = Compatibility(contract).compare(candidate)
        assert report["compatible"] is False
        if change == "added":
            assert report["missing_tests"] == ["getNewFeature"]

    def test_http_fetch(self, contract: Contract) -> None:
        """Upstream requests have no credentials and obey timeout boundaries."""
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            """Return the public YAML fixture."""
            requests.append(request)
            return httpx.Response(200, text=yaml.safe_dump(contract.document))

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            assert Compatibility(contract).fetch(client) == contract.document
        assert "Authorization" not in requests[0].headers

    def test_fetch_failure(self, contract: Contract) -> None:
        """Public contract fetch failures are explicit and sanitized."""

        def handler(_request: httpx.Request) -> httpx.Response:
            """Return a failed public-contract request."""
            return httpx.Response(500)

        with (
            httpx.Client(transport=httpx.MockTransport(handler)) as client,
            pytest.raises(AppError, match="upstream contract"),
        ):
            Compatibility(contract).fetch(client)
