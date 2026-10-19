"""CLI orchestration with safe diagnostics and explicit mutation execution."""

from __future__ import annotations

import getpass
import io
import json
import logging
import shutil
import sys
from collections.abc import Callable, Sequence
from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from ynab_api_cli.cli import Command, CommandLine
from ynab_api_cli.compat import Compatibility
from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.generated.bindings import Bindings
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import JsonCodec, JsonValue, RequestValues

logger = logging.getLogger(__name__)


class Application:
    """Coordinate connection setup and reviewed typed operation dispatch."""

    def __init__(
        self, store: ConfigStore | None = None, transport: Transport | None = None
    ) -> None:
        self.contract = transport.contract if transport is not None else Contract()
        self.store = store
        self.transport = transport

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> None:
        """Run the console entry point and return its documented exit status."""
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.exit(cls().run(argv))

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Produce JSON output and omit traceback chains containing secrets."""
        try:
            command = CommandLine(self.contract).parse(argv)
            logging.basicConfig(
                level=command.log_level, format="%(levelname)s: %(message)s"
            )
            output = self.dispatch(command)
            sys.stdout.write(
                json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
            )
            if isinstance(output, dict) and output.get("compatible") is False:
                return 1
        except (AppError, OSError) as err:
            logger.error(  # noqa: TRY400 - never expose credential-bearing tracebacks.
                "%s",
                str(err)
                if isinstance(err, AppError)
                else "Filesystem operation failed.",
            )
            return 1
        except ValidationError:
            logger.error("Generated model validation failed; check compatibility.")  # noqa: TRY400 - omit request values.
            return 1
        except KeyboardInterrupt:
            return 130
        return 0

    def dispatch(self, command: Command) -> JsonValue:
        """Route non-network discovery and authenticated commands."""
        routes: dict[str, Callable[[Command], JsonValue]] = {
            "discover": self.discover,
            "inspect": self.inspect,
            "compat": self.compatibility,
            "skill": self.skill,
        }
        if command.name in routes:
            return routes[command.name](command)
        store = self.store if self.store is not None else ConfigStore()
        if command.name in {"configure", "select-plan"}:
            return self.configure(command, store)
        connection = store.load()
        transport = (
            self.transport
            if self.transport is not None
            else Transport(connection, self.contract)
        )
        if command.name == "doctor":
            return self.doctor(command, transport, store)
        return self.execute(command, transport)

    def execute(self, command: Command, transport: Transport) -> JsonValue:
        """Validate and preview or submit one reviewed operation."""
        connection = transport.connection
        operation = self.contract.get(command.operation or "")
        request = self.request(command)
        path = dict(request.path)
        if (
            "{plan_id}" in operation.path
            and "plan_id" not in path
            and connection.plan_id is not None
        ):
            path["plan_id"] = connection.plan_id
        request = RequestValues(path, request.query, request.body)
        self.contract.validate_request(operation, request)
        if operation.write and not command.execute:
            return {
                "preview": True,
                "operation": operation.identifier,
                "method": operation.method,
                "path": operation.path,
                "request": request.json(),
            }
        response = Bindings.operations[operation.alias](transport, request)
        if command.metadata:
            return {
                "status": response.status,
                "headers": JsonCodec.encode(response.headers),
                "contract_version": self.contract.version,
                "request_count": transport.request_count,
                "pat_index": transport.active_token_index,
                "body": response.raw,
            }
        return response.raw

    def discover(self, command: Command) -> JsonValue:
        """List the reviewed contract groups and matching operations."""
        groups = {op.group for op in self.contract.operations.values()}
        if command.group is not None and command.group not in groups:
            raise AppError("Unknown resource group.")
        return JsonCodec.encode(
            {
                "contract_version": self.contract.version,
                "groups": sorted(groups),
                "operations": [
                    op.identifier
                    for op in self.contract.operations.values()
                    if op.identifier in self.contract.catalog
                    and (command.group is None or op.group == command.group)
                ],
            }
        )

    def inspect(self, command: Command) -> JsonValue:
        """Return the operation and only its reachable schemas."""
        operation = self.contract.get(command.operation or "")
        return {
            "operation": operation.identifier,
            "method": operation.method,
            "path": operation.path,
            "write": operation.write,
            "definition": operation.definition,
            "components": self.reachable(operation.definition),
        }

    def compatibility(self, _command: Command) -> JsonValue:
        """Check the public upstream definition without credentials."""
        checker = Compatibility(self.contract)
        return checker.compare(checker.fetch())

    @staticmethod
    def configure(command: Command, store: ConfigStore) -> JsonValue:
        """Perform only the explicitly selected local configuration action."""
        if command.name == "select-plan":
            store.select_plan(command.plan or "")
            return {"plan_id": command.plan}
        if not sys.stdin.isatty():
            raise AppError("Run configure in an interactive terminal for hidden input.")
        store.configure(
            getpass.getpass("YNAB personal access token (hidden): "),
            replace=command.replace,
            add=command.add,
        )
        return {"configured": True, "directory": str(store.root)}

    def doctor(
        self, command: Command, transport: Transport, store: ConfigStore
    ) -> dict[str, JsonValue]:
        """Validate API access separately from offline configuration checks."""
        if not command.offline:
            for token in transport.connection.tokens:
                probe = Transport(
                    Connection(token, transport.connection.plan_id),
                    self.contract,
                    transport.client,
                )
                Bindings.operations["get_user"](probe, RequestValues())
                if transport.connection.plan_id is not None:
                    Bindings.operations["get_plan_by_id"](
                        probe, RequestValues({"plan_id": transport.connection.plan_id})
                    )
        output: dict[str, JsonValue] = {
            "ok": True,
            "pat_count": len(transport.connection.tokens),
            "api_checked": not command.offline,
            "directory": str(store.root),
            "plan_id": transport.connection.plan_id,
            "contract_version": self.contract.version,
        }
        if command.upstream:
            checker = Compatibility(self.contract)
            report = checker.compare(checker.fetch())
            output["upstream"] = report
            output["compatible"] = report["compatible"]
        return output

    def request(self, command: Command) -> RequestValues:
        """Read the uniform envelope or a resource command's body."""
        if command.source is None:
            return command.arguments
        text = command.source
        if text.startswith("@"):
            text = Path(text[1:]).read_text(encoding="utf-8")
        elif text == "-":
            text = sys.stdin.read()
        try:
            raw = JsonCodec.loads(text)
        except ValueError as err:
            raise AppError("Invalid request JSON.") from err
        if command.name != "call":
            return RequestValues(command.arguments.path, command.arguments.query, raw)
        envelope = self.contract.object(raw)
        if set(envelope) - {"path", "query", "body"}:
            raise AppError("Request accepts only path, query, and body fields.")
        base = RequestValues(
            dict(self.contract.object(envelope.get("path", {}))),
            dict(self.contract.object(envelope.get("query", {}))),
        )
        return (
            RequestValues(base.path, base.query, envelope["body"])
            if "body" in envelope
            else base
        )

    def reachable(self, definition: JsonValue) -> dict[str, JsonValue]:
        """Disclose only schemas reachable from the inspected operation."""
        selected: dict[str, JsonValue] = {}
        pending = [definition]
        schemas = self.contract.object(
            self.contract.object(self.contract.document["components"])["schemas"]
        )
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                reference = value.get("$ref")
                if isinstance(reference, str) and reference.startswith(
                    "#/components/schemas/"
                ):
                    name = reference.rsplit("/", 1)[-1]
                    if name not in selected:
                        selected[name] = schemas[name]
                        pending.append(schemas[name])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        return selected

    @staticmethod
    def skill(command: Command) -> JsonValue:
        """Display or export the skill supplied by the installed distribution."""
        resource = files("ynab_api_cli.resources").joinpath("skill")
        if command.operation == "show":
            return {"skill": resource.joinpath("SKILL.md").read_text(encoding="utf-8")}
        if command.source is None:
            raise AppError("skill export requires a destination directory.")
        destination = Path(command.source)
        if destination.exists():
            raise AppError("Skill export destination already exists.")
        shutil.copytree(str(resource), destination)
        return {"exported": str(destination)}


if __name__ == "__main__":
    Application.main()
