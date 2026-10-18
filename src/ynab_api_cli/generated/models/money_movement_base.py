"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class MoneyMovementBase(BaseModel):
    """Typed MoneyMovementBase contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    amount: int = Field(alias="amount")
    month: datetime.date | Unset | None = Field(alias="month", default=UNSET)
    moved_at: datetime.datetime | Unset | None = Field(alias="moved_at", default=UNSET)
    note: str | Unset | None = Field(alias="note", default=UNSET)
    money_movement_group_id: Unset | UUID | None = Field(
        alias="money_movement_group_id", default=UNSET
    )
    performed_by_user_id: Unset | UUID | None = Field(
        alias="performed_by_user_id", default=UNSET
    )
    from_category_id: Unset | UUID | None = Field(
        alias="from_category_id", default=UNSET
    )
    to_category_id: Unset | UUID | None = Field(alias="to_category_id", default=UNSET)
