"""Deterministic code generation and release verification commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import yaml


class Development:
    """Run the pinned generator with reviewed templates and transformations."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else Path(__file__).resolve().parents[2]

    @classmethod
    def main(cls) -> None:
        """Dispatch development tasks through the project entry point."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "command", choices=["generate", "codegen-check", "initialize"]
        )
        args = parser.parse_args()
        if args.command == "initialize":
            cls().initialize()
            return
        cls().generate(check=args.command == "codegen-check")

    def initialize(self) -> None:
        """Record the initial reviewed baseline exactly once."""
        resource = self.root / "src/ynab_api_cli/resources"
        path = resource / "openapi.yaml"
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        catalog = {
            op["operationId"]: {"method": verb.upper(), "path": route}
            for route, item in spec["paths"].items()
            for verb, op in item.items()
            if verb in {"get", "post", "put", "patch", "delete"}
        }
        provenance = {
            "source_url": "https://api.ynab.com/papi/open_api_spec.yaml",
            "retrieved_at": datetime.now(UTC).isoformat(),
            "spec_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "api_version": spec["info"]["version"],
            "generator": "openapi-python-client",
            "generator_version": version("openapi-python-client"),
            "operation_count": len(catalog),
        }
        for name, value in (("catalog.json", catalog), ("provenance.json", provenance)):
            with (resource / name).open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(value, indent=2) + "\n")

    def generate(self, *, check: bool) -> None:
        """Generate into a temporary directory and compare or install source."""
        root = self.root
        config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
            "tool"
        ]["ynab_api_cli"]["codegen"]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            config_path = workspace / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = workspace / "generated"
            result = subprocess.run(  # noqa: S603 - fixed installed module and local paths, no shell.
                [
                    sys.executable,
                    "-m",
                    "openapi_python_client",
                    "generate",
                    "--path",
                    str(root / "src/ynab_api_cli/resources/openapi.yaml"),
                    "--meta",
                    "none",
                    "--config",
                    str(config_path),
                    "--custom-template-path",
                    str(root / "templates"),
                    "--output-path",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if (
                result.returncode
                or "warning" in (result.stdout + result.stderr).lower()
            ):
                sys.stderr.write(result.stdout + result.stderr)
                raise SystemExit(1)
            for name in ("client.py", "types.py", "errors.py"):
                (output / name).unlink()
            for path in output.rglob("*.py"):
                self.transform(path, output)
            self.bindings(output)
            subprocess.run(  # noqa: S603 - fixed installed ruff module, no shell.
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "format",
                    str(output),
                    "--config",
                    str(root / "pyproject.toml"),
                ],
                check=True,
            )
            subprocess.run(  # noqa: S603 - fixed installed ruff module, no shell.
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    str(output),
                    "--fix",
                    "--config",
                    str(root / "pyproject.toml"),
                ],
                check=True,
            )
            subprocess.run(  # noqa: S603 - fixed installed ruff module, no shell.
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "format",
                    str(output),
                    "--config",
                    str(root / "pyproject.toml"),
                ],
                check=True,
            )
            destination = (root / "src/ynab_api_cli/generated").resolve()
            if not destination.is_relative_to((root / "src/ynab_api_cli").resolve()):
                raise SystemExit("Generated destination escapes the project.")
            if check:
                if self.fingerprints(output) != self.fingerprints(destination):
                    raise SystemExit(
                        "Generated source differs; run poe generate and review."
                    )
            else:
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(
                    output, destination, ignore=shutil.ignore_patterns(".ruff_cache")
                )

    @staticmethod
    def transform(path: Path, root: Path) -> None:
        """Use absolute package imports and complete generated file headers."""
        text = path.read_text(encoding="utf-8")
        if path.name == "__init__.py":
            if path.parent == root:
                text = '"""Generated REST client declarations."""\n'
            elif path.parent.name != "models":
                text = '"""Generated endpoint declarations."""\n'
            else:
                text = text.replace(
                    '""" Contains all the data models used in inputs/outputs """',
                    '"""Generated request and response models."""',
                )
        package = ["ynab_api_cli", "generated", *path.relative_to(root).parts[:-1]]
        for match in list(re.finditer(r"from (\.+)([\w.]*) import", text)):
            prefix = ".".join(package[: len(package) - len(match[1]) + 1])
            suffix = "." + match[2] if match[2] else ""
            text = text.replace(match[0], f"from {prefix}{suffix} import")
        text = re.sub(r"from ynab_api_cli.generated.types import .*\n", "", text)
        text = text.replace("from enum import Enum", "from enum import StrEnum")
        text = re.sub(
            r"class (\w+)\(str, Enum\):",
            r'class \1(StrEnum):\n    """Generated contract enumeration."""',
            text,
        )
        text = re.sub(
            r"    def __str__\(self\) -> str:\n        return str\(self.value\)\n",
            "",
            text,
        )
        if not text.startswith('"""'):
            text = (
                '"""Generated declarations; regenerate rather than editing."""\n' + text
            )
        if "from __future__ import annotations" not in text:
            closing = text.index('"""', 3) + 3
            text = (
                text[:closing]
                + "\nfrom __future__ import annotations\n"
                + text[closing:]
            )
        if path.name == "__init__.py" and path.parent.name == "models":
            text += '''
from pydantic import BaseModel

class ModelRegistry:
    """Resolve forward references after all models have loaded."""
    @classmethod
    def rebuild(cls) -> None:
        """Resolve generated models against the complete namespace."""
        namespace = globals()
        for value in tuple(namespace.values()):
            if (
                isinstance(value, type) and value is not BaseModel
                and issubclass(value, BaseModel)
            ):
                value.model_rebuild(_types_namespace=namespace)

ModelRegistry.rebuild()
'''
        path.write_text(text, encoding="utf-8")

    @staticmethod
    def fingerprints(root: Path) -> dict[str, str]:
        """Hash generated Python files independently of cache artifacts."""
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*.py")
        }

    @staticmethod
    def bindings(root: Path) -> None:
        """Generate static class bindings without reflective endpoint invocation."""
        imports: list[str] = []
        entries: list[str] = []
        for index, path in enumerate(sorted((root / "api").glob("*/*.py"))):
            if path.name == "__init__.py":
                continue
            module = ".".join(path.parent.relative_to(root).parts)
            alias = f"operation{index}"
            imports.append(
                f"from ynab_api_cli.generated.{module} import {path.stem} as {alias}"
            )
            entries.append(f'        "{path.stem}": {alias}.Endpoint.dispatch,')
        text = "\n".join(
            [
                '"""Generated static endpoint dispatch; regenerate to change."""',
                "from __future__ import annotations",
                "from collections.abc import Callable, Mapping",
                "from types import MappingProxyType",
                "from typing import ClassVar",
                "from ynab_api_cli.transport import Transport",
                "from ynab_api_cli.types import RequestValues, Response",
                *imports,
                "",
                "class Bindings:",
                '    """Statically reference every generated typed operation."""',
                "    operations: ClassVar[Mapping[str,",
                "        Callable[[Transport, RequestValues], Response[object]]",
                "    ]] = MappingProxyType({",
                *entries,
                "    })",
                "",
            ]
        )
        (root / "bindings.py").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    Development.main()
