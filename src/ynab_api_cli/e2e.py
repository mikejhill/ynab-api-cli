"""Run explicitly selected, fixture-based acceptance suites against real YNAB."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.e2e_client import CliSession, JournaledSession
from ynab_api_cli.e2e_fixtures import Fixtures
from ynab_api_cli.e2e_scenarios import Scenarios
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.security import FileSecurity
from ynab_api_cli.transport import Connection
from ynab_api_cli.types import JsonCodec, JsonValue

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class E2eOptions:
    """Explicit plan selection and persistent storage for write-enabled suites."""

    mode: str
    plan_id: str
    state_directory: Path
    enable_writes: bool = False
    request_limit: int = 180

    def __post_init__(self) -> None:
        """Reject implicit plans, unknown suites, and unapproved writes locally."""
        UUID(self.plan_id)
        if self.mode not in {"seed", "reads", "mutations"}:
            raise AppError("Select seed, reads, or mutations.")
        if self.mode != "reads" and not self.enable_writes:
            raise AppError("Seed and mutations require --enable-writes.")


class E2eRunner:
    """Gate writes by plan identity, private durable journals, and exclusive locks."""

    def __init__(self, options: E2eOptions, connection: Connection) -> None:
        if connection.plan_id != options.plan_id:
            raise AppError("Explicit E2E plan and connection must agree.")
        self.options = options
        self.connection = connection

    def run(self) -> dict[str, JsonValue]:
        """Lock local state and leave interrupted runs latched for reconciliation."""
        options = self.options
        options.state_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = options.state_directory / (options.plan_id + ".lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as err:
            raise AppError(
                "E2E state is locked; verify no run is active before recovery."
            ) from err
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
            FileSecurity().protect(lock)
            with tempfile.TemporaryDirectory(prefix="ynab-api-cli-e2e-") as temporary:
                return self._run(
                    CliSession(
                        Path(temporary),
                        self.connection,
                        request_limit=options.request_limit,
                    )
                )
        finally:
            lock.unlink(missing_ok=True)

    def _run(self, client: CliSession) -> dict[str, JsonValue]:
        """Verify baseline identity before seeding or running required scenarios."""
        store = ConfigStore(self.options.state_directory)
        journal = store.root / (self.options.plan_id + ".json")
        if journal.exists():
            FileSecurity().validate(journal)
        state = store.read(journal) if journal.exists() else {}
        if state.get("active_run") is not None or state.get("pending") is not None:
            raise AppError(
                "Unfinished E2E run; reconcile its private journal before continuing."
            )
        session = JournaledSession(
            client, store, journal, state, writes=self.options.enable_writes
        )
        plan = Contract.object(session.invoke("getPlanById")["plan"])
        if plan.get("id") != self.options.plan_id or not str(
            plan.get("name", "")
        ).startswith("YNAB API CLI TEST"):
            raise AppError(
                "E2E requires the exact explicit plan named YNAB API CLI TEST…. "
            )
        if self.options.mode != "reads":
            state["active_run"] = self.options.mode
            state["history"] = []
            store.write(journal, state, secret=True)
        fixtures = Fixtures(session)
        fixtures.discover(seed=self.options.mode == "seed")
        scenarios = Scenarios(fixtures)
        scenarios.reads()
        if self.options.mode == "mutations":
            scenarios.mutations()
        scenarios.remaining_reads()
        if self.options.mode != "reads":
            state.pop("active_run", None)
            state["fixture_version"] = "v1"
            store.write(journal, state, secret=True)
        return {
            "ok": True,
            "mode": self.options.mode,
            "fixture_version": "v1",
            "assertions": JsonCodec.encode(list(dict.fromkeys(scenarios.passed))),
            "completed_operations": JsonCodec.encode(sorted(client.completed)),
            "missing_operations": JsonCodec.encode(
                sorted(set(client.contract.operations) - client.completed)
            ),
            "request_count": client.count,
            "request_limit": client.limit,
            "complete_live_coverage": False,
            "gaps": [
                "Direct Import requires a linked test bank account "
                "and independently verified imports.",
                "Payee locations require a location-enabled test fixture.",
                "Account-wide user and plan-list reads are excluded.",
            ],
        }


class Application:
    """Expose local E2E suites without accepting credentials in arguments."""

    @classmethod
    def main(cls) -> None:
        """Report only sanitized status; keep journals and API output private."""
        parser = argparse.ArgumentParser(
            description="Explicit isolated-plan CLI E2E acceptance"
        )
        parser.add_argument("mode", choices=["seed", "reads", "mutations"])
        parser.add_argument("--plan-id", required=True)
        parser.add_argument("--auth-file", type=Path, required=True)
        parser.add_argument("--state-directory", type=Path, required=True)
        parser.add_argument("--enable-writes", action="store_true")
        parser.add_argument("--request-limit", type=int, default=180)
        args = parser.parse_args()
        logging.basicConfig(level=logging.WARNING)
        try:
            options = E2eOptions(
                str(args.mode),
                str(args.plan_id),
                Path(args.state_directory),
                bool(args.enable_writes),
                int(args.request_limit),
            )
            auth = Path(args.auth_file)
            FileSecurity().validate(auth)
            connection = ConfigStore.credentials(
                ConfigStore.read(auth), options.plan_id
            )
            report = E2eRunner(options, connection).run()
        except KeyboardInterrupt:
            raise SystemExit(130) from None
        except Exception:  # noqa: BLE001 - redact secrets and subprocess output at the process boundary.
            logger.error(  # noqa: TRY400 - omit secret-bearing tracebacks.
                "E2E failed; reconcile the private journal before repeating writes."
            )
            raise SystemExit(1) from None
        sys.stdout.write(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    Application.main()
