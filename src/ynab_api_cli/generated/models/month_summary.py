"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class MonthSummary(BaseModel):
    """Typed MonthSummary contract representation."""

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
    income_formatted: str | Unset = Field(alias="income_formatted", default=UNSET)
    income_currency: float | Unset = Field(alias="income_currency", default=UNSET)
    budgeted_formatted: str | Unset = Field(alias="budgeted_formatted", default=UNSET)
    budgeted_currency: float | Unset = Field(alias="budgeted_currency", default=UNSET)
    activity_formatted: str | Unset = Field(alias="activity_formatted", default=UNSET)
    activity_currency: float | Unset = Field(alias="activity_currency", default=UNSET)
    to_be_budgeted_formatted: str | Unset = Field(
        alias="to_be_budgeted_formatted", default=UNSET
    )
    to_be_budgeted_currency: float | Unset = Field(
        alias="to_be_budgeted_currency", default=UNSET
    )
