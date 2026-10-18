"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.new_transaction import NewTransaction


class PostTransactionsWrapper(BaseModel):
    """Typed PostTransactionsWrapper contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    transaction: NewTransaction | Unset = Field(alias="transaction", default=UNSET)
    transactions: list[NewTransaction] | Unset = Field(
        alias="transactions", default=UNSET
    )
