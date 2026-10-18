"""Generated typed REST endpoint; regenerate rather than editing."""

from __future__ import annotations

from http import HTTPStatus

from ynab_api_cli.generated.models.user_response import UserResponse
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import UNSET, RequestValues, Response


class Endpoint:
    """Typed getUser operation."""

    @classmethod
    def execute(
        cls,
        *,
        transport: Transport,
    ) -> Response[UserResponse]:
        """Execute the typed request and retain its original response JSON."""
        raw = transport.send(
            "getUser",
            RequestValues(
                path={},
                query={},
                body=UNSET,
            ),
        )
        if raw.status == HTTPStatus.OK:
            parsed = UserResponse.model_validate(raw.raw)
            return Response(raw.status, raw.raw, raw.headers, parsed)
        raise ValueError("Validated response has no generated success binding.")

    @classmethod
    def dispatch(
        cls, transport: Transport, _request: RequestValues
    ) -> Response[UserResponse]:
        """Convert validated CLI inputs and call the explicitly typed method."""
        return cls.execute(
            transport=transport,
        )
