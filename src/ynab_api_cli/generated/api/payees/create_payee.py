"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.post_payee_wrapper import PostPayeeWrapper
from ynab_api_cli.generated.models.save_payee_response import SavePayeeResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed createPayee operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        body: PostPayeeWrapper,
    ) -> Response[ErrorResponse | SavePayeeResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "createPayee",
            RequestValues(
                path={
                    "plan_id": plan_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.CREATED:
            parsed = SavePayeeResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | SavePayeeResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            body=TypeAdapter[PostPayeeWrapper](PostPayeeWrapper).validate_python(
                request.body
            ),
        )
