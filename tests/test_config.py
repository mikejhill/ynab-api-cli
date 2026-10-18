"""Connection file preservation, XDG resolution, and credential protection."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from ynab_api_cli.config import ConfigStore
from ynab_api_cli.exceptions import AppError
from ynab_api_cli.security import FileSecurity


class TestConfig:
    """Operate only in temporary directories with synthetic credentials."""

    def test_xdg_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """XDG overrides the home fallback and rejects relative paths."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert ConfigStore().root == tmp_path / "ynab-api-cli"
        monkeypatch.setenv("XDG_CONFIG_HOME", "relative")
        with pytest.raises(AppError, match="absolute"):
            ConfigStore()
        monkeypatch.delenv("XDG_CONFIG_HOME")
        assert ConfigStore().root == Path.home() / ".config/ynab-api-cli"
        monkeypatch.setenv("XDG_CONFIG_HOME", "")
        assert ConfigStore().root == Path.home() / ".config/ynab-api-cli"

    def test_preservation_and_rotation(self, store: ConfigStore) -> None:
        """Replacement is explicit and preserves unrelated configuration fields."""
        store.write(
            store.root / "auth.json",
            {"access_token": "synthetic-test-token", "unrelated": "keep"},
            secret=True,
        )
        with pytest.raises(AppError, match="already exist"):
            store.configure("replacement-test-token")
        assert store.load().token == "synthetic-test-token"  # noqa: S105 - synthetic fixture.
        store.configure("replacement-test-token", replace=True)
        assert store.load().token == "replacement-test-token"  # noqa: S105 - synthetic fixture.
        assert store.read(store.root / "auth.json")["unrelated"] == "keep"
        store.write(store.root / "config.json", {"other": True})
        store.select_plan("00000000-0000-4000-8000-000000000001")
        assert store.read(store.root / "config.json")["other"] is True
        assert store.load().plan_id is not None
        assert "replacement-test-token" not in repr(store.load())

    @pytest.mark.parametrize(
        "token", ["", " ", "two tokens", "line\nline", "bad-é", "bad\x00"]
    )
    def test_invalid_tokens(self, tmp_path: Path, token: str) -> None:
        """Blank and multiline token input never creates credentials."""
        with pytest.raises(AppError):
            ConfigStore(tmp_path).configure(token)
        assert not (tmp_path / "auth.json").exists()

    def test_invalid_files(self, store: ConfigStore) -> None:
        """Corrupt JSON, missing tokens, and invalid plan settings are rejected."""
        with pytest.raises(AppError, match="Missing"):
            ConfigStore(store.root / "absent").load()
        path = store.root / "config.json"
        for content in ("broken", "[]", '{"plan_id": 1}', '{"plan_id":""}'):
            path.write_text(content, encoding="utf-8")
            with pytest.raises(AppError):
                store.load()
        path.unlink()
        store.write(
            store.root / "auth.json", {"wrong": "synthetic-test-token"}, secret=True
        )
        with pytest.raises(AppError, match="access_token"):
            store.load()
        with pytest.raises(AppError, match="explicit plan UUID"):
            store.select_plan("last-used")

    def test_atomic_failure_preserves_file(
        self, store: ConfigStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failed replacement preserves credentials and removes temporary files."""
        monkeypatch.setattr(Path, "replace", Mock(side_effect=OSError("synthetic")))
        with pytest.raises(AppError, match="atomically"):
            store.configure("replacement-test-token", replace=True)
        assert store.load().token == "synthetic-test-token"  # noqa: S105 - synthetic fixture.
        assert not list(store.root.glob(".ynab-api-cli-*"))

    def test_concurrent_creation_cannot_overwrite(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A competing credential file appearing during setup remains untouched."""
        store = ConfigStore(tmp_path)
        target = tmp_path / "auth.json"

        def competing_writer(_path: Path) -> None:
            """Simulate another process creating credentials before atomic commit."""
            target.write_text('{"access_token":"synthetic-existing"}', encoding="utf-8")

        monkeypatch.setattr(store.security, "protect", competing_writer)
        with pytest.raises(AppError, match="atomically"):
            store.configure("synthetic-new")
        assert store.read(target)["access_token"] == "synthetic-existing"  # noqa: S105 - synthetic fixture.
        assert not list(tmp_path.glob(".ynab-api-cli-*"))


class TestFileSecurity:
    """Verify POSIX behavior and the encoded Windows ACL boundary."""

    def test_posix(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """POSIX rejects shared permission bits and applies mode 600."""
        path = tmp_path / "auth.json"
        path.write_text("synthetic", encoding="utf-8")
        chmod = Mock()
        monkeypatch.setattr(Path, "chmod", chmod)
        security = FileSecurity("posix")
        security.protect(path)
        chmod.assert_called_once_with(0o600)
        monkeypatch.setattr(
            Path,
            "stat",
            Mock(return_value=os.stat_result((0o600, 0, 0, 1, 0, 0, 0, 0, 0, 0))),
        )
        security.validate(path)
        monkeypatch.setattr(
            Path,
            "stat",
            Mock(return_value=os.stat_result((0o644, 0, 0, 1, 0, 0, 0, 0, 0, 0))),
        )
        with pytest.raises(AppError, match="mode 600"):
            security.validate(path)

    def test_windows_acl(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Windows protection targets the current SID and quotes file paths."""
        powershell = Mock(return_value="private")
        monkeypatch.setattr(FileSecurity, "powershell", powershell)
        security = FileSecurity("nt")
        security.protect(tmp_path / "quote'file")
        assert "SetAccessRuleProtection($true,$false)" in powershell.call_args.args[0]
        assert "quote''file" in powershell.call_args.args[0]
        security.validate(tmp_path / "auth.json")
        powershell.return_value = "shared"
        with pytest.raises(AppError, match="not private"):
            security.validate(tmp_path / "auth.json")

    def test_powershell_boundary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """PowerShell uses encoded commands and reports boundary failures safely."""
        completed = Mock(stdout="private\n")
        run = Mock(return_value=completed)
        monkeypatch.setattr("ynab_api_cli.security.subprocess.run", run)
        assert FileSecurity("nt").powershell("fixed script") == "private"
        assert "-EncodedCommand" in run.call_args.args[0]
        run.side_effect = OSError("synthetic")
        with pytest.raises(AppError, match="Windows credential ACLs"):
            FileSecurity("nt").powershell("fixed script")
