"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class Payee(BaseModel):
    """Typed Payee contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    name: str = Field(alias="name")
    deleted: bool = Field(alias="deleted")
    transfer_account_id: str | Unset | None = Field(
        alias="transfer_account_id", default=UNSET
    )
