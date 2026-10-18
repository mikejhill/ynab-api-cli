"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.money_movement import MoneyMovement


class MoneyMovementsResponseData(BaseModel):
    """Typed MoneyMovementsResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    money_movements: list[MoneyMovement] = Field(alias="money_movements")
    server_knowledge: int = Field(alias="server_knowledge")
