"""CI credential consumption, seeded acceptance, and failure redaction."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.ci_live import Application
from ynab_api_cli.e2e import E2eRunner
from ynab_api_cli.exceptions import AppError


class TestApplication:
    """Keep CI secrets out of reports, tracebacks, and persistent files."""

    PLAN = "00000000-0000-0000-0000-000000000123"

    @pytest.mark.parametrize("pool", [False, True])
    def test_explicit_credentials_and_cleanup(
        self, *, pool: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both credential formats select required reads without enabling writes."""
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        environment = {"YNAB_TEST_PLAN_ID": self.PLAN}
        environment["YNAB_ACCESS_TOKENS" if pool else "YNAB_ACCESS_TOKEN"] = (
            json.dumps(["first-fake", "second-fake"]) if pool else "first-fake"
        )
        run = Mock(return_value={"ok": True, "mode": "reads"})
        monkeypatch.setattr(E2eRunner, "run", run)
        assert Application.run(environment) == {"ok": True, "mode": "reads"}
        assert environment == {}
        assert not list(tmp_path.iterdir())

    @pytest.mark.parametrize(
        "values",
        [
            {},
            {"YNAB_ACCESS_TOKEN": "bad value"},
            {"YNAB_ACCESS_TOKENS": "[]"},
            {
                "YNAB_ACCESS_TOKEN": "first-fake",
                "YNAB_ACCESS_TOKENS": '["second-fake"]',
            },
            {"YNAB_ACCESS_TOKENS": "malformed"},
        ],
    )
    def test_invalid_settings_no_network(
        self, values: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid and ambiguous credentials fail before creating an E2E runner."""
        values["YNAB_TEST_PLAN_ID"] = self.PLAN
        run = Mock()
        monkeypatch.setattr(E2eRunner, "run", run)
        with pytest.raises((AppError, ValueError)):
            Application.run(values)
        run.assert_not_called()
        assert values == {}

    @pytest.mark.parametrize(
        "error",
        [AppError("secret-body"), ValueError("secret-body"), KeyboardInterrupt()],
    )
    def test_top_boundary_redaction(
        self,
        error: BaseException,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unexpected failures never emit credential-bearing traceback chains."""
        monkeypatch.setattr(Application, "run", Mock(side_effect=error))
        with pytest.raises(SystemExit) as caught:
            Application.main()
        assert caught.value.code == (130 if isinstance(error, KeyboardInterrupt) else 1)
        output = capsys.readouterr()
        assert "secret-body" not in output.out + output.err + caplog.text

    def test_success_summary(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Successful CI emits the sanitized acceptance report."""
        monkeypatch.setattr(Application, "run", Mock(return_value={"ok": True}))
        Application.main()
        assert json.loads(capsys.readouterr().out) == {"ok": True}

    def test_individual_github_masks(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Register each JSON-array credential with the runner's masking protocol."""
        monkeypatch.setattr(E2eRunner, "run", Mock(return_value={"ok": True}))
        Application.run(
            {
                "GITHUB_ACTIONS": "true",
                "YNAB_TEST_PLAN_ID": self.PLAN,
                "YNAB_ACCESS_TOKENS": '["first-fake", "second%fake"]',
            }
        )
        assert (
            capsys.readouterr().out
            == "::add-mask::first-fake\n::add-mask::second%25fake\n"
        )
