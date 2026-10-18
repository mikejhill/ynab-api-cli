"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.payee import Payee


class PayeesResponseData(BaseModel):
    """Typed PayeesResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    payees: list[Payee] = Field(alias="payees")
    server_knowledge: int = Field(alias="server_knowledge")
