"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.save_category_goal_frequency import (
    SaveCategoryGoalFrequency,
)
from ynab_api_cli.types import UNSET, Unset


class ExistingCategory(BaseModel):
    """Typed ExistingCategory contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    name: str | Unset | None = Field(alias="name", default=UNSET)
    note: str | Unset | None = Field(alias="note", default=UNSET)
    category_group_id: UUID | Unset = Field(alias="category_group_id", default=UNSET)
    goal_target: int | Unset | None = Field(alias="goal_target", default=UNSET)
    goal_target_date: datetime.date | Unset | None = Field(
        alias="goal_target_date", default=UNSET
    )
    goal_needs_whole_amount: bool | Unset | None = Field(
        alias="goal_needs_whole_amount", default=UNSET
    )
    goal_frequency: SaveCategoryGoalFrequency | Unset = Field(
        alias="goal_frequency", default=UNSET
    )
