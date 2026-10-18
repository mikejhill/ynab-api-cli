"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.account import Account
    from ynab_api_cli.generated.models.category_base import CategoryBase
    from ynab_api_cli.generated.models.category_group import CategoryGroup
    from ynab_api_cli.generated.models.currency_format_type_0 import CurrencyFormatType0
    from ynab_api_cli.generated.models.date_format_type_0 import DateFormatType0
    from ynab_api_cli.generated.models.month_detail_base import MonthDetailBase
    from ynab_api_cli.generated.models.payee import Payee
    from ynab_api_cli.generated.models.payee_location import PayeeLocation
    from ynab_api_cli.generated.models.scheduled_sub_transaction_base import (
        ScheduledSubTransactionBase,
    )
    from ynab_api_cli.generated.models.scheduled_transaction_summary_base import (
        ScheduledTransactionSummaryBase,
    )
    from ynab_api_cli.generated.models.sub_transaction_base import SubTransactionBase
    from ynab_api_cli.generated.models.transaction_summary_base import (
        TransactionSummaryBase,
    )


class PlanDetail(BaseModel):
    """Typed PlanDetail contract representation."""

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
    payees: list[Payee] | Unset = Field(alias="payees", default=UNSET)
    payee_locations: list[PayeeLocation] | Unset = Field(
        alias="payee_locations", default=UNSET
    )
    category_groups: list[CategoryGroup] | Unset = Field(
        alias="category_groups", default=UNSET
    )
    categories: list[CategoryBase] | Unset = Field(alias="categories", default=UNSET)
    months: list[MonthDetailBase] | Unset = Field(alias="months", default=UNSET)
    transactions: list[TransactionSummaryBase] | Unset = Field(
        alias="transactions", default=UNSET
    )
    subtransactions: list[SubTransactionBase] | Unset = Field(
        alias="subtransactions", default=UNSET
    )
    scheduled_transactions: list[ScheduledTransactionSummaryBase] | Unset = Field(
        alias="scheduled_transactions", default=UNSET
    )
    scheduled_subtransactions: list[ScheduledSubTransactionBase] | Unset = Field(
        alias="scheduled_subtransactions", default=UNSET
    )
