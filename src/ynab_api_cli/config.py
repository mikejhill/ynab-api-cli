"""Atomic connection configuration in XDG-style directories."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import UUID

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.security import FileSecurity
from ynab_api_cli.transport import Connection
from ynab_api_cli.types import JsonCodec, JsonValue


class ConfigStore:
    """Keep credentials separate from non-secret default settings."""

    def __init__(
        self, root: Path | None = None, security: FileSecurity | None = None
    ) -> None:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        if root is None and not base.is_absolute():
            raise AppError("XDG_CONFIG_HOME must be absolute.")
        self.root = root if root is not None else base / "ynab-api-cli"
        self.security = security if security is not None else FileSecurity()

    @staticmethod
    def read(path: Path) -> dict[str, JsonValue]:
        """Read a JSON object without reporting credential file contents."""
        try:
            return Contract.object(JsonCodec.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as err:
            raise AppError(f"Cannot read JSON configuration: {path.name}.") from err

    def write(
        self,
        path: Path,
        values: dict[str, JsonValue],
        *,
        secret: bool = False,
        exclusive: bool = False,
    ) -> None:
        """Replace a JSON file atomically after securing its temporary file."""
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary = tempfile.mkstemp(dir=self.root, prefix=".ynab-api-cli-")
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                if secret:
                    self.security.protect(temporary_path)
                stream.write(json.dumps(values, indent=2) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            if exclusive:
                os.link(temporary_path, path)
            else:
                temporary_path.replace(path)
        except OSError as err:
            raise AppError("Cannot write configuration atomically.") from err
        finally:
            temporary_path.unlink(missing_ok=True)

    def configure(
        self, token: str, *, replace: bool = False, add: bool = False
    ) -> None:
        """Create, append, or explicitly replace protected credentials."""
        if not token.strip() or any(character.isspace() for character in token.strip()):
            raise AppError("Token must be nonempty and contain no whitespace.")
        Connection(token.strip())
        path = self.root / "auth.json"
        if replace and add:
            raise AppError("Choose either --add or --replace.")
        if path.exists() and not (replace or add):
            raise AppError(
                "Credentials already exist; use configure --add or --replace to rotate."
            )
        previous = self.read(path) if path.exists() else {}
        tokens = (
            (*self.credentials(previous).tokens, token.strip())
            if add and path.exists()
            else (token.strip(),)
        )
        connection = Connection(tokens[0], additional_tokens=tokens[1:])
        previous.pop("access_token", None)
        previous["access_tokens"] = list(connection.tokens)
        self.write(path, previous, secret=True, exclusive=not (replace or add))

    @staticmethod
    def credentials(
        values: dict[str, JsonValue], plan: str | None = None
    ) -> Connection:
        """Decode legacy single credentials or the ordered multi-PAT format."""
        if "access_tokens" in values and "access_token" in values:
            raise AppError("Use access_tokens or legacy access_token, not both.")
        raw = values.get("access_tokens", [values.get("access_token")])
        if (
            not isinstance(raw, list)
            or not raw
            or any(not isinstance(item, str) for item in raw)
        ):
            raise AppError(
                "auth.json requires a nonempty access_tokens list or access_token."
            )
        tokens = tuple(str(item) for item in raw)
        return Connection(tokens[0], plan, tokens[1:])

    def load(self) -> Connection:
        """Validate permissions, credentials, and optional default plan."""
        path = self.root / "auth.json"
        if not path.is_file():
            raise AppError("Missing auth.json; run configure in a local terminal.")
        self.security.validate(path)
        credentials = self.read(path)
        config = self.root / "config.json"
        plan = self.read(config).get("plan_id") if config.exists() else None
        if plan is not None and (not isinstance(plan, str) or not plan):
            raise AppError("config.json plan_id must be a nonempty string.")
        return self.credentials(credentials, plan)

    def select_plan(self, plan: str) -> None:
        """Store an explicit UUID without overwriting unrelated settings."""
        try:
            UUID(plan)
        except ValueError as err:
            raise AppError("Select an explicit plan UUID.") from err
        path = self.root / "config.json"
        values = self.read(path) if path.exists() else {}
        values["plan_id"] = plan
        self.write(path, values)
