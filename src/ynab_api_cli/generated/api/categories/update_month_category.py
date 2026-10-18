"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

import datetime
from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.patch_month_category_wrapper import (
    PatchMonthCategoryWrapper,
)
from ynab_api_cli.generated.models.save_category_response import SaveCategoryResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed updateMonthCategory operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        month: datetime.date,
        category_id: str,
        body: PatchMonthCategoryWrapper,
    ) -> Response[ErrorResponse | SaveCategoryResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "updateMonthCategory",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "month": month,
                    "category_id": category_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = SaveCategoryResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | SaveCategoryResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            month=request.value(
                "path", "month", TypeAdapter[datetime.date](datetime.date)
            ),
            category_id=request.value("path", "category_id", TypeAdapter[str](str)),
            body=TypeAdapter[PatchMonthCategoryWrapper](
                PatchMonthCategoryWrapper
            ).validate_python(request.body),
        )
