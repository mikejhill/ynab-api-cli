"""Compile positive and deliberately invalid endpoint calls under strict ty."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestTyping:
    """Generated public signatures must expose errors to a static checker."""

    def test_typed_calls(self, tmp_path: Path) -> None:
        """Valid calls pass; wrong types and omitted arguments produce diagnostics."""
        project = Path(__file__).resolve().parents[1]
        header = """from __future__ import annotations
from ynab_api_cli.generated.api.accounts.get_account_by_id import Endpoint
from ynab_api_cli.generated.models.user import User
from ynab_api_cli.transport import Connection, Transport
from uuid import UUID
"""
        valid = tmp_path / "positive.py"
        valid.write_text(
            header + 'Endpoint.execute(transport=Transport(Connection("synthetic")), '
            'plan_id="fixture", '
            'account_id=UUID("00000000-0000-4000-8000-000000000001"))\n'
            'User(id=UUID("00000000-0000-4000-8000-000000000001"))\n',
            encoding="utf-8",
        )
        invalid = tmp_path / "negative.py"
        invalid.write_text(
            header + 'Endpoint.execute(transport=Transport(Connection("synthetic")), '
            'plan_id=3, account_id="wrong-type")\n'
            'Endpoint.execute(transport=Transport(Connection("synthetic")))\n'
            "User(id=123)\n",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            "-m",
            "ty",
            "check",
            "--project",
            str(project),
            "--python",
            sys.executable,
        ]
        positive = subprocess.run(  # noqa: S603 - fixed checker and synthetic files.
            [*command, str(valid)], capture_output=True, text=True, check=False
        )
        assert positive.returncode == 0, positive.stdout + positive.stderr
        negative = subprocess.run(  # noqa: S603 - fixed checker and synthetic files.
            [*command, str(invalid)], capture_output=True, text=True, check=False
        )
        diagnostics = negative.stdout + negative.stderr
        assert negative.returncode != 0
        assert "invalid-argument-type" in diagnostics
        assert "missing-argument" in diagnostics
