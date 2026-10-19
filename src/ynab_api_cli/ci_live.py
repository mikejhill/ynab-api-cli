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

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.e2e import E2eOptions, E2eRunner
from ynab_api_cli.types import JsonCodec, JsonValue

logger = logging.getLogger(__name__)


class Application:
    """Consume CI secrets once and expose only operation-level test results."""

    @classmethod
    def main(cls) -> None:
        """Run the probe without emitting exception details or API payloads."""
        logging.basicConfig(level=logging.WARNING)
        try:
            report = cls.run(os.environ)
        except KeyboardInterrupt:
            raise SystemExit(130) from None
        except Exception:  # noqa: BLE001 - redact unexpected failures at the process boundary.
            logger.error(  # noqa: TRY400 - tracebacks may expose credentials.
                "Live CI probe failed; no response or credential details logged."
            )
            raise SystemExit(1) from None
        sys.stdout.write(json.dumps(report, indent=2) + "\n")

    @staticmethod
    def run(environment: MutableMapping[str, str]) -> dict[str, JsonValue]:
        """Run required seeded acceptance using only explicit environment secrets."""
        token = environment.pop("YNAB_ACCESS_TOKEN", "")
        pool = environment.pop("YNAB_ACCESS_TOKENS", "")
        plan = environment.pop("YNAB_TEST_PLAN_ID", "")
        if token and pool:
            raise ValueError("Configure one credential secret format, not both.")
        values: dict[str, JsonValue] = (
            {"access_tokens": JsonCodec.loads(pool)}
            if pool
            else {"access_token": token}
        )
        connection = ConfigStore.credentials(values, str(UUID(plan)))
        if environment.get("GITHUB_ACTIONS") == "true":
            for credential in connection.tokens:
                sys.stdout.write("::add-mask::" + credential.replace("%", "%25") + "\n")
            sys.stdout.flush()
        with tempfile.TemporaryDirectory(prefix="ynab-api-cli-live-") as temporary:
            options = E2eOptions(
                "reads", connection.plan_id or "", Path(temporary) / "state"
            )
            return E2eRunner(options, connection).run()


if __name__ == "__main__":
    Application.main()
