"""Shared JSON values and typed REST requests and responses."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import NoReturn, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel, GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema, core_schema

type JsonValue = (
    bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
)
T = TypeVar("T")


class Unset:
    """Distinguish an omitted field from an explicit JSON null."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Require the actual sentinel; never coerce a JSON object into omission."""
        return core_schema.is_instance_schema(cls)


UNSET = Unset()


class JsonCodec:
    """Convert validated Python values without erasing JSON field presence."""

    @classmethod
    def encode(cls, value: object) -> JsonValue:
        """Normalize JSON-compatible values and typed contract models."""
        if isinstance(value, BaseModel):
            return cls.encode(
                value.model_dump(mode="python", by_alias=True, exclude_unset=True)
            )
        if isinstance(value, dict):
            return {
                str(key): cls.encode(item)
                for key, item in value.items()
                if not isinstance(item, Unset)
            }
        if isinstance(value, (list, tuple)):
            return [cls.encode(item) for item in value]
        if isinstance(value, Enum):
            return cls.encode(value.value)
        if isinstance(value, (date, UUID)):
            return value.isoformat() if isinstance(value, date) else str(value)
        if value is None or isinstance(value, (str, int, float, bool)):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Non-finite numbers are not valid JSON.")
            return value
        raise ValueError("Value cannot be represented as JSON.")

    @staticmethod
    def loads(text: str) -> JsonValue:
        """Decode JSON into its recursive value type."""
        # JSON's parser guarantees this recursive union for successfully decoded input.
        return cast(
            "JsonValue", json.loads(text, parse_constant=JsonCodec.reject_constant)
        )

    @staticmethod
    def reject_constant(_text: str) -> NoReturn:
        """Reject non-standard JSON numeric constants without exposing values."""
        raise ValueError("Non-finite numbers are not valid JSON.")


@dataclass(frozen=True, slots=True)
class RequestValues:
    """Raw or typed endpoint arguments with explicit body presence."""

    path: Mapping[str, object] = field(default_factory=dict)
    query: Mapping[str, object] = field(default_factory=dict)
    body: object = UNSET

    def value(self, section: str, name: str, adapter: TypeAdapter[T]) -> T:
        """Decode one argument using the generated endpoint's exact type."""
        source = self.path if section == "path" else self.query
        return adapter.validate_python(source.get(name, UNSET))

    def json(self) -> dict[str, JsonValue]:
        """Normalize the request without inserting omitted bodies or fields."""
        values: dict[str, JsonValue] = {
            "path": JsonCodec.encode(self.path),
            "query": JsonCodec.encode(self.query),
        }
        if not isinstance(self.body, Unset):
            values["body"] = JsonCodec.encode(self.body)
        return values


@dataclass(frozen=True, slots=True)
class Response[T_co]:
    """HTTP response retaining raw JSON, headers, and its typed representation."""

    status: int
    raw: JsonValue
    headers: dict[str, str]
    parsed: T_co
