"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.generated.models.save_account_type import SaveAccountType


class SaveAccount(BaseModel):
    """Typed SaveAccount contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    name: str = Field(alias="name")
    type_: SaveAccountType = Field(alias="type")
    balance: int = Field(alias="balance")
