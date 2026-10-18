"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SaveCategoryGroup(BaseModel):
    """Typed SaveCategoryGroup contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    name: str = Field(alias="name")
