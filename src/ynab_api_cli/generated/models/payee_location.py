"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PayeeLocation(BaseModel):
    """Typed PayeeLocation contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    payee_id: UUID = Field(alias="payee_id")
    latitude: str = Field(alias="latitude")
    longitude: str = Field(alias="longitude")
    deleted: bool = Field(alias="deleted")
