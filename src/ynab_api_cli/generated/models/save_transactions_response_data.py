"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.transaction_detail import TransactionDetail


class SaveTransactionsResponseData(BaseModel):
    """Typed SaveTransactionsResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transaction_ids: list[str] = Field(alias="transaction_ids")
    server_knowledge: int = Field(alias="server_knowledge")
    transaction: TransactionDetail | Unset = Field(alias="transaction", default=UNSET)
    transactions: list[TransactionDetail] | Unset = Field(
        alias="transactions", default=UNSET
    )
    duplicate_import_ids: list[str] | Unset = Field(
        alias="duplicate_import_ids", default=UNSET
    )
