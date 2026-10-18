"""Load the reviewed OpenAPI contract and validate runtime JSON."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonCodec, JsonValue, RequestValues


@dataclass(frozen=True, slots=True)
class Operation:
    """Reviewed operation identity and its wire contract."""

    identifier: str
    alias: str
    group: str
    method: str
    path: str
    definition: dict[str, JsonValue]

    @property
    def write(self) -> bool:
        """Classify mutations by the HTTP method."""
        return self.method not in {"GET", "HEAD", "OPTIONS"}


class Contract:
    """Single source for operation metadata and JSON Schema validation."""

    def __init__(self, document: dict[str, JsonValue] | None = None) -> None:
        resource = files("ynab_api_cli.resources")
        loaded = (
            JsonCodec.encode(
                yaml.safe_load(
                    resource.joinpath("openapi.yaml").read_text(encoding="utf-8")
                )
            )
            if document is None
            else document
        )
        self.document = self.object(loaded)
        self.normalized_components = self.normalize(self.document["components"])
        self.version = str(self.object(self.document["info"])["version"])
        self.operations = self.inventory()
        self.catalog = self.object(
            JsonCodec.loads(
                resource.joinpath("catalog.json").read_text(encoding="utf-8")
            )
        )

    @staticmethod
    def object(value: JsonValue) -> dict[str, JsonValue]:
        """Require a JSON object without leaking its contents in errors."""
        if not isinstance(value, dict):
            raise AppError("Expected a JSON object.")
        return value

    @staticmethod
    def snake(value: str) -> str:
        """Convert a contract operation ID into a Python-compatible name."""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()

    def inventory(self) -> dict[str, Operation]:
        """Enumerate HTTP operations directly from the specification."""
        result: dict[str, Operation] = {}
        for path, raw in self.object(self.document["paths"]).items():
            for method, entry in self.object(raw).items():
                if method not in {
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                }:
                    continue
                definition = self.object(entry)
                identifier = str(definition["operationId"])
                tags = definition["tags"]
                if not isinstance(tags, list) or not tags:
                    raise AppError("Operation has no resource tag.")
                result[identifier] = Operation(
                    identifier,
                    self.snake(identifier),
                    str(tags[0]).lower().replace(" ", "-"),
                    method.upper(),
                    path,
                    definition,
                )
        return result

    def get(self, name: str) -> Operation:
        """Resolve only operations explicitly admitted by the reviewed catalog."""
        for operation in self.operations.values():
            if (
                name in {operation.identifier, operation.alias}
                and operation.identifier in self.catalog
            ):
                return operation
        raise AppError("Unknown or unreviewed operation; run discover.")

    def parameters(self, operation: Operation) -> list[dict[str, JsonValue]]:
        """Return declared endpoint parameters."""
        values = operation.definition.get("parameters", [])
        if not isinstance(values, list):
            raise AppError("Invalid parameter definition.")
        return [self.object(item) for item in values]

    def validate(
        self, schema: dict[str, JsonValue], value: JsonValue, label: str
    ) -> None:
        """Validate constraints and formats without quoting personal values."""
        complete = self.object(self.normalize(schema))
        complete["components"] = self.normalized_components
        errors = list(
            Draft202012Validator(complete, format_checker=FormatChecker()).iter_errors(
                value
            )
        )
        if errors:
            location = "/".join(str(part) for part in errors[0].absolute_path) or "root"
            raise AppError(
                f"Invalid {label} at {location}: {errors[0].validator} constraint."
            )

    @classmethod
    def normalize(cls, value: JsonValue) -> JsonValue:
        """Honor legacy nullable annotations in the published 3.1 document."""
        if isinstance(value, list):
            return [cls.normalize(item) for item in value]
        if isinstance(value, dict):
            result: dict[str, JsonValue] = {
                key: cls.normalize(item)
                for key, item in value.items()
                if key != "nullable"
            }
            if value.get("nullable") is True:
                return {"anyOf": [result, {"type": "null"}]}
            return result
        return value

    def validate_request(self, operation: Operation, request: RequestValues) -> None:
        """Validate path, query, body presence, and documented semantic rules."""
        values = request.json()
        for section in ("path", "query"):
            parameters = [
                item for item in self.parameters(operation) if item["in"] == section
            ]
            schema: dict[str, JsonValue] = {
                "type": "object",
                "properties": {
                    str(item["name"]): item["schema"] for item in parameters
                },
                "required": [
                    str(item["name"])
                    for item in parameters
                    if item.get("required") is True
                ],
                "additionalProperties": False,
            }
            self.validate(schema, values[section], section)
        body = operation.definition.get("requestBody")
        if body is None:
            if "body" in values:
                raise AppError("This operation does not accept a request body.")
            return
        definition = self.object(body)
        if "body" not in values:
            if definition.get("required") is True:
                raise AppError("This operation requires a request body.")
            return
        content = self.object(self.object(definition["content"])["application/json"])
        self.validate(self.object(content["schema"]), values["body"], "body")
        if operation.identifier == "createTransaction":
            payload = self.object(values["body"])
            if ("transaction" in payload) == ("transactions" in payload):
                raise AppError("Provide exactly one of transaction or transactions.")

    def validate_response(
        self, operation: Operation, status: int, raw: JsonValue
    ) -> None:
        """Validate the actual success response against its declared schema."""
        response = self.object(operation.definition["responses"]).get(str(status))
        if response is None:
            raise AppError(
                f"Unexpected HTTP {status}; bundled API contract {self.version}."
            )
        content = self.object(self.object(response)["content"])
        schema = self.object(self.object(content["application/json"])["schema"])
        self.validate(schema, raw, "response")
