"""Bounded REST execution with independent schema checks and raw JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from http import HTTPStatus
from urllib.parse import quote

import httpx

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonCodec, RequestValues, Response


@dataclass(frozen=True, slots=True)
class Connection:
    """Connection settings whose token is never included in representations."""

    token: str = field(repr=False)
    plan_id: str | None = None

    def __post_init__(self) -> None:
        """Reject invalid header characters without including token contents."""
        if (
            not self.token
            or not self.token.isascii()
            or not self.token.isprintable()
            or any(character.isspace() for character in self.token)
        ):
            raise AppError("Access token must use visible ASCII without whitespace.")


class Transport:
    """Submit exactly one request; forbid credentials following redirects."""

    BASE_URL = "https://api.ynab.com/v1"

    def __init__(
        self,
        connection: Connection,
        contract: Contract | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.connection = connection
        self.contract = contract if contract is not None else Contract()
        self.client = client

    def send(self, identifier: str, request: RequestValues) -> Response[None]:
        """Validate, serialize, send once, and validate the response JSON."""
        operation = self.contract.get(identifier)
        self.contract.validate_request(operation, request)
        values = request.json()
        path = operation.path
        for name, value in self.contract.object(values["path"]).items():
            path = path.replace("{" + name + "}", quote(str(value), safe=""))
        query = {
            key: self.query_value(value)
            for key, value in self.contract.object(values["query"]).items()
        }
        body = (
            json.dumps(values["body"], ensure_ascii=False, allow_nan=False).encode(
                "utf-8"
            )
            if "body" in values
            else None
        )
        headers = {
            "Authorization": "Bearer " + self.connection.token,
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            if self.client is not None:
                response = self.client.request(
                    operation.method,
                    self.BASE_URL + path,
                    params=query,
                    content=body,
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
            else:
                with httpx.Client(
                    verify=True,
                    follow_redirects=False,
                    transport=httpx.HTTPTransport(retries=0),
                    trust_env=False,
                ) as client:
                    response = client.request(
                        operation.method,
                        self.BASE_URL + path,
                        params=query,
                        content=body,
                        headers=headers,
                        timeout=30,
                    )
        except httpx.HTTPError as err:
            uncertainty = (
                " Write outcome may be unknown; inspect state before retrying."
                if operation.write
                else ""
            )
            raise AppError("YNAB network failure; no retry." + uncertainty) from err
        if response.status_code >= HTTPStatus.MULTIPLE_CHOICES:
            retry = response.headers.get("Retry-After")
            suffix = (
                f" Retry-After: {retry}."
                if retry is not None and retry.isdecimal()
                else ""
            )
            raise AppError(f"YNAB HTTP {response.status_code}; no retry." + suffix)
        try:
            raw = JsonCodec.loads(response.text)
        except ValueError as err:
            raise AppError(
                "YNAB returned malformed JSON; outcome may be unknown."
            ) from err
        self.contract.validate_response(operation, response.status_code, raw)
        relevant = {
            key: value
            for key, value in response.headers.items()
            if key.lower() in {"content-type", "x-rate-limit", "retry-after"}
        }
        return Response(response.status_code, raw, relevant, None)

    @staticmethod
    def query_value(value: object) -> str:
        """Encode boolean query values in their lowercase wire form."""
        return str(value).lower() if isinstance(value, bool) else str(value)
