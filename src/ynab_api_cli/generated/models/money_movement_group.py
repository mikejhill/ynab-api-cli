"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class MoneyMovementGroup(BaseModel):
    """Typed MoneyMovementGroup contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    group_created_at: datetime.datetime = Field(alias="group_created_at")
    month: datetime.date = Field(alias="month")
    note: str | Unset | None = Field(alias="note", default=UNSET)
    performed_by_user_id: Unset | UUID | None = Field(
        alias="performed_by_user_id", default=UNSET
    )
