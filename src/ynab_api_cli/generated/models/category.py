"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.goal_1 import Goal1
from ynab_api_cli.generated.models.goal_2 import Goal2
from ynab_api_cli.generated.models.goal_3 import Goal3
from ynab_api_cli.types import UNSET, Unset


class Category(BaseModel):
    """Typed Category contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    category_group_id: UUID = Field(alias="category_group_id")
    name: str = Field(alias="name")
    hidden: bool = Field(alias="hidden")
    internal: bool = Field(alias="internal")
    budgeted: int = Field(alias="budgeted")
    activity: int = Field(alias="activity")
    balance: int = Field(alias="balance")
    deleted: bool = Field(alias="deleted")
    category_group_name: str | Unset = Field(alias="category_group_name", default=UNSET)
    original_category_group_id: Unset | UUID | None = Field(
        alias="original_category_group_id", default=UNSET
    )
    note: str | Unset | None = Field(alias="note", default=UNSET)
    goal_type: Goal1 | Goal2 | Goal3 | Unset | None = Field(
        alias="goal_type", default=UNSET
    )
    goal_needs_whole_amount: bool | Unset | None = Field(
        alias="goal_needs_whole_amount", default=UNSET
    )
    goal_day: int | Unset | None = Field(alias="goal_day", default=UNSET)
    goal_cadence: int | Unset | None = Field(alias="goal_cadence", default=UNSET)
    goal_cadence_frequency: int | Unset | None = Field(
        alias="goal_cadence_frequency", default=UNSET
    )
    goal_creation_month: datetime.date | Unset | None = Field(
        alias="goal_creation_month", default=UNSET
    )
    goal_target: int | Unset | None = Field(alias="goal_target", default=UNSET)
    goal_target_month: datetime.date | Unset | None = Field(
        alias="goal_target_month", default=UNSET
    )
    goal_target_date: datetime.date | Unset | None = Field(
        alias="goal_target_date", default=UNSET
    )
    goal_percentage_complete: int | Unset | None = Field(
        alias="goal_percentage_complete", default=UNSET
    )
    goal_months_to_budget: int | Unset | None = Field(
        alias="goal_months_to_budget", default=UNSET
    )
    goal_under_funded: int | Unset | None = Field(
        alias="goal_under_funded", default=UNSET
    )
    goal_overall_funded: int | Unset | None = Field(
        alias="goal_overall_funded", default=UNSET
    )
    goal_overall_left: int | Unset | None = Field(
        alias="goal_overall_left", default=UNSET
    )
    goal_snoozed_at: datetime.datetime | Unset | None = Field(
        alias="goal_snoozed_at", default=UNSET
    )
    balance_formatted: str | Unset = Field(alias="balance_formatted", default=UNSET)
    balance_currency: float | Unset = Field(alias="balance_currency", default=UNSET)
    activity_formatted: str | Unset = Field(alias="activity_formatted", default=UNSET)
    activity_currency: float | Unset = Field(alias="activity_currency", default=UNSET)
    budgeted_formatted: str | Unset = Field(alias="budgeted_formatted", default=UNSET)
    budgeted_currency: float | Unset = Field(alias="budgeted_currency", default=UNSET)
    goal_target_formatted: str | Unset | None = Field(
        alias="goal_target_formatted", default=UNSET
    )
    goal_target_currency: float | Unset | None = Field(
        alias="goal_target_currency", default=UNSET
    )
    goal_under_funded_formatted: str | Unset | None = Field(
        alias="goal_under_funded_formatted", default=UNSET
    )
    goal_under_funded_currency: float | Unset | None = Field(
        alias="goal_under_funded_currency", default=UNSET
    )
    goal_overall_funded_formatted: str | Unset | None = Field(
        alias="goal_overall_funded_formatted", default=UNSET
    )
    goal_overall_funded_currency: float | Unset | None = Field(
        alias="goal_overall_funded_currency", default=UNSET
    )
    goal_overall_left_formatted: str | Unset | None = Field(
        alias="goal_overall_left_formatted", default=UNSET
    )
    goal_overall_left_currency: float | Unset | None = Field(
        alias="goal_overall_left_currency", default=UNSET
    )
