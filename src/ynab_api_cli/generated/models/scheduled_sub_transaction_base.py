"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class ScheduledSubTransactionBase(BaseModel):
    """Typed ScheduledSubTransactionBase contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    scheduled_transaction_id: UUID = Field(alias="scheduled_transaction_id")
    amount: int = Field(alias="amount")
    deleted: bool = Field(alias="deleted")
    memo: str | Unset | None = Field(alias="memo", default=UNSET)
    payee_id: Unset | UUID | None = Field(alias="payee_id", default=UNSET)
    payee_name: str | Unset | None = Field(alias="payee_name", default=UNSET)
    category_id: Unset | UUID | None = Field(alias="category_id", default=UNSET)
    category_name: str | Unset | None = Field(alias="category_name", default=UNSET)
    transfer_account_id: Unset | UUID | None = Field(
        alias="transfer_account_id", default=UNSET
    )
