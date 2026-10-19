"""Bounded REST execution with independent schema checks and raw JSON."""

from __future__ import annotations

import json
import time
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
    additional_tokens: tuple[str, ...] = field(default=(), repr=False)

    @property
    def tokens(self) -> tuple[str, ...]:
        """Return the ordered credential pool without exposing it in repr."""
        return (self.token, *self.additional_tokens)

    def __post_init__(self) -> None:
        """Reject invalid header characters without including token contents."""
        if any(
            not token
            or not token.isascii()
            or not token.isprintable()
            or any(character.isspace() for character in token)
            for token in self.tokens
        ):
            raise AppError("Access token must use visible ASCII without whitespace.")
        if len(set(self.tokens)) != len(self.tokens):
            raise AppError("Duplicate access tokens are not allowed.")


class Transport:
    """Roll over only explicit 429 responses; never replay uncertain requests."""

    BASE_URL = "https://api.ynab.com/v1"
    MAX_RETRY_DIGITS = 9

    def __init__(
        self,
        connection: Connection,
        contract: Contract | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.connection = connection
        self.contract = contract if contract is not None else Contract()
        self.client = client
        self._cursor = 0
        self._cooldowns: dict[int, float] = {}
        self.request_count = 0
        self.request_limit: int | None = None

    @property
    def active_token_index(self) -> int:
        """Expose the successful pool position without exposing a credential."""
        return self._cursor

    def send(self, identifier: str, request: RequestValues) -> Response[None]:
        """Validate and send with at most one attempt per available PAT."""
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
        try:
            if self.client is None:
                with httpx.Client(
                    verify=True,
                    follow_redirects=False,
                    transport=httpx.HTTPTransport(retries=0),
                    trust_env=False,
                ) as client:
                    response = self._submit(client, operation.method, path, query, body)
            else:
                response = self._submit(
                    self.client, operation.method, path, query, body
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

    def _submit(
        self,
        client: httpx.Client,
        method: str,
        path: str,
        query: dict[str, str],
        body: bytes | None,
    ) -> httpx.Response:
        """Try each available credential once, retaining session cooldowns."""
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        count = len(self.connection.tokens)
        start = self._cursor
        for offset in range(count):
            index = (start + offset) % count
            if self._cooldowns.get(index, 0) > time.monotonic():
                continue
            if (
                self.request_limit is not None
                and self.request_count >= self.request_limit
            ):
                raise AppError("Request budget exhausted; no request submitted.")
            self.request_count += 1
            response = client.request(
                method,
                self.BASE_URL + path,
                params=query,
                content=body,
                headers=headers
                | {"Authorization": "Bearer " + self.connection.tokens[index]},
                timeout=30,
                follow_redirects=False,
            )
            self._cursor = index
            if response.status_code != HTTPStatus.TOO_MANY_REQUESTS:
                return response
            retry = response.headers.get("Retry-After", "")
            delay = (
                max(1, int(retry))
                if retry.isascii()
                and retry.isdecimal()
                and len(retry) <= self.MAX_RETRY_DIGITS
                else 3600
            )
            self._cooldowns[index] = time.monotonic() + delay
            self._cursor = (index + 1) % count
        raise AppError(
            "YNAB HTTP 429; all configured PATs are rate limited; no further attempts."
        )

    @staticmethod
    def query_value(value: object) -> str:
        """Encode boolean query values in their lowercase wire form."""
        return str(value).lower() if isinstance(value, bool) else str(value)
