"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.hybrid_transaction import HybridTransaction


class HybridTransactionsResponseData(BaseModel):
    """Typed HybridTransactionsResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transactions: list[HybridTransaction] = Field(alias="transactions")
    server_knowledge: int | Unset = Field(alias="server_knowledge", default=UNSET)
