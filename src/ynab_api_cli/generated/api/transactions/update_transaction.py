"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.put_transaction_wrapper import PutTransactionWrapper
from ynab_api_cli.generated.models.transaction_response import TransactionResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed updateTransaction operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        transaction_id: str,
        body: PutTransactionWrapper,
    ) -> Response[ErrorResponse | TransactionResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "updateTransaction",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "transaction_id": transaction_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = TransactionResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | TransactionResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            transaction_id=request.value(
                "path", "transaction_id", TypeAdapter[str](str)
            ),
            body=TypeAdapter[PutTransactionWrapper](
                PutTransactionWrapper
            ).validate_python(request.body),
        )
