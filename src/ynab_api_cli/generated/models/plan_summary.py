"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.account import Account
    from ynab_api_cli.generated.models.currency_format_type_0 import CurrencyFormatType0
    from ynab_api_cli.generated.models.date_format_type_0 import DateFormatType0


class PlanSummary(BaseModel):
    """Typed PlanSummary contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    name: str = Field(alias="name")
    last_modified_on: datetime.datetime | Unset = Field(
        alias="last_modified_on", default=UNSET
    )
    first_month: datetime.date | Unset = Field(alias="first_month", default=UNSET)
    last_month: datetime.date | Unset = Field(alias="last_month", default=UNSET)
    date_format: DateFormatType0 | Unset | None = Field(
        alias="date_format", default=UNSET
    )
    currency_format: CurrencyFormatType0 | Unset | None = Field(
        alias="currency_format", default=UNSET
    )
    accounts: list[Account] | Unset = Field(alias="accounts", default=UNSET)
