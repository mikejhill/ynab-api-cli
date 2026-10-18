"""Compare bundled and upstream contracts without modifying installed files."""

from __future__ import annotations

import hashlib
import json

import httpx
import yaml

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonCodec, JsonValue


class Compatibility:
    """Detect additions, removals, and structural contract changes."""

    URL = "https://api.ynab.com/papi/open_api_spec.yaml"
    DOCUMENTATION_KEYS = frozenset(
        {"description", "summary", "example", "examples", "externalDocs"}
    )

    def __init__(self, contract: Contract | None = None) -> None:
        self.contract = contract if contract is not None else Contract()

    @classmethod
    def structural(cls, value: JsonValue) -> JsonValue:
        """Strip documentation while retaining API validation and wire semantics."""
        if isinstance(value, dict):
            return {
                key: cls.structural(item)
                for key, item in value.items()
                if key not in cls.DOCUMENTATION_KEYS
            }
        if isinstance(value, list):
            return [cls.structural(item) for item in value]
        return value

    def compare(self, latest: dict[str, JsonValue]) -> dict[str, JsonValue]:
        """Report semantic paths and operation changes, including optional additions."""
        upstream = Contract(latest)
        baseline = self.contract.operations
        added = sorted(set(upstream.operations) - set(baseline))
        removed = sorted(set(baseline) - set(upstream.operations))
        changed = [
            name
            for name in sorted(set(baseline) & set(upstream.operations))
            if self.structural(baseline[name].definition)
            != self.structural(upstream.operations[name].definition)
            or baseline[name].path != upstream.operations[name].path
            or baseline[name].method != upstream.operations[name].method
        ]
        schema_changes = self.differences(
            self.structural(self.contract.document["components"]),
            self.structural(latest["components"]),
            "/components",
        )
        server_changes = self.contract.document.get("servers") != latest.get("servers")
        compatible = not (
            added or removed or changed or schema_changes or server_changes
        )
        affected = sorted(
            set(changed)
            | set(removed)
            | (set(baseline) if schema_changes or server_changes else set())
        )
        output: dict[str, JsonValue] = {
            "compatible": compatible,
            "baseline_version": self.contract.version,
            "upstream_version": upstream.version,
            "added": JsonCodec.encode(added),
            "removed": JsonCodec.encode(removed),
            "changed": JsonCodec.encode(changed),
            "schema_changes": JsonCodec.encode(schema_changes),
            "server_changed": server_changes,
            "affected_commands": JsonCodec.encode(affected),
            "missing_tests": JsonCodec.encode(added),
            "documentation_only": compatible and self.contract.document != latest,
        }
        return output

    @classmethod
    def differences(cls, old: JsonValue, new: JsonValue, path: str) -> list[str]:
        """Find changed schema paths without relying on version strings."""
        if isinstance(old, dict) and isinstance(new, dict):
            result: list[str] = []
            for key in sorted(set(old) | set(new)):
                pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
                result.extend(
                    [pointer]
                    if key not in old or key not in new
                    else cls.differences(old[key], new[key], pointer)
                )
            return result
        return [] if old == new else [path]

    def fetch(self, client: httpx.Client | None = None) -> dict[str, JsonValue]:
        """Fetch the official YAML using bounded credential-free HTTPS."""
        try:
            if client is None:
                with httpx.Client(
                    verify=True, follow_redirects=False, timeout=30, trust_env=False
                ) as session:
                    response = session.get(self.URL)
            else:
                response = client.get(self.URL, timeout=30, follow_redirects=False)
            response.raise_for_status()
            return Contract.object(JsonCodec.encode(yaml.safe_load(response.text)))
        except (httpx.HTTPError, yaml.YAMLError, ValueError) as err:
            raise AppError(
                "Cannot fetch or parse the public upstream contract."
            ) from err

    @staticmethod
    def digest(value: dict[str, JsonValue]) -> str:
        """Hash a canonical contract document for provenance checks."""
        return hashlib.sha256(
            json.dumps(value, sort_keys=True).encode("utf-8")
        ).hexdigest()
