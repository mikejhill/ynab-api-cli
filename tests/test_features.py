"""Reviewed feature accounting and negative schema constraint probes."""

from __future__ import annotations

import copy
import json
from importlib.resources import files

import pytest
from pydantic import BaseModel, ValidationError

from ynab_api_cli.contract import Contract
from ynab_api_cli.contract_testing import SchemaCases
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.generated import models
from ynab_api_cli.types import JsonCodec, JsonValue
from ynab_api_cli.verification import Verification


class TestFeatures:
    """Every feature needs a reviewed identifier and exercised validation behavior."""

    def test_reviewed_manifest(self) -> None:
        """Changing or adding a schema feature requires a reviewed manifest update."""
        reviewed = json.loads(
            files("ynab_api_cli.resources")
            .joinpath("schema_features.json")
            .read_text(encoding="utf-8")
        )
        assert reviewed == Verification.manifest()

    def test_typed_maps_and_nonfinite_numbers(self) -> None:
        """Typed map values and strict JSON numbers reject invalid input."""
        with pytest.raises(ValidationError):
            models.LoanAccountPeriodicValueType0.model_validate(
                {"2026-01-01": "not-an-integer"}
            )
        for text in ("NaN", "Infinity", "-Infinity"):
            with pytest.raises(ValueError, match="Non-finite"):
                JsonCodec.loads(text)
        with pytest.raises(ValueError, match="Non-finite"):
            JsonCodec.encode(float("nan"))

    def test_generated_properties(self, contract: Contract) -> None:
        """Named object schemas retain typed properties and required fields."""
        cases = SchemaCases(contract)
        aliases = {
            "CurrencyFormat": "CurrencyFormatType0",
            "DateFormat": "DateFormatType0",
            "LoanAccountPeriodicValue": "LoanAccountPeriodicValueType0",
        }
        for name, definition in cases.schemas.items():
            schema = contract.object(definition)
            sample = cases.sample(schema)
            if not isinstance(sample, dict):
                continue
            model = getattr(models, aliases.get(name, name), None)
            assert isinstance(model, type), name
            assert issubclass(model, BaseModel), name
            fields = {
                info.alias or key: info for key, info in model.model_fields.items()
            }
            properties, required = self.object_fields(contract, schema)
            assert properties <= set(fields), name
            assert all(fields[key].is_required() for key in required), name
            parsed = model.model_validate(sample)
            assert parsed is not None

    def object_fields(
        self, contract: Contract, schema: dict[str, JsonValue]
    ) -> tuple[set[str], set[str]]:
        """Resolve property declarations through references and composed schemas."""
        reference = schema.get("$ref")
        if isinstance(reference, str):
            schemas = contract.object(
                contract.object(contract.document["components"])["schemas"]
            )
            return self.object_fields(
                contract, contract.object(schemas[reference.rsplit("/", 1)[-1]])
            )
        properties = set(contract.object(schema.get("properties", {})))
        required = schema.get("required", [])
        names: set[str] = (
            {str(item) for item in required} if isinstance(required, list) else set()
        )
        for key in ("allOf", "anyOf", "oneOf"):
            branches = schema.get(key)
            if isinstance(branches, list):
                for branch in branches:
                    fields, mandatory = self.object_fields(
                        contract, contract.object(branch)
                    )
                    properties.update(fields)
                    names.update(mandatory)
        return properties, names

    def test_negative_constraints(self, contract: Contract) -> None:
        """Declared schema constraints reject invalid witnesses."""
        for probe in SchemaCases(contract).probes():
            schema = probe.schema
            enum = schema.get("enum")
            if isinstance(enum, list):
                self.reject(contract, schema, {"invalid_enum": True})
            kind = schema.get("type")
            if isinstance(kind, str):
                invalid: JsonValue = (
                    [] if kind == "object" else {} if kind != "null" else "invalid"
                )
                self.reject(contract, schema, invalid)
            required = schema.get("required")
            if isinstance(required, list) and isinstance(probe.value, dict):
                for name in required:
                    invalid_object = copy.deepcopy(probe.value)
                    invalid_object.pop(str(name), None)
                    self.reject(contract, schema, invalid_object)
            if schema.get("format") in {"uuid", "date", "date-time"}:
                self.reject(contract, schema, "invalid-format")
            maximum = schema.get("maxLength")
            if isinstance(maximum, int):
                self.reject(contract, schema, "x" * (maximum + 1))
            minimum = schema.get("minimum")
            if isinstance(minimum, (int, float)):
                self.reject(contract, schema, minimum - 1)

    @staticmethod
    def reject(
        contract: Contract, schema: dict[str, JsonValue], value: JsonValue
    ) -> None:
        """Assert a malformed witness cannot satisfy its original schema."""
        with pytest.raises(AppError):
            contract.validate(schema, value, "negative witness")
