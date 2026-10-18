"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.money_movement_group import MoneyMovementGroup


class MoneyMovementGroupsResponseData(BaseModel):
    """Typed MoneyMovementGroupsResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    money_movement_groups: list[MoneyMovementGroup] = Field(
        alias="money_movement_groups"
    )
    server_knowledge: int = Field(alias="server_knowledge")
