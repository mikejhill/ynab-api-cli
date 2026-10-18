"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ynab_api_cli.types import UNSET, Unset


class SavePayee(BaseModel):
    """Typed SavePayee contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    name: str | Unset = Field(alias="name", default=UNSET)
