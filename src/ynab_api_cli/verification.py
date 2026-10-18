"""Reviewed feature manifests and public upstream candidate verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from ynab_api_cli.compat import Compatibility
from ynab_api_cli.contract import Contract
from ynab_api_cli.contract_testing import SchemaCases
from ynab_api_cli.development import Development


class Verification:
    """Keep acceptance manifests reviewed and detect all structural changes."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else Path(__file__).resolve().parents[2]

    @classmethod
    def main(cls) -> None:
        """Execute the public poe verification tasks."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "command",
            choices=["manifest-init", "contract-check", "compat-check", "skill-check"],
        )
        command = str(parser.parse_args().command)
        instance = cls()
        if command == "manifest-init":
            with (
                instance.root / "src/ynab_api_cli/resources/schema_features.json"
            ).open("x", encoding="utf-8") as stream:
                json.dump(instance.manifest(), stream, indent=2)
                stream.write("\n")
        elif command == "contract-check":
            instance.contract_check()
        elif command == "skill-check":
            instance.skill_check()
        else:
            instance.compat_check()

    @staticmethod
    def manifest() -> dict[str, str]:
        """Fingerprint every declared schema node, enum variant, and null branch."""
        return {
            probe.identifier: hashlib.sha256(
                json.dumps(
                    Compatibility.structural(probe.schema), sort_keys=True
                ).encode("utf-8")
            ).hexdigest()
            for probe in SchemaCases(Contract()).probes()
        }

    def contract_check(self) -> None:
        """Require review when any existing or additional schema feature changes."""
        resource = self.root / "src/ynab_api_cli/resources"
        reviewed = json.loads(
            (resource / "schema_features.json").read_text(encoding="utf-8")
        )
        if reviewed != self.manifest():
            raise SystemExit(
                "Schema feature manifest differs; review all changed cases."
            )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_contract.py",
                "tests/test_typing.py",
                "tests/test_features.py",
                "-q",
            ],
            cwd=self.root,
            check=True,
        )

    def skill_check(self) -> None:
        """Ensure canonical and installed skill files match exactly."""
        canonical = self.root / "skills/ynab-api-cli"
        bundled = self.root / "src/ynab_api_cli/resources/skill"
        left = {
            str(path.relative_to(canonical)): path.read_bytes()
            for path in canonical.rglob("*")
            if path.is_file()
        }
        right = {
            str(path.relative_to(bundled)): path.read_bytes()
            for path in bundled.rglob("*")
            if path.is_file()
        }
        if not left or left != right:
            raise SystemExit("Canonical and bundled skill resources differ.")

    def compat_check(self) -> None:
        """Generate, type-check, and test a candidate without editing the checkout."""
        checker = Compatibility()
        latest = checker.fetch()
        report = checker.compare(latest)
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            shutil.copytree(
                self.root,
                candidate,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".venv",
                    ".ruff_cache",
                    ".pytest_cache",
                    "__pycache__",
                    "dist",
                    ".hypothesis",
                    ".coverage",
                ),
            )
            spec_path = candidate / "src/ynab_api_cli/resources/openapi.yaml"
            spec_path.write_text(
                yaml.safe_dump(latest, sort_keys=False), encoding="utf-8"
            )
            Development(candidate).generate(check=False)
            subprocess.run(  # noqa: S603 - fixed checker module; no shell.
                [
                    sys.executable,
                    "-m",
                    "ty",
                    "check",
                    str(candidate),
                    "--python",
                    sys.executable,
                ],
                cwd=candidate,
                check=True,
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(candidate / "src")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_contract.py",
                    "tests/test_compat.py",
                    "tests/test_typing.py",
                    "tests/test_features.py",
                    "-q",
                ],
                cwd=candidate,
                env=environment,
                check=True,
            )
        if report["compatible"] is not True:
            raise SystemExit(1)


if __name__ == "__main__":
    Verification.main()
