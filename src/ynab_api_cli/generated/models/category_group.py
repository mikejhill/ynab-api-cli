"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryGroup(BaseModel):
    """Typed CategoryGroup contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    name: str = Field(alias="name")
    hidden: bool = Field(alias="hidden")
    internal: bool = Field(alias="internal")
    deleted: bool = Field(alias="deleted")
