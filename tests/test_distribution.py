"""Package resource checks and isolated-install command construction."""

from __future__ import annotations

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.distribution import DistributionCheck
from ynab_api_cli.exceptions import AppError


class TestDistribution:
    """Verify release checks independently of a real global tool installation."""

    def artifacts(self, root: Path, *, complete: bool = True) -> None:
        """Create synthetic wheel and source archives with expected resources."""
        (root / "dist").mkdir()
        (root / "skills/ynab-api-cli").mkdir(parents=True)
        (root / "skills/ynab-api-cli/SKILL.md").write_text(
            "synthetic skill", encoding="utf-8"
        )
        (root / "README.md").write_text("synthetic", encoding="utf-8")
        with zipfile.ZipFile(
            root / "dist/ynab_api_cli-0.1.0-py3-none-any.whl", "w"
        ) as archive:
            for name in ("openapi.yaml", "catalog.json", "skill/SKILL.md"):
                archive.writestr("ynab_api_cli/resources/" + name, "synthetic")
            if complete:
                archive.writestr("ynab_api_cli/py.typed", "")
        with tarfile.open(root / "dist/ynab_api_cli-0.1.0.tar.gz", "w:gz") as archive:
            archive.add(root / "skills", arcname="ynab_api_cli-0.1.0/skills")

    def test_isolated_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clean-install verification uses temporary tool and config directories."""
        self.artifacts(tmp_path)
        run = Mock(
            return_value=subprocess.CompletedProcess(
                [], 0, '{"operations":' + str(list(range(44))) + "}", ""
            )
        )
        monkeypatch.setattr("ynab_api_cli.distribution.subprocess.run", run)
        monkeypatch.setattr("ynab_api_cli.distribution.ConfigStore.configure", Mock())
        monkeypatch.setattr(
            "ynab_api_cli.distribution.shutil.which",
            Mock(return_value=str(tmp_path / "uv.exe")),
        )
        DistributionCheck().run(tmp_path)
        assert run.call_count == 6
        install_environment = run.call_args_list[0].kwargs["env"]
        assert install_environment["UV_TOOL_DIR"] != str(
            Path.home() / ".local/share/uv/tools"
        )
        assert list((tmp_path / "dist").glob("*-release.zip"))

    def test_missing_resources(self, tmp_path: Path) -> None:
        """A wheel missing the typing marker cannot pass distribution checks."""
        self.artifacts(tmp_path, complete=False)
        with pytest.raises(AppError, match="missing required"):
            DistributionCheck().run(tmp_path)

    def test_uv_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The installation check reports a missing uv executable clearly."""
        self.artifacts(tmp_path)
        monkeypatch.setattr(shutil, "which", Mock(return_value=None))
        with pytest.raises(AppError, match="uv is required"):
            DistributionCheck().run(tmp_path)
