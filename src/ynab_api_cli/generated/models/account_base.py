"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.account_type import AccountType
from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.loan_account_periodic_value_type_0 import (
        LoanAccountPeriodicValueType0,
    )


class AccountBase(BaseModel):
    """Typed AccountBase contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    name: str = Field(alias="name")
    type_: AccountType = Field(alias="type")
    on_budget: bool = Field(alias="on_budget")
    closed: bool = Field(alias="closed")
    balance: int = Field(alias="balance")
    cleared_balance: int = Field(alias="cleared_balance")
    uncleared_balance: int = Field(alias="uncleared_balance")
    transfer_payee_id: UUID | None = Field(alias="transfer_payee_id")
    deleted: bool = Field(alias="deleted")
    note: str | Unset | None = Field(alias="note", default=UNSET)
    direct_import_linked: bool | Unset = Field(
        alias="direct_import_linked", default=UNSET
    )
    direct_import_in_error: bool | Unset = Field(
        alias="direct_import_in_error", default=UNSET
    )
    last_reconciled_at: datetime.datetime | Unset | None = Field(
        alias="last_reconciled_at", default=UNSET
    )
    debt_original_balance: int | Unset | None = Field(
        alias="debt_original_balance", default=UNSET
    )
    debt_interest_rates: LoanAccountPeriodicValueType0 | Unset | None = Field(
        alias="debt_interest_rates", default=UNSET
    )
    debt_minimum_payments: LoanAccountPeriodicValueType0 | Unset | None = Field(
        alias="debt_minimum_payments", default=UNSET
    )
    debt_escrow_amounts: LoanAccountPeriodicValueType0 | Unset | None = Field(
        alias="debt_escrow_amounts", default=UNSET
    )
