"""Safe application failures whose messages never contain credentials."""

from __future__ import annotations


class AppError(Exception):
    """Expected configuration, validation, or HTTP failure."""
