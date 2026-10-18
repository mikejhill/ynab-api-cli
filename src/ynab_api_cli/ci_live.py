"""Run read-only CI probes with temporary credentials and sanitized output."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from uuid import UUID

import httpx

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.live import LiveOptions, LiveRunner
from ynab_api_cli.transport import Connection, Transport
from ynab_api_cli.types import JsonValue

logger = logging.getLogger(__name__)


class Application:
    """Consume CI secrets once and expose only operation-level test results."""

    @classmethod
    def main(cls, client: httpx.Client | None = None) -> None:
        """Run the probe without emitting exception details or API payloads."""
        logging.basicConfig(level=logging.WARNING)
        try:
            report = cls.run(os.environ, client)
        except KeyboardInterrupt:
            raise SystemExit(130) from None
        except Exception:  # noqa: BLE001 - redact unexpected failures at the process boundary.
            logger.error(  # noqa: TRY400 - tracebacks may expose credentials.
                "Live CI probe failed; no response or credential details logged."
            )
            raise SystemExit(1) from None
        sys.stdout.write(json.dumps(report, indent=2) + "\n")

    @staticmethod
    def run(
        environment: MutableMapping[str, str], client: httpx.Client | None = None
    ) -> dict[str, JsonValue]:
        """Use explicit environment secrets and remove private files on all exits."""
        token = environment.pop("YNAB_ACCESS_TOKEN", "")
        plan = environment.pop("YNAB_TEST_PLAN_ID", "")
        connection = Connection(token, str(UUID(plan)))
        with tempfile.TemporaryDirectory(prefix="ynab-api-cli-live-") as temporary:
            root = Path(temporary)
            store = ConfigStore(root / "config")
            store.configure(connection.token)
            options = LiveOptions(
                plan_id=connection.plan_id or "",
                auth_file=store.root / "auth.json",
                state_directory=root / "state",
                enable_writes=False,
                account_reads=False,
            )
            runner = LiveRunner(options, Transport(connection, client=client))
            result = runner.run()
        return {
            "ok": True,
            "mode": "read-only",
            "completed_operations": result["completed_operations"],
            "missing_operations": result["missing_operations"],
            "gaps": result["gaps"],
            "complete_live_coverage": False,
        }


if __name__ == "__main__":
    Application.main()
