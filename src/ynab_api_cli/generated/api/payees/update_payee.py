"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.patch_payee_wrapper import PatchPayeeWrapper
from ynab_api_cli.generated.models.save_payee_response import SavePayeeResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed updatePayee operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        payee_id: str,
        body: PatchPayeeWrapper,
    ) -> Response[ErrorResponse | SavePayeeResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "updatePayee",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "payee_id": payee_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.OK:
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
            payee_id=request.value("path", "payee_id", TypeAdapter[str](str)),
            body=TypeAdapter[PatchPayeeWrapper](PatchPayeeWrapper).validate_python(
                request.body
            ),
        )
