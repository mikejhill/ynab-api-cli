"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class MonthSummaryBase(BaseModel):
    """Typed MonthSummaryBase contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    month: datetime.date = Field(alias="month")
    income: int = Field(alias="income")
    budgeted: int = Field(alias="budgeted")
    activity: int = Field(alias="activity")
    to_be_budgeted: int = Field(alias="to_be_budgeted")
    deleted: bool = Field(alias="deleted")
    note: str | Unset | None = Field(alias="note", default=UNSET)
    age_of_money: int | Unset | None = Field(alias="age_of_money", default=UNSET)
