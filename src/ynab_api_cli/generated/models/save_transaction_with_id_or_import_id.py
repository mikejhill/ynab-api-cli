"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.flag_1 import Flag1
from ynab_api_cli.generated.models.flag_2 import Flag2
from ynab_api_cli.generated.models.flag_3 import Flag3
from ynab_api_cli.generated.models.transaction_cleared_status import (
    TransactionClearedStatus,
)
from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.save_sub_transaction import SaveSubTransaction


class SaveTransactionWithIdOrImportId(BaseModel):
    """Typed SaveTransactionWithIdOrImportId contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    account_id: UUID | Unset = Field(alias="account_id", default=UNSET)
    date: datetime.date | Unset = Field(alias="date", default=UNSET)
    amount: int | Unset = Field(alias="amount", default=UNSET)
    payee_id: Unset | UUID | None = Field(alias="payee_id", default=UNSET)
    payee_name: str | Unset | None = Field(alias="payee_name", default=UNSET)
    category_id: Unset | UUID | None = Field(alias="category_id", default=UNSET)
    memo: str | Unset | None = Field(alias="memo", default=UNSET)
    cleared: TransactionClearedStatus | Unset = Field(alias="cleared", default=UNSET)
    approved: bool | Unset = Field(alias="approved", default=UNSET)
    flag_color: Flag1 | Flag2 | Flag3 | Unset | None = Field(
        alias="flag_color", default=UNSET
    )
    subtransactions: list[SaveSubTransaction] | Unset = Field(
        alias="subtransactions", default=UNSET
    )
    id: str | Unset | None = Field(alias="id", default=UNSET)
    import_id: str | Unset | None = Field(alias="import_id", default=UNSET)
