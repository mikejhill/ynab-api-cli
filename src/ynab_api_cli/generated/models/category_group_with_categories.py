"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.category import Category


class CategoryGroupWithCategories(BaseModel):
    """Typed CategoryGroupWithCategories contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    id: UUID = Field(alias="id")
    name: str = Field(alias="name")
    hidden: bool = Field(alias="hidden")
    internal: bool = Field(alias="internal")
    deleted: bool = Field(alias="deleted")
    categories: list[Category] = Field(alias="categories")
