"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class SaveSubTransaction(BaseModel):
    """Typed SaveSubTransaction contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    amount: int = Field(alias="amount")
    payee_id: Unset | UUID | None = Field(alias="payee_id", default=UNSET)
    payee_name: str | Unset | None = Field(alias="payee_name", default=UNSET)
    category_id: Unset | UUID | None = Field(alias="category_id", default=UNSET)
    memo: str | Unset | None = Field(alias="memo", default=UNSET)
