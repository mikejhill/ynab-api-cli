"""Generator determinism, candidate isolation, and reviewed release gates."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.contract import Contract
from ynab_api_cli.development import Development
from ynab_api_cli.verification import Verification


class TestDevelopment:
    """Verify reproducible generation rather than editing generated source."""

    def test_real_generation(self, tmp_path: Path) -> None:
        """Pinned generation reproduces checked-in code and catches changed output."""
        project = Path(__file__).resolve().parents[1]
        for name in ("pyproject.toml", "templates"):
            if (project / name).is_dir():
                shutil.copytree(project / name, tmp_path / name)
            else:
                shutil.copy2(project / name, tmp_path / name)
        shutil.copytree(
            project / "src/ynab_api_cli/resources",
            tmp_path / "src/ynab_api_cli/resources",
        )
        development = Development(tmp_path)
        development.generate(check=False)
        assert development.fingerprints(
            tmp_path / "src/ynab_api_cli/generated"
        ) == development.fingerprints(project / "src/ynab_api_cli/generated")
        development.generate(check=True)
        (tmp_path / "src/ynab_api_cli/generated/changed.py").write_text(
            "synthetic", encoding="utf-8"
        )
        with pytest.raises(SystemExit, match="differs"):
            development.generate(check=True)

    def test_generator_warning_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Warnings cannot silently discard unsupported contract components."""
        project = Path(__file__).resolve().parents[1]
        shutil.copy2(project / "pyproject.toml", tmp_path / "pyproject.toml")
        monkeypatch.setattr(
            "ynab_api_cli.development.subprocess.run",
            Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, "WARNING unsupported", ""
                )
            ),
        )
        with pytest.raises(SystemExit) as captured:
            Development(tmp_path).generate(check=False)
        assert captured.value.code == 1

    def test_baseline_provenance(self, tmp_path: Path) -> None:
        """Initial provenance records the actual generator and specification hash."""
        project = Path(__file__).resolve().parents[1]
        directory = tmp_path / "src/ynab_api_cli/resources"
        directory.mkdir(parents=True)
        shutil.copy2(
            project / "src/ynab_api_cli/resources/openapi.yaml",
            directory / "openapi.yaml",
        )
        Development(tmp_path).initialize()
        record = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
        assert record["operation_count"] == 44
        assert record["generator_version"] == "0.29.0"
        assert record["spec_sha256"]

    @pytest.mark.parametrize("command", ["generate", "codegen-check", "initialize"])
    def test_entrypoint(self, monkeypatch: pytest.MonkeyPatch, command: str) -> None:
        """Poe's generator entry point dispatches the selected action."""
        monkeypatch.setattr("sys.argv", ["development", command])
        generate = Mock()
        initialize = Mock()
        monkeypatch.setattr(Development, "generate", generate)
        monkeypatch.setattr(Development, "initialize", initialize)
        Development.main()
        assert initialize.called == (command == "initialize")
        assert generate.called == (command != "initialize")


class TestVerification:
    """Release checks must fail drift while preserving the original checkout."""

    def test_manifest_and_skill_checks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A matching manifest passes; changed manifests and skill copies fail."""
        project = Path(__file__).resolve().parents[1]
        shutil.copytree(
            project / "src/ynab_api_cli/resources",
            tmp_path / "src/ynab_api_cli/resources",
        )
        shutil.copytree(project / "skills", tmp_path / "skills")
        verification = Verification(tmp_path)
        subprocess_run = Mock(return_value=subprocess.CompletedProcess([], 0))
        monkeypatch.setattr("ynab_api_cli.verification.subprocess.run", subprocess_run)
        verification.contract_check()
        assert subprocess_run.called
        verification.skill_check()
        (tmp_path / "src/ynab_api_cli/resources/schema_features.json").write_text(
            "{}", encoding="utf-8"
        )
        with pytest.raises(SystemExit, match="feature manifest"):
            verification.contract_check()
        (tmp_path / "skills/ynab-api-cli/SKILL.md").write_text(
            "changed", encoding="utf-8"
        )
        with pytest.raises(SystemExit, match="resources differ"):
            verification.skill_check()

    def test_candidate_isolation(
        self, tmp_path: Path, contract: Contract, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Upstream candidates are generated only in temporary directories."""
        project = Path(__file__).resolve().parents[1]
        shutil.copytree(project / "src", tmp_path / "src")
        monkeypatch.setattr(
            "ynab_api_cli.verification.Compatibility.fetch",
            Mock(return_value=contract.document),
        )
        generation = Mock()
        checks = Mock(return_value=subprocess.CompletedProcess([], 0))
        monkeypatch.setattr(
            "ynab_api_cli.verification.Development.generate", generation
        )
        monkeypatch.setattr("ynab_api_cli.verification.subprocess.run", checks)
        before = (tmp_path / "src/ynab_api_cli/resources/openapi.yaml").read_bytes()
        Verification(tmp_path).compat_check()
        assert generation.call_args.kwargs["check"] is False
        assert checks.call_count == 2
        assert (
            tmp_path / "src/ynab_api_cli/resources/openapi.yaml"
        ).read_bytes() == before
        monkeypatch.setattr(
            "ynab_api_cli.verification.Compatibility.compare",
            Mock(return_value={"compatible": False}),
        )
        with pytest.raises(SystemExit) as captured:
            Verification(tmp_path).compat_check()
        assert captured.value.code == 1

    @pytest.mark.parametrize(
        "command", ["manifest-init", "contract-check", "compat-check", "skill-check"]
    )
    def test_entrypoint(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
    ) -> None:
        """Every poe verification action has an exercised CLI entry point."""
        (tmp_path / "src/ynab_api_cli/resources").mkdir(parents=True)
        instance = Verification(tmp_path)
        monkeypatch.setattr("sys.argv", ["verification", command])

        def initialize(subject: Verification) -> None:
            """Bind the verification entry point to the isolated project."""
            subject.root = tmp_path

        monkeypatch.setattr(Verification, "__init__", initialize)
        for name in ("contract_check", "compat_check", "skill_check"):
            monkeypatch.setattr(Verification, name, Mock())
        Verification.main()
        if command == "manifest-init":
            assert (
                tmp_path / "src/ynab_api_cli/resources/schema_features.json"
            ).exists()
        assert instance.root == tmp_path
