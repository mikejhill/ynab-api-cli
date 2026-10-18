"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CurrencyFormatType0(BaseModel):
    """Typed CurrencyFormatType0 contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )
    iso_code: str = Field(alias="iso_code")
    example_format: str = Field(alias="example_format")
    decimal_digits: int = Field(alias="decimal_digits")
    decimal_separator: str = Field(alias="decimal_separator")
    symbol_first: bool = Field(alias="symbol_first")
    group_separator: str = Field(alias="group_separator")
    currency_symbol: str = Field(alias="currency_symbol")
    display_symbol: bool = Field(alias="display_symbol")
