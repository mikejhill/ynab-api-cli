"""Enforce authored branch coverage independently of statement coverage."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from coverage import Coverage

from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.types import JsonCodec, JsonValue


class BranchCoverage:
    """Reject missing branch data and branch coverage below the delivery threshold."""

    MINIMUM = 90

    @classmethod
    def evaluate(cls, totals: dict[str, JsonValue]) -> float:
        """Check branch counters independently of the combined coverage percentage."""
        total = totals.get("num_branches")
        covered = totals.get("covered_branches")
        if (
            type(total) is not int
            or type(covered) is not int
            or total <= 0
            or not 0 <= covered <= total
        ):
            raise AppError("Missing or invalid authored branch-coverage data.")
        percent = 100 * covered / total
        if percent < cls.MINIMUM:
            raise AppError(
                f"Authored branch coverage {percent:.2f}% is below {cls.MINIMUM}%."
            )
        return percent

    @classmethod
    def main(cls) -> None:
        """Read the preceding pytest coverage data and report the separate gate."""
        coverage = Coverage()
        coverage.load()
        with tempfile.TemporaryDirectory(prefix="ynab-branch-coverage-") as temporary:
            output = Path(temporary) / "coverage.json"
            coverage.json_report(outfile=str(output))
            data = Contract.object(JsonCodec.loads(output.read_text(encoding="utf-8")))
        percent = cls.evaluate(Contract.object(data["totals"]))
        sys.stdout.write(
            json.dumps(
                {"authored_branch_coverage": round(percent, 2), "minimum": cls.MINIMUM}
            )
            + "\n"
        )


if __name__ == "__main__":
    BranchCoverage.main()
