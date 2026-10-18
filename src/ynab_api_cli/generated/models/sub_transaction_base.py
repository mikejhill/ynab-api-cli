"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class SubTransactionBase(BaseModel):
    """Typed SubTransactionBase contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: str = Field(alias="id")
    transaction_id: str = Field(alias="transaction_id")
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
    transfer_transaction_id: str | Unset | None = Field(
        alias="transfer_transaction_id", default=UNSET
    )
