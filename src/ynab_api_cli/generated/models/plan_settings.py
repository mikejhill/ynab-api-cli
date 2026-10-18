"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.currency_format_type_0 import CurrencyFormatType0
    from ynab_api_cli.generated.models.date_format_type_0 import DateFormatType0


class PlanSettings(BaseModel):
    """Typed PlanSettings contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    date_format: DateFormatType0 | None = Field(alias="date_format")
    currency_format: CurrencyFormatType0 | None = Field(alias="currency_format")
