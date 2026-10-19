"""Exercise the installed CLI in isolated subprocesses with bounded traffic."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.transport import Connection
from ynab_api_cli.types import UNSET, JsonCodec, JsonValue, RequestValues


class CliSession:
    """Keep credentials out of argv, child environments, and diagnostic output."""

    def __init__(
        self, root: Path, connection: Connection, *, request_limit: int = 180
    ) -> None:
        if request_limit < len(connection.tokens):
            raise AppError("Request budget must cover one attempt per configured PAT.")
        self.connection = connection
        self.contract = Contract()
        self.root = root
        self.count = 0
        self.limit = request_limit
        self.completed: set[str] = set()
        store = ConfigStore(root / "config/ynab-api-cli")
        self.store = store
        store.write(
            store.root / "auth.json",
            {"access_tokens": list(connection.tokens)},
            secret=True,
        )
        store.select_plan(connection.plan_id or "")
        allowed = {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "HOME",
            "USERPROFILE",
            "LOCALAPPDATA",
            "LANG",
        }
        self.environment = {
            key: value for key, value in os.environ.items() if key.upper() in allowed
        }
        self.environment.update(
            {
                "XDG_CONFIG_HOME": str(store.root.parent),
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
        )

    def command(
        self, arguments: list[str], *, payload: JsonValue = None, network: bool = True
    ) -> dict[str, JsonValue]:
        """Capture private process output and export only validated JSON results."""
        reservation = len(self.connection.tokens) if network else 0
        if self.count + reservation > self.limit:
            raise AppError("E2E request budget exhausted before CLI execution.")
        # Reserve worst-case traffic even if the subprocess fails without a report.
        self.count += reservation
        try:
            result = subprocess.run(  # noqa: S603 - fixed Python module, no shell or credential arguments.
                [sys.executable, "-m", "ynab_api_cli", *arguments],
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                check=False,
                timeout=35 * len(self.connection.tokens) + 10,
                cwd=self.root,
                env=self.environment,
            )
        except (OSError, subprocess.TimeoutExpired) as err:
            raise AppError(
                "E2E CLI process failed; reconcile any journaled write."
            ) from err
        if result.returncode != 0 or result.stderr.strip():
            raise AppError("E2E CLI failed; private response details withheld.")
        try:
            output = Contract.object(JsonCodec.loads(result.stdout))
        except ValueError as err:
            raise AppError("E2E CLI returned invalid JSON.") from err
        if network:
            attempts = output.get("request_count")
            if (
                not isinstance(attempts, int)
                or isinstance(attempts, bool)
                or not 1 <= attempts <= reservation
            ):
                raise AppError("E2E CLI did not report a valid request count.")
            self.count += attempts - reservation
            index = output.get("pat_index")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or not 0 <= index < len(self.connection.tokens)
            ):
                raise AppError("E2E CLI did not report a valid PAT position.")
            if index:
                tokens = self.connection.tokens[index:] + self.connection.tokens[:index]
                self.connection = Connection(
                    tokens[0], self.connection.plan_id, tokens[1:]
                )
                self.store.write(
                    self.store.root / "auth.json",
                    {"access_tokens": list(tokens)},
                    secret=True,
                )
        return output

    def invoke(
        self, operation: str, request: RequestValues, *, preview: bool = False
    ) -> dict[str, JsonValue]:
        """Submit the public uniform interface using stdin for request bodies."""
        definition = self.contract.get(operation)
        self.contract.validate_request(definition, request)
        arguments = ["call", operation, "--request", "-", "--metadata"]
        if definition.write and not preview:
            arguments.append("--execute")
        output = self.command(arguments, payload=request.json(), network=not preview)
        if preview:
            if (
                output.get("preview") is not True
                or output.get("request") != request.json()
            ):
                raise AppError("CLI preview did not preserve the exact request.")
            return output
        status = output.get("status")
        if not isinstance(status, int):
            raise AppError("CLI metadata omitted the HTTP status.")
        raw = output.get("body")
        self.contract.validate_response(definition, status, raw)
        self.completed.add(operation)
        return Contract.object(Contract.object(raw)["data"])

    def accounts(self, *, explicit: bool) -> dict[str, JsonValue]:
        """Exercise endpoint flags and the configured default plan separately."""
        arguments = ["accounts", "get-accounts", "--metadata"]
        if explicit:
            arguments.extend(["--plan", self.connection.plan_id or ""])
            self.store.select_plan(str(UUID(int=0)))
        try:
            output = self.command(arguments)
        finally:
            if explicit:
                self.store.select_plan(self.connection.plan_id or "")
        return Contract.object(Contract.object(output.get("body"))["data"])


class JournaledSession:
    """Persist each intent before execution and block ambiguous mutation outcomes."""

    def __init__(
        self,
        client: CliSession,
        store: ConfigStore,
        path: Path,
        state: dict[str, JsonValue],
        *,
        writes: bool,
    ) -> None:
        self.client = client
        self.store = store
        self.path = path
        self.state = state
        self.writes = writes

    def invoke(
        self,
        operation: str,
        *,
        path: Mapping[str, object] | None = None,
        query: Mapping[str, object] | None = None,
        body: object = UNSET,
    ) -> dict[str, JsonValue]:
        """Constrain every request to the explicit test plan and journal mutations."""
        values: dict[str, object] = {"plan_id": self.client.connection.plan_id}
        values.update(path or {})
        if values["plan_id"] != self.client.connection.plan_id:
            raise AppError("E2E requests cannot leave the designated test plan.")
        definition = self.client.contract.get(operation)
        request = RequestValues(values, query or {}, body)
        if definition.write:
            if not self.writes or self.state.get("pending") is not None:
                raise AppError("E2E write disabled or unresolved intent exists.")
            self.client.invoke(operation, request, preview=True)
            self.state["pending"] = {"operation": operation, "request": request.json()}
            self.store.write(self.path, self.state, secret=True)
        result = self.client.invoke(operation, request)
        if definition.write:
            receipt: dict[str, JsonValue] = {
                "operation": operation,
                "request": request.json(),
                "data": result,
            }
            history = self.state.get("history", [])
            if not isinstance(history, list):
                raise AppError("Invalid private E2E journal history.")
            self.state["history"] = [*history, receipt]
            self.state["last_receipt"] = receipt
            self.state.pop("pending", None)
            self.store.write(self.path, self.state, secret=True)
        return result
