"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.category_group_with_categories import (
        CategoryGroupWithCategories,
    )


class CategoriesResponseData(BaseModel):
    """Typed CategoriesResponseData contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    category_groups: list[CategoryGroupWithCategories] = Field(alias="category_groups")
    server_knowledge: int = Field(alias="server_knowledge")
