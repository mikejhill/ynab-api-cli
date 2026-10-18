"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.plan_summary_response import PlanSummaryResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import UNSET, RequestValues, Response, Unset


class Endpoint:
    """Typed getPlans operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        include_accounts: bool | Unset = UNSET,
    ) -> Response[ErrorResponse | PlanSummaryResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "getPlans",
            RequestValues(
                path={},
                query={
                    "include_accounts": include_accounts,
                },
                body=UNSET,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = PlanSummaryResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | PlanSummaryResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            include_accounts=request.value(
                "query", "include_accounts", TypeAdapter[bool | Unset](bool | Unset)
            ),
        )
