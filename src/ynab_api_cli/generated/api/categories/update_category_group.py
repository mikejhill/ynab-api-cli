"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from pydantic import TypeAdapter

from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.patch_category_group_wrapper import (
    PatchCategoryGroupWrapper,
)
from ynab_api_cli.generated.models.save_category_group_response import (
    SaveCategoryGroupResponse,
)
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Endpoint:
    """Typed updateCategoryGroup operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
        plan_id: str,
        category_group_id: str,
        body: PatchCategoryGroupWrapper,
    ) -> Response[ErrorResponse | SaveCategoryGroupResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "updateCategoryGroup",
            RequestValues(
                path={
                    "plan_id": plan_id,
                    "category_group_id": category_group_id,
                },
                query={},
                body=body,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = SaveCategoryGroupResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, request: RequestValues
    ) -> Response[ErrorResponse | SaveCategoryGroupResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
            plan_id=request.value("path", "plan_id", TypeAdapter[str](str)),
            category_group_id=request.value(
                "path", "category_group_id", TypeAdapter[str](str)
            ),
            body=TypeAdapter[PatchCategoryGroupWrapper](
                PatchCategoryGroupWrapper
            ).validate_python(request.body),
        )
