"""Protect credentials with private POSIX permissions or Windows ACLs."""

from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path

from ynab_api_cli.exceptions import AppError


class FileSecurity:
    """Apply and inspect credential protection without revealing file contents."""

    def __init__(self, platform: str = os.name) -> None:
        self.platform = platform

    def powershell(self, script: str) -> str:
        """Execute a fixed ACL script with no profile or interactive window."""
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        try:
            result = subprocess.run(  # noqa: S603 - encoded fixed ACL script; no shell.
                [
                    str(
                        Path(os.environ.get("SYSTEMROOT", "C:/Windows"))
                        / "System32/WindowsPowerShell/v1.0/powershell.exe"
                    ),
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    encoded,
                ],
                capture_output=True,
                text=True,
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.CalledProcessError) as err:
            raise AppError(
                "Cannot inspect or protect Windows credential ACLs."
            ) from err
        return result.stdout.strip()

    def protect(self, path: Path) -> None:
        """Replace permissions on a newly created credential file."""
        if self.platform != "nt":
            path.chmod(0o600)
            return
        literal = str(path).replace("'", "''")
        self.powershell(
            "$ErrorActionPreference='Stop'; "
            "$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User; "
            "$acl=New-Object System.Security.AccessControl.FileSecurity; "
            "$acl.SetOwner($sid); $acl.SetAccessRuleProtection($true,$false); "
            "$rule=New-Object System.Security.AccessControl.FileSystemAccessRule"
            "($sid,'FullControl','Allow'); "
            "$acl.AddAccessRule($rule); "
            f"[System.IO.File]::SetAccessControl('{literal}', $acl)"
        )

    def validate(self, path: Path) -> None:
        """Refuse credential files readable by other principals."""
        if self.platform != "nt":
            if path.stat().st_mode & 0o077:
                raise AppError("Credential file must have mode 600.")
            return
        literal = str(path).replace("'", "''")
        result = self.powershell(
            "$ErrorActionPreference='Stop'; "
            "$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent()"
            ".User.Value; "
            f"$acl=[System.IO.File]::GetAccessControl('{literal}'); "
            "$bad=@($acl.Access | Where-Object { "
            "$_.AccessControlType -eq 'Allow' -and $_.IdentityReference.Translate"
            "([System.Security.Principal.SecurityIdentifier]).Value -ne $sid }); "
            "if ($bad.Count -eq 0 -and $acl.AreAccessRulesProtected) "
            "{ 'private' } else { 'shared' }"
        )
        if result != "private":
            raise AppError(
                "Credential ACL is not private; rerun configure --replace locally."
            )
