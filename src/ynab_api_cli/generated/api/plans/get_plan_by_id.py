"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.plan_detail_response import PlanDetailResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import UNSET, RequestValues, Response, Unset


class Endpoint:
    """Typed getPlanById operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        last_knowledge_of_server: int | Unset = UNSET,
    ) -> Response[ErrorResponse | PlanDetailResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "getPlanById",
            RequestValues(
                path={
                    "plan_id": plan_id,
                },
                query={
                    "last_knowledge_of_server": last_knowledge_of_server,
                },
                body=UNSET,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = PlanDetailResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | PlanDetailResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            last_knowledge_of_server=request.value(
                "query",
                "last_knowledge_of_server",
                TypeAdapter[int | Unset](int | Unset),
            ),
        )
