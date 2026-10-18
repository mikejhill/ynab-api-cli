"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SaveMonthCategory(BaseModel):
    """Typed SaveMonthCategory contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    budgeted: int = Field(alias="budgeted")
