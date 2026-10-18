"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.flag_1 import Flag1
from ynab_api_cli.generated.models.flag_2 import Flag2
from ynab_api_cli.generated.models.flag_3 import Flag3
from ynab_api_cli.generated.models.scheduled_transaction_summary_base_frequency import (
    ScheduledTransactionSummaryBaseFrequency,
)
from ynab_api_cli.types import UNSET, Unset


class ScheduledTransactionSummary(BaseModel):
    """Typed ScheduledTransactionSummary contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    date_first: datetime.date = Field(alias="date_first")
    date_next: datetime.date = Field(alias="date_next")
    frequency: ScheduledTransactionSummaryBaseFrequency = Field(alias="frequency")
    amount: int = Field(alias="amount")
    account_id: UUID = Field(alias="account_id")
    deleted: bool = Field(alias="deleted")
    memo: str | Unset | None = Field(alias="memo", default=UNSET)
    flag_color: Flag1 | Flag2 | Flag3 | Unset | None = Field(
        alias="flag_color", default=UNSET
    )
    flag_name: str | Unset | None = Field(alias="flag_name", default=UNSET)
    payee_id: Unset | UUID | None = Field(alias="payee_id", default=UNSET)
    category_id: Unset | UUID | None = Field(alias="category_id", default=UNSET)
    transfer_account_id: Unset | UUID | None = Field(
        alias="transfer_account_id", default=UNSET
    )
    amount_formatted: str | Unset = Field(alias="amount_formatted", default=UNSET)
    amount_currency: float | Unset = Field(alias="amount_currency", default=UNSET)
