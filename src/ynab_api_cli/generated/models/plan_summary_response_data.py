"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.plan_summary import PlanSummary


class PlanSummaryResponseData(BaseModel):
    """Typed PlanSummaryResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    plans: list[PlanSummary] = Field(alias="plans")
    default_plan: PlanSummary | Unset | None = Field(
        alias="default_plan", default=UNSET
    )
