"""Separate branch coverage thresholds and coverage report integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.branch_coverage import BranchCoverage
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonValue


class TestBranchCoverage:
    """Never allow strong statement coverage to mask weak branch coverage."""

    @pytest.mark.parametrize(
        "totals",
        [
            {},
            {"num_branches": 0, "covered_branches": 0},
            {"num_branches": True, "covered_branches": 1},
            {"num_branches": 100, "covered_branches": 101},
            {"num_branches": 100, "covered_branches": 89},
        ],
    )
    def test_rejects_invalid_or_insufficient_coverage(
        self, totals: dict[str, JsonValue]
    ) -> None:
        """Missing branch measurements and low coverage fail independently."""
        with pytest.raises(AppError, match="branch"):
            BranchCoverage.evaluate(totals)

    def test_threshold_and_report(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The exact threshold passes and report integration prints only metrics."""
        assert (
            BranchCoverage.evaluate({"num_branches": 100, "covered_branches": 90}) == 90
        )

        def write_report(*, outfile: str) -> None:
            """Simulate the external coverage library's JSON report boundary."""
            Path(outfile).write_text(
                '{"totals":{"num_branches":100,"covered_branches":95}}',
                encoding="utf-8",
            )

        coverage = Mock()
        coverage.json_report.side_effect = write_report
        monkeypatch.setattr(
            "ynab_api_cli.branch_coverage.Coverage", Mock(return_value=coverage)
        )
        BranchCoverage.main()
        assert json.loads(capsys.readouterr().out)["authored_branch_coverage"] == 95
