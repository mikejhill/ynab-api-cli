"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

import datetime
from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.money_movements_response import (
    MoneyMovementsResponse,
)
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import UNSET, RequestValues, Response


class Endpoint:
    """Typed getMoneyMovementsByMonth operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        month: datetime.date,
    ) -> Response[ErrorResponse | MoneyMovementsResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "getMoneyMovementsByMonth",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "month": month,
                },
                query={},
                body=UNSET,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = MoneyMovementsResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | MoneyMovementsResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            month=request.value(
                "path", "month", TypeAdapter[datetime.date](datetime.date)
            ),
        )
