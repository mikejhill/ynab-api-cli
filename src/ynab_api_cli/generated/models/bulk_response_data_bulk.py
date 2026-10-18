"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BulkResponseDataBulk(BaseModel):
    """Typed BulkResponseDataBulk contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transaction_ids: list[str] = Field(alias="transaction_ids")
    duplicate_import_ids: list[str] = Field(alias="duplicate_import_ids")
