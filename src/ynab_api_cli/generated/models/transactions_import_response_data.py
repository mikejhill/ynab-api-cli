"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TransactionsImportResponseData(BaseModel):
    """Typed TransactionsImportResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transaction_ids: list[str] = Field(alias="transaction_ids")
