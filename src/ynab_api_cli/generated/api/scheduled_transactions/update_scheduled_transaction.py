"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.put_scheduled_transaction_wrapper import (
    PutScheduledTransactionWrapper,
)
from ynab_api_cli.generated.models.scheduled_transaction_response import (
    ScheduledTransactionResponse,
)
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed updateScheduledTransaction operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        scheduled_transaction_id: str,
        body: PutScheduledTransactionWrapper,
    ) -> Response[ErrorResponse | ScheduledTransactionResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "updateScheduledTransaction",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "scheduled_transaction_id": scheduled_transaction_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = ScheduledTransactionResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | ScheduledTransactionResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            scheduled_transaction_id=request.value(
                "path", "scheduled_transaction_id", TypeAdapter[str](str)
            ),
            body=TypeAdapter[PutScheduledTransactionWrapper](
                PutScheduledTransactionWrapper
            ).validate_python(request.body),
        )
