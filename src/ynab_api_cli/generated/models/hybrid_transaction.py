"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.debt_1 import Debt1
from ynab_api_cli.generated.models.debt_2 import Debt2
from ynab_api_cli.generated.models.debt_3 import Debt3
from ynab_api_cli.generated.models.flag_1 import Flag1
from ynab_api_cli.generated.models.flag_2 import Flag2
from ynab_api_cli.generated.models.flag_3 import Flag3
from ynab_api_cli.generated.models.hybrid_transaction_type import HybridTransactionType
from ynab_api_cli.generated.models.transaction_cleared_status import (
    TransactionClearedStatus,
)
from ynab_api_cli.types import UNSET, Unset


class HybridTransaction(BaseModel):
    """Typed HybridTransaction contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: str = Field(alias="id")
    date: datetime.date = Field(alias="date")
    amount: int = Field(alias="amount")
    cleared: TransactionClearedStatus = Field(alias="cleared")
    approved: bool = Field(alias="approved")
    account_id: UUID = Field(alias="account_id")
    deleted: bool = Field(alias="deleted")
    type_: HybridTransactionType = Field(alias="type")
    account_name: str = Field(alias="account_name")
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
    transfer_transaction_id: str | Unset | None = Field(
        alias="transfer_transaction_id", default=UNSET
    )
    matched_transaction_id: str | Unset | None = Field(
        alias="matched_transaction_id", default=UNSET
    )
    import_id: str | Unset | None = Field(alias="import_id", default=UNSET)
    import_payee_name: str | Unset | None = Field(
        alias="import_payee_name", default=UNSET
    )
    import_payee_name_original: str | Unset | None = Field(
        alias="import_payee_name_original", default=UNSET
    )
    debt_transaction_type: Debt1 | Debt2 | Debt3 | Unset | None = Field(
        alias="debt_transaction_type", default=UNSET
    )
    amount_formatted: str | Unset = Field(alias="amount_formatted", default=UNSET)
    amount_currency: float | Unset = Field(alias="amount_currency", default=UNSET)
    parent_transaction_id: str | Unset | None = Field(
        alias="parent_transaction_id", default=UNSET
    )
    payee_name: str | Unset | None = Field(alias="payee_name", default=UNSET)
    category_name: str | Unset = Field(alias="category_name", default=UNSET)
