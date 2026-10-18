"""Synthetic HTTP and filesystem collaborators for deterministic tests."""

from __future__ import annotations

import json

import httpx

from ynab_api_cli.contract import Contract
from ynab_api_cli.contract_testing import SchemaCases
from ynab_api_cli.types import JsonValue, Unset


class Server:
    """Capture requests and synthesize schema-valid responses without networking."""

    def __init__(self, contract: Contract, operation: str = "getUser") -> None:
        self.contract = contract
        self.operation = operation
        self.requests: list[httpx.Request] = []
        self.status: int | None = None
        self.raw: JsonValue | Unset = Unset()
        self.text: str | None = None
        self.error: httpx.HTTPError | None = None

    def handle(self, request: httpx.Request) -> httpx.Response:
        """Return synthetic response data or the configured boundary failure."""
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        operation = self.contract.get(self.operation)
        definitions = self.contract.object(operation.definition["responses"])
        success = int(next(code for code in definitions if code.startswith("2")))
        status = self.status if self.status is not None else success
        if self.text is not None:
            return httpx.Response(status, text=self.text)
        content = self.contract.object(
            self.contract.object(definitions[str(success)])["content"]
        )
        schema = self.contract.object(
            self.contract.object(content["application/json"])["schema"]
        )
        raw = (
            SchemaCases(self.contract).sample(schema)
            if isinstance(self.raw, Unset)
            else self.raw
        )
        return httpx.Response(
            status,
            content=json.dumps(raw),
            headers={
                "Content-Type": "application/json",
                "Retry-After": "60",
                "X-Rate-Limit": "fixture",
                "Location": "https://untrusted.example/",
            },
        )
