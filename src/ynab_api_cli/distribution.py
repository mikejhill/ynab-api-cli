"""Build archive checks and isolated installation smoke verification."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.contract import Contract
from ynab_api_cli.exceptions import AppError


class DistributionCheck:
    """Verify wheels, source archives, and a clean uv tool installation."""

    @classmethod
    def main(cls) -> None:
        """Run the release check from the project root."""
        cls().run(Path(__file__).resolve().parents[2])

    def run(self, root: Path) -> None:
        """Inspect built artifacts and exercise the independently installed CLI."""
        wheel = next((root / "dist").glob("*.whl"))
        source = next((root / "dist").glob("*.tar.gz"))
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            required = {
                "ynab_api_cli/resources/openapi.yaml",
                "ynab_api_cli/resources/catalog.json",
                "ynab_api_cli/resources/skill/SKILL.md",
                "ynab_api_cli/py.typed",
            }
            if not required <= set(names):
                raise AppError("Wheel is missing required contract or skill resources.")
        with tarfile.open(source) as archive:
            if not any(
                name.endswith("/skills/ynab-api-cli/SKILL.md")
                for name in archive.getnames()
            ):
                raise AppError("Source archive is missing the supplementary skill.")
        uv = shutil.which("uv")
        if uv is None:
            raise AppError("uv is required for clean installation verification.")
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            environment = dict(os.environ)
            environment.update(
                {
                    "UV_TOOL_DIR": str(workspace / "tools"),
                    "UV_TOOL_BIN_DIR": str(workspace / "bin"),
                    "XDG_CONFIG_HOME": str(workspace / "config"),
                }
            )
            subprocess.run(  # noqa: S603 - resolved uv and local wheel, no shell.
                [
                    uv,
                    "tool",
                    "install",
                    "--python",
                    sys.executable,
                    "--no-managed-python",
                    str(wheel),
                ],
                env=environment,
                cwd=workspace,
                check=True,
            )
            executable = (
                workspace
                / "bin"
                / ("ynab-api-cli.exe" if os.name == "nt" else "ynab-api-cli")
            )
            store = ConfigStore(workspace / "config/ynab-api-cli")
            store.configure("synthetic-install-test")
            for argv in (
                ["--help"],
                ["discover"],
                ["inspect", "getUser"],
                ["doctor", "--offline"],
                ["skill", "export", str(workspace / "exported-skill")],
            ):
                result = subprocess.run(  # noqa: S603 - fixed installed CLI smoke commands.
                    [str(executable), *argv],
                    env=environment,
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if argv[0] == "discover" and len(
                    json.loads(result.stdout)["operations"]
                ) != len(Contract().catalog):
                    raise AppError("Installed CLI operation inventory mismatch.")
        release = root / "dist" / (wheel.name.split("-py3-")[0] + "-release.zip")
        with zipfile.ZipFile(release, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for artifact in (wheel, source, root / "README.md"):
                archive.write(artifact, artifact.name)
            for directory in ("skills", "docs"):
                for path in (root / directory).rglob("*"):
                    if path.is_file():
                        archive.write(path, str(path.relative_to(root)))
        sys.stdout.write(
            json.dumps(
                {
                    "wheel": wheel.name,
                    "source": source.name,
                    "release": release.name,
                    "clean_install": "passed",
                }
            )
            + "\n"
        )


if __name__ == "__main__":
    DistributionCheck.main()
