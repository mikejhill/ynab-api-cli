"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ynab_api_cli.generated.models.save_category_response_data import (
        SaveCategoryResponseData,
    )


class SaveCategoryResponse(BaseModel):
    """Typed SaveCategoryResponse contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    data: SaveCategoryResponseData = Field(alias="data")
