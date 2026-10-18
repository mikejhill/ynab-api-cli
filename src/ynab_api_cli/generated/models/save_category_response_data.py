"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.category import Category


class SaveCategoryResponseData(BaseModel):
    """Typed SaveCategoryResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    category: Category = Field(alias="category")
    server_knowledge: int = Field(alias="server_knowledge")
