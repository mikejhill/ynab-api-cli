"""Enumerate contract features and synthesize supplemental schema probes."""

from __future__ import annotations

from dataclasses import dataclass

from ynab_api_cli.contract import Contract
from ynab_api_cli.types import JsonValue


@dataclass(frozen=True, slots=True)
class Probe:
    """One schema feature and a candidate value to validate independently."""

    identifier: str
    schema: dict[str, JsonValue]
    value: JsonValue


class SchemaCases:
    """Exercise each reachable schema node in addition to handwritten wire cases."""

    UUID = "00000000-0000-4000-8000-000000000001"

    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        self.schemas = contract.object(
            contract.object(contract.document["components"])["schemas"]
        )

    def sample(self, schema: dict[str, JsonValue]) -> JsonValue:
        """Construct a positive witness for the schema's declared structure."""
        reference = schema.get("$ref")
        if isinstance(reference, str):
            return self.sample(
                self.contract.object(self.schemas[reference.rsplit("/", 1)[-1]])
            )
        enum = schema.get("enum")
        if isinstance(enum, list):
            return enum[0]
        for key in ("allOf", "anyOf", "oneOf"):
            branches = schema.get(key)
            if isinstance(branches, list):
                values = [self.sample(self.contract.object(item)) for item in branches]
                if key != "allOf":
                    return values[0]
                if not all(isinstance(item, dict) for item in values):
                    return values[0]
                merged: dict[str, JsonValue] = {}
                for item in values:
                    merged.update(self.contract.object(item))
                return merged
        return self.primitive(schema)

    def primitive(self, schema: dict[str, JsonValue]) -> JsonValue:
        """Construct a witness for a primitive, array, or object schema."""
        kind = schema.get("type")
        if isinstance(kind, list):
            kind = next(item for item in kind if item != "null")
        if kind == "object" or "properties" in schema or "required" in schema:
            result = {
                key: self.sample(self.contract.object(value))
                for key, value in self.contract.object(
                    schema.get("properties", {})
                ).items()
            }
            extras = schema.get("additionalProperties")
            if isinstance(extras, dict):
                result["2026-01-01"] = self.sample(extras)
            return result
        if kind == "array":
            return [self.sample(self.contract.object(schema["items"]))]
        if kind in {"integer", "number"}:
            return schema.get("minimum", 0)
        if kind == "boolean":
            return False
        if kind == "null":
            return None
        return self.string(schema)

    @staticmethod
    def string(schema: dict[str, JsonValue]) -> str:
        """Produce format-aware deterministic string samples."""
        values = {
            "uuid": SchemaCases.UUID,
            "date": "2026-01-01",
            "date-time": "2026-01-01T00:00:00Z",
        }
        result = values.get(str(schema.get("format")), "fixture")
        minimum = schema.get("minLength", 0)
        maximum = schema.get("maxLength", len(result))
        if isinstance(minimum, int) and isinstance(maximum, int):
            return result.ljust(minimum, "x")[:maximum]
        return result

    def nodes(
        self, value: JsonValue, pointer: str
    ) -> list[tuple[str, dict[str, JsonValue]]]:
        """Walk every schema node with stable JSON-pointer identifiers."""
        result: list[tuple[str, dict[str, JsonValue]]] = []
        if isinstance(value, dict):
            if (
                isinstance(value.get("type"), (str, list))
                or isinstance(value.get("$ref"), str)
                or any(
                    isinstance(value.get(key), list)
                    for key in ("allOf", "anyOf", "oneOf", "enum")
                )
            ):
                result.append((pointer, value))
            for key, item in value.items():
                result.extend(self.nodes(item, pointer + "/" + key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                result.extend(self.nodes(item, pointer + "/" + str(index)))
        return result

    def probes(self) -> list[Probe]:
        """Build positive probes for each node, enum member, and nullable branch."""
        result: list[Probe] = []
        roots: dict[str, JsonValue] = {"components": self.schemas}
        for operation in self.contract.operations.values():
            roots[operation.identifier] = operation.definition
        for pointer, schema in self.nodes(roots, ""):
            result.append(Probe(pointer, schema, self.sample(schema)))
            enum = schema.get("enum")
            if isinstance(enum, list):
                result.extend(
                    Probe(pointer + "/enum/" + str(index), schema, item)
                    for index, item in enumerate(enum)
                )
            kind = schema.get("type")
            if schema.get("nullable") is True:
                result.append(Probe(pointer + "/legacy-nullable", schema, None))
            if (
                isinstance(kind, list)
                and "null" in kind
                and (not isinstance(enum, list) or None in enum)
            ):
                result.append(Probe(pointer + "/nullable", schema, None))
        return result
