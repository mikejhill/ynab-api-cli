"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.transaction_detail import TransactionDetail


class TransactionResponseData(BaseModel):
    """Typed TransactionResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transaction: TransactionDetail = Field(alias="transaction")
    server_knowledge: int = Field(alias="server_knowledge")
