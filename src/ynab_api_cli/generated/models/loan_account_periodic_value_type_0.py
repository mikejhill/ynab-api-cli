"""Generated contract model; regenerate rather than editing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, TypeAdapter, model_validator


class LoanAccountPeriodicValueType0(BaseModel):
    """Typed LoanAccountPeriodicValueType0 contract representation."""

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True
    )

    @model_validator(mode="before")
    @classmethod
    def validate_extra_values(cls, value: object) -> object:
        """Validate typed map entries before the Pydantic model boundary."""
        if not isinstance(value, dict):
            return value
        declared = {field.alias or name for name, field in cls.model_fields.items()}
        extra = {
            str(key): item for key, item in value.items() if str(key) not in declared
        }
        TypeAdapter[dict[str, int]](dict[str, int]).validate_python(extra)
        return value

    @property
    def additional_properties(self) -> dict[str, int]:
        """Return additional entries through a validated typed boundary."""
        return TypeAdapter[dict[str, int]](dict[str, int]).validate_python(
            self.model_extra or {}
        )
