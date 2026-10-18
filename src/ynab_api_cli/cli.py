"""Contract-derived argument parsing into immutable command settings."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from ynab_api_cli.contract import Contract
from ynab_api_cli.types import RequestValues


@dataclass(frozen=True, slots=True)
class Command:
    """Typed command input separated from argparse's dynamic namespace."""

    name: str
    operation: str | None
    group: str | None
    plan: str | None
    source: str | None
    arguments: RequestValues
    execute: bool
    metadata: bool
    offline: bool
    upstream: bool
    replace: bool
    log_level: str


class CommandLine:
    """Expose every reviewed endpoint with useful resource-specific flags."""

    def __init__(self, contract: Contract) -> None:
        self.contract = contract

    def parser(self) -> argparse.ArgumentParser:
        """Build connection, discovery, uniform, and resource subcommands."""
        parser = argparse.ArgumentParser(
            prog="ynab-api-cli", description="Complete reviewed YNAB REST API CLI"
        )
        parser.add_argument(
            "--log-level", choices=["ERROR", "WARNING", "INFO"], default="WARNING"
        )
        sub = parser.add_subparsers(dest="command", required=True)
        configure = sub.add_parser(
            "configure", help="Prompt locally for protected credentials"
        )
        configure.add_argument("--replace", action="store_true")
        doctor = sub.add_parser(
            "doctor", help="Validate local settings and read-only API access"
        )
        doctor.add_argument("--offline", action="store_true")
        doctor.add_argument("--upstream", action="store_true")
        select = sub.add_parser("select-plan")
        select.add_argument("plan")
        discover = sub.add_parser("discover")
        discover.add_argument("group", nargs="?")
        describe = sub.add_parser("inspect")
        describe.add_argument("operation")
        call = sub.add_parser("call")
        call.add_argument("operation")
        call.add_argument(
            "--request",
            dest="source",
            default="{}",
            help="JSON envelope, @file, or - for stdin",
        )
        self.execution_flags(call)
        compat = sub.add_parser("compat")
        compat.add_argument("action", choices=["check"])
        skill = sub.add_parser(
            "skill", help="Inspect or export the bundled supplementary skill"
        )
        skill.add_argument("action", choices=["show", "export"])
        skill.add_argument("destination", nargs="?")
        groups = {
            group: sub.add_parser(group).add_subparsers(dest="operation", required=True)
            for group in sorted(
                {
                    op.group
                    for op in self.contract.operations.values()
                    if op.identifier in self.contract.catalog
                }
            )
        }
        for operation in self.contract.operations.values():
            if operation.identifier not in self.contract.catalog:
                continue
            endpoint = groups[operation.group].add_parser(
                operation.alias.replace("_", "-"),
                help=str(operation.definition.get("summary", "")),
            )
            endpoint.set_defaults(operation=operation.identifier)
            for parameter in self.contract.parameters(operation):
                endpoint.add_argument(
                    "--" + str(parameter["name"]).replace("_", "-"),
                    dest="argument_" + str(parameter["name"]),
                    required=bool(parameter.get("required"))
                    and parameter["name"] != "plan_id",
                    help=str(parameter.get("description", "")),
                )
            if operation.definition.get("requestBody") is not None:
                endpoint.add_argument(
                    "--body",
                    dest="source",
                    required=True,
                    help="JSON object, @file, or - for stdin",
                )
            self.execution_flags(endpoint)
        return parser

    @staticmethod
    def execution_flags(parser: argparse.ArgumentParser) -> None:
        """Add mutation guards and optional HTTP metadata."""
        parser.add_argument(
            "--execute", action="store_true", help="Submit an authorized mutation"
        )
        parser.add_argument("--metadata", action="store_true")

    def parse(self, argv: Sequence[str] | None = None) -> Command:
        """Convert the namespace and endpoint flags into immutable settings."""
        parser = self.parser()
        args = parser.parse_args(argv)
        name = str(args.command)
        operation = getattr(args, "operation", None)
        path: dict[str, object] = {}
        query: dict[str, object] = {}
        if operation is not None and name not in {"inspect", "call"}:
            for parameter in self.contract.parameters(self.contract.get(operation)):
                raw = getattr(args, "argument_" + str(parameter["name"]), None)
                if raw is not None:
                    schema = self.contract.object(parameter["schema"])
                    value = self.convert(
                        str(raw), str(schema.get("type", "string")), parser
                    )
                    (path if parameter["in"] == "path" else query)[
                        str(parameter["name"])
                    ] = value
        source = getattr(args, "source", None)
        if name == "skill":
            operation = str(args.action)
            source = getattr(args, "destination", None)
        return Command(
            name,
            operation,
            getattr(args, "group", None),
            getattr(args, "plan", None),
            source,
            RequestValues(path, query),
            bool(getattr(args, "execute", False)),
            bool(getattr(args, "metadata", False)),
            bool(getattr(args, "offline", False)),
            bool(getattr(args, "upstream", False)),
            bool(getattr(args, "replace", False)),
            str(args.log_level),
        )

    @staticmethod
    def convert(text: str, kind: str, parser: argparse.ArgumentParser) -> object:
        """Decode CLI primitive types without treating false as truthy."""
        if kind == "boolean":
            if text not in {"true", "false"}:
                parser.error("Boolean values must be true or false.")
            return text == "true"
        if kind == "integer":
            try:
                return int(text)
            except ValueError:
                parser.error("Integer argument required.")
        return text
