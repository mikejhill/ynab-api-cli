"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

import datetime
from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.get_transactions_type import GetTransactionsType
from ynab_api_cli.generated.models.transactions_response import TransactionsResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import UNSET, RequestValues, Response, Unset


class Endpoint:
    """Typed getTransactions operation."""

    @classmethod
    def execute(  # noqa: PLR0913 - preserve the endpoint contract.
        cls,
        *,
        transport: Transport,
        plan_id: str,
        since_date: datetime.date | Unset = UNSET,
        until_date: datetime.date | Unset = UNSET,
        type_: GetTransactionsType | Unset = UNSET,
        last_knowledge_of_server: int | Unset = UNSET,
    ) -> Response[ErrorResponse | TransactionsResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "getTransactions",
            RequestValues(
                path={
                    "plan_id": plan_id,
                },
                query={
                    "since_date": since_date,
                    "until_date": until_date,
                    "type": type_,
                    "last_knowledge_of_server": last_knowledge_of_server,
                },
                body=UNSET,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = TransactionsResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | TransactionsResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            since_date=request.value(
                "query",
                "since_date",
                TypeAdapter[datetime.date | Unset](datetime.date | Unset),
            ),
            until_date=request.value(
                "query",
                "until_date",
                TypeAdapter[datetime.date | Unset](datetime.date | Unset),
            ),
            type_=request.value(
                "query",
                "type",
                TypeAdapter[GetTransactionsType | Unset](GetTransactionsType | Unset),
            ),
            last_knowledge_of_server=request.value(
                "query",
                "last_knowledge_of_server",
                TypeAdapter[int | Unset](int | Unset),
            ),
        )
